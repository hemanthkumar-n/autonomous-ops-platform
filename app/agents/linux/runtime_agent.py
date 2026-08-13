from __future__ import annotations

from app.schemas.linux import (
    LinuxRuntimeDangerousAction,
    LinuxRuntimeEvidenceArea,
    LinuxRuntimePlan,
)


SUPPORTED_RUNTIMES = ("containerd", "crio", "docker")
SUPPORTED_RUNTIME_SYMPTOMS = (
    "image-pull",
    "container-create",
    "disk-pressure",
    "node-not-ready",
    "runtime-down",
    "cni-network",
    "log-pressure",
    "pid-pressure",
    "cgroup",
)

RUNTIME_ALIASES = {
    "cri-o": "crio",
    "cri_o": "crio",
    "crio": "crio",
    "containerd": "containerd",
    "docker": "docker",
    "dockerd": "docker",
}

SYMPTOM_ALIASES = {
    "pull": "image-pull",
    "image": "image-pull",
    "imagepull": "image-pull",
    "imagepullbackoff": "image-pull",
    "errimagepull": "image-pull",
    "create": "container-create",
    "createcontainererror": "container-create",
    "runtime": "runtime-down",
    "down": "runtime-down",
    "disk": "disk-pressure",
    "diskpressure": "disk-pressure",
    "node": "node-not-ready",
    "notready": "node-not-ready",
    "network": "cni-network",
    "cni": "cni-network",
    "logs": "log-pressure",
    "log": "log-pressure",
    "pid": "pid-pressure",
    "pidpressure": "pid-pressure",
    "cgroups": "cgroup",
}


def list_supported_runtimes() -> list[str]:
    return list(SUPPORTED_RUNTIMES)


def list_runtime_symptoms() -> list[str]:
    return list(SUPPORTED_RUNTIME_SYMPTOMS)


def normalize_runtime(runtime: str) -> str:
    key = runtime.strip().lower()
    if key in RUNTIME_ALIASES:
        return RUNTIME_ALIASES[key]

    supported = ", ".join(SUPPORTED_RUNTIMES)
    raise ValueError(
        f"Unsupported Linux container runtime '{runtime}'. Supported: {supported}"
    )


def normalize_runtime_symptom(symptom: str | None) -> str:
    if not symptom:
        return "runtime-down"

    key = symptom.strip().lower().replace("_", "-").replace(" ", "-")
    compact = key.replace("-", "")
    if key in SUPPORTED_RUNTIME_SYMPTOMS:
        return key
    if key in SYMPTOM_ALIASES:
        return SYMPTOM_ALIASES[key]
    if compact in SYMPTOM_ALIASES:
        return SYMPTOM_ALIASES[compact]

    supported = ", ".join(SUPPORTED_RUNTIME_SYMPTOMS)
    raise ValueError(
        f"Unsupported container runtime symptom '{symptom}'. Supported: {supported}"
    )


def build_runtime_plan(
    runtime: str = "containerd",
    symptom: str | None = None,
) -> LinuxRuntimePlan:
    normalized_runtime = normalize_runtime(runtime)
    normalized_symptom = normalize_runtime_symptom(symptom)
    profile = _runtime_profile(normalized_runtime)
    evidence = _base_evidence(profile)
    next_aop_commands = [
        f"aop investigate linux service --service {profile['service']}",
        f"aop investigate linux disk --path {profile['storage_path']}",
        "aop investigate linux host --service kubelet.service",
    ]

    evidence.extend(_symptom_evidence(normalized_runtime, normalized_symptom, profile))
    next_aop_commands.extend(
        _symptom_aop_commands(normalized_runtime, normalized_symptom, profile)
    )

    return LinuxRuntimePlan(
        runtime=normalized_runtime,
        symptom=normalized_symptom,
        primary_diagnosis=_primary_diagnosis(normalized_runtime, normalized_symptom),
        severity=_severity(normalized_symptom),
        confidence=92,
        summary=(
            f"Plan read-only evidence for {normalized_runtime} runtime symptom "
            f"{normalized_symptom} before restarting, pruning, or deleting data."
        ),
        service_units=profile["service_units"],
        storage_paths=profile["storage_paths"],
        evidence=_dedupe_evidence(evidence),
        next_aop_commands=list(dict.fromkeys(next_aop_commands)),
        kubernetes_correlation=_kubernetes_correlation(normalized_symptom),
        aws_correlation=_aws_correlation(normalized_symptom),
        do_not_assume=_do_not_assume(),
        dangerous_actions=_dangerous_actions(normalized_runtime, profile),
        memory_note=_memory_note(normalized_runtime, normalized_symptom),
    )


