from __future__ import annotations

from app.schemas.correlation import (
    KubernetesNodeLinuxPlan,
    KubernetesNodeSignal,
    LinuxEvidenceRequirement,
)


SUPPORTED_NODE_CONDITIONS = (
    "DiskPressure",
    "MemoryPressure",
    "PIDPressure",
    "NetworkUnavailable",
    "ReadyFalse",
    "NodeNotReady",
)


ALIASES = {
    "disk": "DiskPressure",
    "diskpressure": "DiskPressure",
    "node-disk-pressure": "DiskPressure",
    "memory": "MemoryPressure",
    "memorypressure": "MemoryPressure",
    "node-memory-pressure": "MemoryPressure",
    "pid": "PIDPressure",
    "pidpressure": "PIDPressure",
    "network": "NetworkUnavailable",
    "networkunavailable": "NetworkUnavailable",
    "notready": "NodeNotReady",
    "node-not-ready": "NodeNotReady",
    "readyfalse": "ReadyFalse",
    "ready=false": "ReadyFalse",
}


def _evidence(
    domain: str,
    reason: str,
    commands: list[str],
) -> LinuxEvidenceRequirement:
    return LinuxEvidenceRequirement(
        domain=domain,
        reason=reason,
        commands=commands,
    )


def list_k8s_node_conditions() -> list[str]:
    return sorted(SUPPORTED_NODE_CONDITIONS)


def normalize_node_condition(condition: str) -> str:
    key = condition.strip()
    if key in SUPPORTED_NODE_CONDITIONS:
        return key

    alias_key = key.lower().replace("_", "-").replace(" ", "-")
    compact_key = key.lower().replace("_", "").replace("-", "").replace(" ", "")
    if alias_key in ALIASES:
        return ALIASES[alias_key]
    if compact_key in ALIASES:
        return ALIASES[compact_key]

    supported = ", ".join(list_k8s_node_conditions())
    raise ValueError(
        f"Unsupported Kubernetes node condition '{condition}'. "
        f"Supported: {supported}"
    )