def _runtime_profile(runtime: str) -> dict:
    if runtime == "crio":
        return {
            "service": "crio.service",
            "service_units": ["crio.service", "kubelet.service"],
            "storage_path": "/var/lib/containers",
            "storage_paths": ["/var/lib/containers", "/var/log/pods", "/var/log/containers"],
            "cli": "crictl",
            "native_cli": "crio",
        }
    if runtime == "docker":
        return {
            "service": "docker.service",
            "service_units": ["docker.service", "kubelet.service"],
            "storage_path": "/var/lib/docker",
            "storage_paths": ["/var/lib/docker", "/var/log/pods", "/var/log/containers"],
            "cli": "docker",
            "native_cli": "docker",
        }
    return {
        "service": "containerd.service",
        "service_units": ["containerd.service", "kubelet.service"],
        "storage_path": "/var/lib/containerd",
        "storage_paths": ["/var/lib/containerd", "/var/log/pods", "/var/log/containers"],
        "cli": "crictl",
        "native_cli": "ctr",
    }


def _area(area: str, reason: str, commands: list[str]) -> LinuxRuntimeEvidenceArea:
    return LinuxRuntimeEvidenceArea(area=area, reason=reason, commands=commands)


def _base_evidence(profile: dict) -> list[LinuxRuntimeEvidenceArea]:
    service = profile["service"]
    storage_path = profile["storage_path"]
    cli = profile["cli"]
    native_cli = profile["native_cli"]
    return [
        _area(
            "service-state",
            "Confirms whether runtime and kubelet are active, failed, or restart-looping.",
            [
                f"systemctl status {service} --no-pager --full",
                "systemctl status kubelet --no-pager --full",
                f"systemctl show {service}",
                "systemctl show kubelet",
            ],
        ),
        _area(
            "runtime-journal",
            "Preserves runtime and kubelet error text before restart or log rotation.",
            [
                f"journalctl -u {service} --since '2 hours ago' --no-pager",
                "journalctl -u kubelet --since '2 hours ago' --no-pager",
            ],
        ),
        _area(
            "runtime-storage",
            "Separates image, snapshot, log, inode, and filesystem pressure.",
            [
                f"df -hT {storage_path} /var/log/pods /var/log/containers",
                f"df -i {storage_path} /var/log/pods /var/log/containers",
                f"du -x -h --max-depth=1 {storage_path} | sort -h",
                "aop investigate linux disk --path /var/log/pods",
            ],
        ),
        _area(
            "runtime-inventory",
            "Shows pods, containers, images, namespaces, and runtime health without pruning.",
            _runtime_inventory_commands(cli, native_cli),
        ),
        _area(
            "host-correlation",
            "Correlates runtime symptoms with CPU, memory, disk, network, boot, and service state.",
            [
                "aop investigate linux host --service kubelet.service",
                f"aop investigate linux service --service {service}",
                f"aop investigate linux disk --path {storage_path}",
            ],
        ),
    ]


def _runtime_inventory_commands(cli: str, native_cli: str) -> list[str]:
    if cli == "docker":
        return [
            "docker info",
            "docker ps -a",
            "docker images",
            "docker system df",
        ]
    commands = [
        "crictl info",
        "crictl pods",
        "crictl ps -a",
        "crictl images",
    ]
    if native_cli == "ctr":
        commands.extend(
            [
                "ctr namespaces list",
                "ctr -n k8s.io containers list",
                "ctr -n k8s.io images list",
                "ctr -n k8s.io snapshots list",
            ]
        )
    return commands


def _symptom_evidence(
    runtime: str,
    symptom: str,
    profile: dict,
) -> list[LinuxRuntimeEvidenceArea]:
    storage_path = profile["storage_path"]
    if symptom == "image-pull":
        return [
            _area(
                "image-pull",
                "Image pull failures need registry, DNS, auth, certificate, proxy, and runtime storage evidence.",
                [
                    "kubectl describe pod <pod> -n <namespace>",
                    "kubectl get events -n <namespace> --sort-by=.lastTimestamp",
                    f"journalctl -u {profile['service']} -g 'pull|image|registry|certificate|x509|auth|timeout' --no-pager",
                    "aop investigate linux network",
                    f"aop investigate linux disk --path {storage_path}",
                ],
            )
        ]
    if symptom == "container-create":
        return [
            _area(
                "container-create",
                "Create failures can come from runtime logs, mounts, cgroups, SELinux, storage, or CNI setup.",
                [
                    "kubectl describe pod <pod> -n <namespace>",
                    f"journalctl -u {profile['service']} -g 'create|mount|cgroup|permission|snapshot|overlay' --no-pager",
                    "journalctl -u kubelet -g 'CreateContainer|container create|FailedMount|cgroup' --no-pager",
                    "aop linux security",
                    "aop linux cgroups --pid <runtime-or-shim-pid>",
                ],
            )
        ]
    if symptom == "disk-pressure":
        return [
            _area(
                "runtime-disk-pressure",
                "Runtime disk pressure includes images, snapshots, writable layers, pod logs, inodes, and deleted-open files.",
                [
                    f"aop investigate linux disk --path {storage_path}",
                    "aop investigate linux disk --path /var/lib/kubelet",
                    "aop investigate linux disk --path /var/log/pods",
                    "lsof +L1 /var/log/pods",
                ],
            )
        ]
    if symptom == "node-not-ready":
        return [
            _area(
                "node-readiness",
                "Node readiness loss may be runtime down, kubelet down, host pressure, network, or kernel instability.",
                [
                    "aop investigate linux host --service kubelet.service",
                    f"aop investigate linux service --service {profile['service']}",
                    "aop investigate linux boot",
                    "aop investigate linux network",
                ],
            )
        ]
    if symptom == "cni-network":
        return [
            _area(
                "cni-network",
                "CNI failures can prevent sandbox creation even when runtime service is running.",
                [
                    "ls -la /etc/cni/net.d",
                    "ls -la /opt/cni/bin",
                    "journalctl -u kubelet -g 'CNI|network plugin|sandbox|pod sandbox' --no-pager",
                    "aop investigate linux network",
                    "aop linux nic",
                ],
            )
        ]
    if symptom == "log-pressure":
        return [
            _area(
                "container-log-pressure",
                "Container logs can fill bytes or inodes and trigger eviction or runtime write errors.",
                [
                    "aop investigate linux disk --path /var/log/pods",
                    "aop investigate linux disk --path /var/log/containers",
                    "find /var/log/pods -xdev -type f -size +100M -printf '%s %p\\n' | sort -n | tail -20",
                    "lsof +L1 /var/log/pods",
                ],
            )
        ]
    if symptom == "pid-pressure":
        return [
            _area(
                "runtime-pid-pressure",
                "PID pressure may prevent shim, pause, or container processes from starting.",
                [
                    "aop linux processes --top 30",
                    "aop linux cgroups --pid <kubelet-or-runtime-pid>",
                    "systemctl show kubelet -p TasksCurrent -p TasksMax",
                    f"systemctl show {profile['service']} -p TasksCurrent -p TasksMax",
                ],
            )
        ]
    if symptom == "cgroup":
        return [
            _area(
                "runtime-cgroup",
                "Runtime and kubelet failures often depend on cgroup v1/v2 mode, limits, and event counters.",
                [
                    "cat /proc/cgroups",
                    "stat -fc %T /sys/fs/cgroup",
                    "aop linux cgroups --pid <runtime-or-shim-pid> --interval 5",
                    "aop investigate linux memory --pid <container-pid>",
                ],
            )
        ]
    return []


def _symptom_aop_commands(runtime: str, symptom: str, profile: dict) -> list[str]:
    storage_path = profile["storage_path"]
    if symptom == "image-pull":
        return [
            "aop investigate linux network",
            f"aop investigate linux disk --path {storage_path}",
            "aop investigate k8s-linux --incident ImagePullBackOff",
        ]
    if symptom == "container-create":
        return [
            "aop investigate k8s-linux --incident CreateContainerError",
            "aop linux cgroups --pid <runtime-or-shim-pid>",
            "aop linux security",
        ]
    if symptom == "disk-pressure":
        return [
            "aop investigate k8s-node --node <node> --condition DiskPressure",
            f"aop investigate linux disk --path {storage_path}",
            "aop investigate linux disk --path /var/lib/kubelet",
        ]
    if symptom == "node-not-ready":
        return [
            "aop investigate k8s-node --node <node> --condition NodeNotReady",
            "aop investigate linux host --service kubelet.service",
        ]
    if symptom == "cni-network":
        return [
            "aop investigate k8s-node --node <node> --condition NetworkUnavailable",
            "aop investigate linux network",
            "aop linux nic",
        ]
    if symptom == "log-pressure":
        return [
            "aop investigate linux disk --path /var/log/pods",
            "aop investigate linux disk --path /var/log/containers",
        ]
    if symptom == "pid-pressure":
        return [
            "aop investigate k8s-node --node <node> --condition PIDPressure",
            "aop linux processes --top 30",
        ]
    if symptom == "cgroup":
        return [
            "aop linux cgroups --pid <runtime-or-shim-pid> --interval 5",
            "aop investigate linux memory --pid <container-pid>",
        ]
    return []