def plan_k8s_node_linux(
    node: str,
    conditions: list[str] | tuple[str, ...] | None = None,
) -> KubernetesNodeLinuxPlan:
    """
    Build a deterministic Linux evidence plan for Kubernetes node symptoms.
    """

    normalized = [
        normalize_node_condition(condition)
        for condition in (conditions or ["NodeNotReady"])
    ]
    normalized = list(dict.fromkeys(normalized))

    signals: list[KubernetesNodeSignal] = []
    evidence: list[LinuxEvidenceRequirement] = []
    kubernetes_checks = [
        f"kubectl describe node {node}",
        "kubectl get events --all-namespaces --sort-by=.lastTimestamp",
        f"kubectl get node {node} -o yaml",
    ]
    next_aop_commands: list[str] = []
    cloud_checks: list[str] = []
    do_not_assume = [
        "Do not SSH and change the node before preserving Kubernetes condition and event evidence.",
        "Do not treat Kubernetes node pressure as root cause until Linux host evidence proves the layer.",
    ]
    memory_notes: list[str] = []

    for condition in normalized:
        if condition == "DiskPressure":
            signals.append(
                KubernetesNodeSignal(
                    condition="DiskPressure",
                    status="True",
                    reason="Node filesystem pressure",
                    summary=(
                        "Kubelet reports disk pressure that can trigger "
                        "evictions or block image/runtime operations."
                    ),
                )
            )
            evidence.extend(
                [
                    _evidence(
                        "linux-host-storage",
                        (
                            "Correlates kubelet path usage, runtime path "
                            "usage, filesystem state, LVM, NFS, multipath, "
                            "and I/O latency in one host view."
                        ),
                        [
                            "aop investigate linux host --path /var/lib/kubelet --service kubelet.service",
                            "aop investigate linux disk --path /var/lib/kubelet",
                            "aop investigate linux disk --path /var/lib/containerd",
                        ],
                    )
                ]
            )
            next_aop_commands.extend(
                [
                    "aop investigate linux host --path /var/lib/kubelet --service kubelet.service",
                    "aop investigate linux disk --path /var/lib/containerd",
                ]
            )
            cloud_checks.append(
                "Check node volume size, IOPS, burst balance, resize events, and filesystem expansion state."
            )
            memory_notes.append(
                "Preserve DiskPressure condition, eviction events, kubelet path usage, runtime path usage, inode usage, and storage backend evidence."
            )
        elif condition == "MemoryPressure":
            signals.append(
                KubernetesNodeSignal(
                    condition="MemoryPressure",
                    status="True",
                    reason="Node memory pressure",
                    summary=(
                        "Kubelet reports memory pressure and may evict pods."
                    ),
                )
            )
            evidence.append(
                _evidence(
                    "linux-host-memory",
                    (
                        "Separates host memory pressure from cgroup OOM, "
                        "swap, reclaim, and process-level memory usage."
                    ),
                    [
                        "aop investigate linux host",
                        "aop investigate linux memory",
                        "aop linux internals --interval 5",
                    ],
                )
            )
            next_aop_commands.extend(
                [
                    "aop investigate linux host",
                    "aop investigate linux memory",
                    "aop linux internals --interval 5",
                ]
            )
            cloud_checks.append(
                "Check instance size, autoscaler decisions, recent workload placement, and node allocatable memory."
            )
            memory_notes.append(
                "Preserve MemoryPressure condition, pod evictions, MemAvailable, PSI, swap, and OOM evidence."
            )
        elif condition == "PIDPressure":
            signals.append(
                KubernetesNodeSignal(
                    condition="PIDPressure",
                    status="True",
                    reason="Node process ID pressure",
                    summary=(
                        "Kubelet reports PID pressure, often caused by fork "
                        "storms, process leaks, or pod density."
                    ),
                )
            )
            evidence.append(
                _evidence(
                    "linux-process-cgroup",
                    (
                        "Confirms process count, process tree, PID cgroup "
                        "limits, and whether kubelet/runtime are affected."
                    ),
                    [
                        "aop linux processes --top 30",
                        "aop linux cgroups --pid <kubelet-or-runtime-pid>",
                        "aop investigate linux host --service kubelet.service",
                    ],
                )
            )
            next_aop_commands.extend(
                [
                    "aop linux processes --top 30",
                    "aop investigate linux host --service kubelet.service",
                ]
            )
            memory_notes.append(
                "Preserve PIDPressure condition, process count, fork pattern, kubelet/runtime PID state, and affected pods."
            )
        elif condition == "NetworkUnavailable":
            signals.append(
                KubernetesNodeSignal(
                    condition="NetworkUnavailable",
                    status="True",
                    reason="Node network unavailable",
                    summary=(
                        "Kubernetes reports node networking is unavailable, "
                        "usually involving CNI, routes, NIC, DNS, or cloud networking."
                    ),
                )
            )
            evidence.append(
                _evidence(
                    "linux-network-nic",
                    (
                        "Confirms NIC carrier, link errors, routes, DNS, and "
                        "host networking before blaming pods."
                    ),
                    [
                        "aop investigate linux host --iface <node-interface>",
                        "aop investigate linux network --iface <node-interface>",
                        "aop linux nic --iface <node-interface>",
                    ],
                )
            )
            next_aop_commands.extend(
                [
                    "aop investigate linux host --iface <node-interface>",
                    "aop investigate linux network --iface <node-interface>",
                ]
            )
            cloud_checks.append(
                "Check ENI/NIC attachment, subnet routes, security groups, NACLs, and CNI plugin health."
            )
            memory_notes.append(
                "Preserve NetworkUnavailable condition, CNI events, route state, NIC counters, DNS, and cloud network evidence."
            )
        elif condition in {"ReadyFalse", "NodeNotReady"}:
            signals.append(
                KubernetesNodeSignal(
                    condition="Ready",
                    status="False",
                    reason="Node not ready",
                    summary=(
                        "The control plane cannot rely on the node; kubelet, "
                        "runtime, network, storage, memory, CPU, or cloud instance health may be involved."
                    ),
                )
            )
            evidence.extend(
                [
                    _evidence(
                        "linux-host",
                        "Correlates the broad host state before choosing one failure layer.",
                        [
                            "aop investigate linux host --service kubelet.service",
                            "aop investigate linux service --service kubelet.service",
                            "aop investigate linux network",
                        ],
                    ),
                    _evidence(
                        "container-runtime",
                        "Runtime failure can make kubelet report node readiness loss.",
                        [
                            "aop investigate linux service --service containerd.service",
                            "aop investigate linux disk --path /var/lib/containerd",
                        ],
                    ),
                ]
            )
            next_aop_commands.extend(
                [
                    "aop investigate linux host --service kubelet.service",
                    "aop investigate linux service --service containerd.service",
                    "aop investigate linux disk --path /var/lib/containerd",
                ]
            )
            cloud_checks.append(
                "Check VM/EC2 health checks, maintenance events, instance networking, and node lifecycle events."
            )
            memory_notes.append(
                "Preserve Ready=False transition time, kubelet service state, runtime service state, host pressure, and cloud instance health."
            )

    primary = _primary_diagnosis(normalized)
    severity = _severity(normalized)
    confidence = 94 if severity == "critical" else 88

    return KubernetesNodeLinuxPlan(
        node=node,
        primary_diagnosis=primary,
        severity=severity,
        confidence=confidence,
        summary=(
            f"Kubernetes node {node} requires Linux host evidence for "
            f"{', '.join(normalized)}."
        ),
        kubernetes_signals=signals,
        linux_evidence=_dedupe_evidence(evidence),
        kubernetes_checks=list(dict.fromkeys(kubernetes_checks)),
        next_aop_commands=list(dict.fromkeys(next_aop_commands)),
        cloud_checks=list(dict.fromkeys(cloud_checks)),
        do_not_assume=do_not_assume,
        memory_note=" ".join(memory_notes)
        or "Preserve node condition timeline, events, and Linux host evidence.",
    )


def _primary_diagnosis(conditions: list[str]) -> str:
    if "DiskPressure" in conditions:
        return "node_disk_pressure_requires_linux_storage_check"
    if "MemoryPressure" in conditions:
        return "node_memory_pressure_requires_linux_memory_check"
    if "PIDPressure" in conditions:
        return "node_pid_pressure_requires_linux_process_check"
    if "NetworkUnavailable" in conditions:
        return "node_network_unavailable_requires_linux_network_check"
    return "node_not_ready_requires_linux_host_check"


def _severity(conditions: list[str]) -> str:
    if any(
        condition in conditions
        for condition in ("DiskPressure", "NetworkUnavailable", "NodeNotReady", "ReadyFalse")
    ):
        return "critical"
    return "warning"


def _dedupe_evidence(
    evidence: list[LinuxEvidenceRequirement],
) -> list[LinuxEvidenceRequirement]:
    seen: set[tuple[str, str]] = set()
    deduped: list[LinuxEvidenceRequirement] = []
    for item in evidence:
        key = (item.domain, item.reason)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