def _primary_diagnosis(runtime: str, symptom: str) -> str:
    return f"{runtime}_{symptom.replace('-', '_')}_requires_runtime_evidence"


def _severity(symptom: str) -> str:
    if symptom in {"runtime-down", "node-not-ready", "disk-pressure"}:
        return "critical"
    return "warning"


def _kubernetes_correlation(symptom: str) -> list[str]:
    mapping = {
        "image-pull": [
            "ImagePullBackOff",
            "ErrImagePull",
            "Node DNS/proxy/registry path",
        ],
        "container-create": ["CreateContainerError", "FailedMount", "sandbox creation"],
        "disk-pressure": ["DiskPressure", "pod eviction", "image garbage collection"],
        "node-not-ready": ["NodeNotReady", "Ready=False", "runtime unavailable"],
        "runtime-down": ["NodeNotReady", "CreateContainerError", "pod sandbox failure"],
        "cni-network": ["NetworkUnavailable", "pod sandbox network setup failure"],
        "log-pressure": ["DiskPressure", "eviction", "ephemeral-storage pressure"],
        "pid-pressure": ["PIDPressure", "fork failure", "shim creation failure"],
        "cgroup": ["OOMKilled", "CreateContainerError", "kubelet cgroup setup"],
    }
    return mapping.get(symptom, [])


def _aws_correlation(symptom: str) -> list[str]:
    if symptom in {"disk-pressure", "image-pull", "log-pressure"}:
        return [
            "Check EBS/root volume size, IOPS, throughput, burst balance, and recent resize events.",
            "Check NAT/proxy/registry egress for image pulls when network evidence points outward.",
        ]
    if symptom in {"node-not-ready", "runtime-down"}:
        return [
            "Check EC2 status checks, maintenance events, ENI attachment, and instance storage health.",
        ]
    return [
        "Correlate node timeline with cloud maintenance, scaling, image, and network changes.",
    ]


def _do_not_assume() -> list[str]:
    return [
        "Do not restart kubelet or the runtime before preserving service and journal evidence.",
        "Do not prune images or delete runtime directories before proving the pressure source.",
        "Do not treat Kubernetes events as root cause; they are symptoms pointing to host/runtime evidence.",
        "Do not print secrets, registry tokens, or image pull credentials into memory.",
    ]


def _dangerous_actions(
    runtime: str,
    profile: dict,
) -> list[LinuxRuntimeDangerousAction]:
    storage_path = profile["storage_path"]
    service = profile["service"]
    prune = "docker system prune" if runtime == "docker" else "crictl rmi --prune"
    return [
        LinuxRuntimeDangerousAction(
            action=f"systemctl restart {service}",
            why_dangerous="Restart can disrupt all pods using that runtime and erase timing evidence.",
            safer_first_step=f"Collect `systemctl status {service}` and `journalctl -u {service}` first.",
        ),
        LinuxRuntimeDangerousAction(
            action="systemctl restart kubelet",
            why_dangerous="Restart can change node condition timing and trigger pod disruption.",
            safer_first_step="Collect kubelet status, recent journal, node events, and host pressure evidence first.",
        ),
        LinuxRuntimeDangerousAction(
            action=f"rm -rf {storage_path}",
            why_dangerous="Manual runtime directory deletion can corrupt runtime state and orphan pods/images.",
            safer_first_step=f"Use `aop investigate linux disk --path {storage_path}` and runtime inventory first.",
        ),
        LinuxRuntimeDangerousAction(
            action=prune,
            why_dangerous="Pruning can delete evidence and impact workloads if image/runtime ownership is misunderstood.",
            safer_first_step="Map image usage, runtime disk pressure, kubelet GC events, and eviction state first.",
        ),
    ]


def _memory_note(runtime: str, symptom: str) -> str:
    return (
        f"Store {runtime} symptom {symptom}, runtime service state, kubelet "
        "state, journal excerpts, runtime storage paths, Kubernetes events, "
        "and the do-not-assume decisions together."
    )


def _dedupe_evidence(
    evidence: list[LinuxRuntimeEvidenceArea],
) -> list[LinuxRuntimeEvidenceArea]:
    seen: set[str] = set()
    deduped: list[LinuxRuntimeEvidenceArea] = []
    for item in evidence:
        if item.area in seen:
            continue
        seen.add(item.area)
        deduped.append(item)
    return deduped
