from __future__ import annotations

from app.schemas.correlation import (
    KubernetesLinuxCorrelation,
    LinuxEvidenceRequirement,
)


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


K8S_LINUX_CORRELATIONS: dict[str, KubernetesLinuxCorrelation] = {
    "OOMKilled": KubernetesLinuxCorrelation(
        incident="OOMKilled",
        kubernetes_meaning=(
            "A container was terminated after exceeding a memory boundary. "
            "The boundary may be the pod/container cgroup limit, node memory "
            "pressure, or application allocation behavior."
        ),
        linux_evidence=[
            _evidence(
                "memory",
                "Confirms host memory availability, swap activity, and recent "
                "kernel OOM evidence.",
                [
                    "aop linux memory",
                    "aop investigate linux memory",
                ],
            ),
            _evidence(
                "cgroups",
                "Separates container/cgroup OOM from host-wide memory "
                "pressure.",
                [
                    "aop linux cgroups --pid <container-pid>",
                    "aop investigate linux memory --pid <container-pid>",
                ],
            ),
            _evidence(
                "internals",
                "PSI and VM deltas show reclaim, swap, and stall behavior "
                "during the incident window.",
                ["aop linux internals --interval 5"],
            ),
        ],
        kubernetes_checks=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl top pod <pod> -n <namespace>",
            "kubectl get pod <pod> -n <namespace> -o yaml",
        ],
        cloud_checks=[
            "Check node instance memory size and recent scaling/change events.",
        ],
        do_not_assume=[
            "Do not assume host memory is exhausted only because a pod was OOMKilled.",
            "Do not assume increasing limits is safe before identifying the allocation path.",
        ],
        next_aop_commands=[
            "aop investigate linux memory --pid <container-pid>",
            "aop linux cgroups --pid <container-pid> --interval 5",
            "aop linux internals --interval 5",
        ],
        memory_note=(
            "Store pod limits, restart count, victim process, cgroup events, "
            "and host memory pressure together."
        ),
    ),
    "CrashLoopBackOff": KubernetesLinuxCorrelation(
        incident="CrashLoopBackOff",
        kubernetes_meaning=(
            "Kubernetes is repeatedly restarting a container that exits or "
            "fails health checks."
        ),
        linux_evidence=[
            _evidence(
                "service/process",
                "Process state and service-style startup evidence explain "
                "whether the workload exits, hangs, or misses dependencies.",
                [
                    "aop linux processes --top 20",
                    "aop linux logs",
                ],
            ),
            _evidence(
                "memory",
                "Crash loops can hide a previous OOM termination.",
                ["aop investigate linux memory"],
            ),
            _evidence(
                "network",
                "Startup failures often come from missing listeners, DNS, or "
                "dependency connectivity.",
                ["aop linux network"],
            ),
        ],
        kubernetes_checks=[
            "kubectl logs <pod> -n <namespace> --previous",
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl get events -n <namespace> --sort-by=.lastTimestamp",
        ],
        cloud_checks=[
            "Check recent deployment, image, secret, config, or dependency changes.",
        ],
        do_not_assume=[
            "Do not treat CrashLoopBackOff as root cause; it is a restart symptom.",
            "Do not ignore previous container termination reason.",
        ],
        next_aop_commands=[
            "aop linux processes --top 20",
            "aop linux logs",
            "aop investigate linux memory",
        ],
        memory_note=(
            "Preserve previous logs, exit code, restart count, config change, "
            "and any Linux memory/process evidence."
        ),
    ),
    "ImagePullBackOff": KubernetesLinuxCorrelation(
        incident="ImagePullBackOff",
        kubernetes_meaning=(
            "The kubelet cannot pull the requested image after retries."
        ),
        linux_evidence=[
            _evidence(
                "network",
                "Image pulls require DNS, default route, registry reachability, "
                "and working node networking.",
                [
                    "aop linux network",
                    "aop investigate linux network",
                ],
            ),
            _evidence(
                "nic",
                "NIC carrier, packet errors, driver, or speed issues can make "
                "registry access fail intermittently.",
                ["aop linux nic"],
            ),
            _evidence(
                "disk",
                "Container runtime disk pressure can block image pulls even "
                "when the image reference is correct.",
                ["aop investigate linux disk --path /var/lib"],
            ),
        ],
        kubernetes_checks=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl get secret -n <namespace>",
            "kubectl get events -n <namespace> --sort-by=.lastTimestamp",
        ],
        cloud_checks=[
            "Check registry availability, IAM/registry auth, NAT gateway, proxy, and firewall paths.",
        ],
        do_not_assume=[
            "Do not assume the image name is wrong before checking registry auth and node network.",
            "Do not ignore runtime disk pressure on the node.",
        ],
        next_aop_commands=[
            "aop investigate linux network",
            "aop linux nic",
            "aop investigate linux disk --path /var/lib",
        ],
        memory_note=(
            "Store image reference, pull event text, node network evidence, "
            "registry/auth result, and runtime disk state."
        ),
    ),
    "ErrImagePull": KubernetesLinuxCorrelation(
        incident="ErrImagePull",
        kubernetes_meaning=(
            "The first image pull attempt failed before Kubernetes entered "
            "backoff."
        ),
        linux_evidence=[],
        kubernetes_checks=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl get events -n <namespace> --sort-by=.lastTimestamp",
        ],
        cloud_checks=[
            "Check registry, IAM, image tag, proxy, and network egress.",
        ],
        do_not_assume=[
            "Do not wait for backoff before preserving the first pull error.",
        ],
        next_aop_commands=[
            "aop investigate k8s-linux --incident ImagePullBackOff",
        ],
        memory_note=(
            "Use the ImagePullBackOff correlation path after preserving the "
            "first ErrImagePull event."
        ),
    ),
    "CreateContainerConfigError": KubernetesLinuxCorrelation(
        incident="CreateContainerConfigError",
        kubernetes_meaning=(
            "Kubernetes could not build the container config, commonly because "
            "a ConfigMap, Secret, key, volume, or environment reference is invalid."
        ),
        linux_evidence=[
            _evidence(
                "node-filesystem",
                "Host evidence is secondary, but volume mount and kubelet "
                "node state may matter for projected volumes.",
                ["aop linux logs"],
            ),
        ],
        kubernetes_checks=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl get configmap,secret -n <namespace>",
            "kubectl get pod <pod> -n <namespace> -o yaml",
        ],
        cloud_checks=[
            "Check external secret manager or CSI provider health if used.",
        ],
        do_not_assume=[
            "Do not debug application code before validating missing config references.",
            "Do not print secret values into incident memory.",
        ],
        next_aop_commands=[
            "aop linux logs",
        ],
        memory_note=(
            "Record object names and missing keys, but never store secret values."
        ),
    ),
    "CreateContainerError": KubernetesLinuxCorrelation(
        incident="CreateContainerError",
        kubernetes_meaning=(
            "The runtime accepted the pod spec but failed while creating or "
            "starting the container."
        ),
        linux_evidence=[
            _evidence(
                "runtime",
                "Container runtime, kubelet, storage, and cgroup setup can be "
                "behind startup failures.",
                [
                    "aop linux logs",
                    "aop linux cgroups --pid <runtime-or-shim-pid>",
                ],
            ),
            _evidence(
                "disk",
                "Runtime storage exhaustion can prevent container creation.",
                ["aop investigate linux disk --path /var/lib"],
            ),
        ],
        kubernetes_checks=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl get events -n <namespace> --sort-by=.lastTimestamp",
        ],
        cloud_checks=[
            "Check node image, runtime version, and recent node maintenance.",
        ],
        do_not_assume=[
            "Do not treat it as an application crash before checking runtime events.",
        ],
        next_aop_commands=[
            "aop linux logs",
            "aop investigate linux disk --path /var/lib",
        ],
        memory_note=(
            "Store kubelet/runtime event text, node name, runtime storage, and "
            "cgroup setup evidence."
        ),
    ),
    "FailedScheduling": KubernetesLinuxCorrelation(
        incident="FailedScheduling",
        kubernetes_meaning=(
            "The scheduler could not place the pod on a node because of "
            "resources, taints, affinity, topology, or node conditions."
        ),
        linux_evidence=[
            _evidence(
                "capacity",
                "Node CPU, memory, disk, and pressure evidence may explain why "
                "capacity is unavailable.",
                [
                    "aop linux cpu",
                    "aop linux memory",
                    "aop linux disk --path /var",
                ],
            ),
            _evidence(
                "internals",
                "Pressure and cgroup evidence separate real host contention "
                "from Kubernetes policy constraints.",
                ["aop linux internals --interval 5"],
            ),
        ],
        kubernetes_checks=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl describe node <node>",
            "kubectl get nodes",
        ],
        cloud_checks=[
            "Check autoscaler, instance quota, subnet IP capacity, and recent scaling failures.",
        ],
        do_not_assume=[
            "Do not assume adding nodes fixes taints, affinity, or quota problems.",
        ],
        next_aop_commands=[
            "aop linux cpu",
            "aop linux memory",
            "aop investigate linux disk --path /var",
        ],
        memory_note=(
            "Store scheduler reason, requested resources, node conditions, "
            "and host pressure evidence."
        ),
    ),
    "DiskPressure": KubernetesLinuxCorrelation(
        incident="DiskPressure",
        kubernetes_meaning=(
            "The node reports filesystem pressure that can trigger evictions "
            "or block container runtime operations."
        ),
        linux_evidence=[
            _evidence(
                "disk",
                "Bytes, inodes, mount state, deleted-open files, and kernel "
                "storage errors decide the real disk path.",
                [
                    "aop linux plan disk --path /var/lib/kubelet",
                    "aop investigate linux disk --path /var/lib/kubelet",
                    "aop investigate linux disk --path /var/lib",
                ],
            ),
        ],
        kubernetes_checks=[
            "kubectl describe node <node>",
            "kubectl get events --all-namespaces --sort-by=.lastTimestamp",
        ],
        cloud_checks=[
            "Check EBS/volume size, burst balance, IOPS, snapshots, and recent resize events.",
        ],
        do_not_assume=[
            "Do not delete files before identifying whether bytes, inodes, deleted-open files, or I/O errors are responsible.",
        ],
        next_aop_commands=[
            "aop investigate linux disk --path /var/lib/kubelet",
            "aop investigate linux disk --path /var/lib",
        ],
        memory_note=(
            "Store node condition, kubelet path usage, runtime path usage, "
            "inode usage, and cloud volume evidence."
        ),
    ),
    "MemoryPressure": KubernetesLinuxCorrelation(
        incident="MemoryPressure",
        kubernetes_meaning=(
            "The node reports memory pressure and may evict pods."
        ),
        linux_evidence=[
            _evidence(
                "memory",
                "Host memory, swap, OOM, and reclaim evidence decide whether "
                "pressure is active or historical.",
                [
                    "aop linux memory",
                    "aop investigate linux memory",
                    "aop linux internals --interval 5",
                ],
            ),
        ],
        kubernetes_checks=[
            "kubectl describe node <node>",
            "kubectl top node <node>",
            "kubectl get events --all-namespaces --sort-by=.lastTimestamp",
        ],
        cloud_checks=[
            "Check instance size, autoscaler decisions, and recent workload placement.",
        ],
        do_not_assume=[
            "Do not blame one pod until requests, limits, node pressure, and cgroup evidence are compared.",
        ],
        next_aop_commands=[
            "aop investigate linux memory",
            "aop linux internals --interval 5",
        ],
        memory_note=(
            "Store node memory condition, eviction events, MemAvailable, "
            "swap activity, PSI, and OOM evidence."
        ),
    ),
    "NodeNotReady": KubernetesLinuxCorrelation(
        incident="NodeNotReady",
        kubernetes_meaning=(
            "The control plane cannot treat the node as healthy. Causes may "
            "include kubelet, runtime, network, disk, CPU starvation, or cloud "
            "instance health."
        ),
        linux_evidence=[
            _evidence(
                "service",
                "kubelet or container runtime service failure can make the "
                "node NotReady.",
                [
                    "aop investigate linux service --service kubelet",
                    "aop linux services",
                ],
            ),
            _evidence(
                "network",
                "Node readiness depends on working node networking and DNS.",
                [
                    "aop investigate linux network",
                    "aop linux nic",
                ],
            ),
            _evidence(
                "host-pressure",
                "Disk, memory, CPU, and kernel pressure can stop kubelet or "
                "runtime heartbeats.",
                [
                    "aop investigate linux disk --path /var",
                    "aop investigate linux memory",
                    "aop investigate linux cpu",
                ],
            ),
        ],
        kubernetes_checks=[
            "kubectl describe node <node>",
            "kubectl get events --all-namespaces --sort-by=.lastTimestamp",
        ],
        cloud_checks=[
            "Check EC2/VM health, network interface state, security groups, and maintenance events.",
        ],
        do_not_assume=[
            "Do not drain or replace the node before preserving kubelet, runtime, and host pressure evidence.",
        ],
        next_aop_commands=[
            "aop investigate linux service --service kubelet",
            "aop investigate linux network",
            "aop investigate linux disk --path /var",
            "aop investigate linux memory",
            "aop investigate linux cpu",
        ],
        memory_note=(
            "Store node condition timeline, kubelet state, runtime evidence, "
            "network evidence, and cloud instance health."
        ),
    ),
}


ALIASES = {
    "imagepullfailure": "ImagePullBackOff",
    "imagepull": "ImagePullBackOff",
    "errimagepull": "ErrImagePull",
    "oom": "OOMKilled",
    "memoryexhaustion": "OOMKilled",
    "crashloop": "CrashLoopBackOff",
    "applicationcrashloop": "CrashLoopBackOff",
    "configerror": "CreateContainerConfigError",
    "containerconfig": "CreateContainerConfigError",
    "containerstartup": "CreateContainerError",
    "schedulingfailure": "FailedScheduling",
    "disk": "DiskPressure",
    "node-disk-pressure": "DiskPressure",
    "memory": "MemoryPressure",
    "node-memory-pressure": "MemoryPressure",
    "notready": "NodeNotReady",
    "node-not-ready": "NodeNotReady",
}


def list_k8s_linux_incidents() -> list[str]:
    return sorted(K8S_LINUX_CORRELATIONS)


def normalize_incident_name(incident: str) -> str:
    key = incident.strip()
    if key in K8S_LINUX_CORRELATIONS:
        return key

    alias_key = key.lower().replace("_", "-").replace(" ", "-")
    compact_key = key.lower().replace("_", "").replace("-", "").replace(" ", "")

    if alias_key in ALIASES:
        return ALIASES[alias_key]
    if compact_key in ALIASES:
        return ALIASES[compact_key]

    for known in K8S_LINUX_CORRELATIONS:
        if known.lower() == key.lower():
            return known

    supported = ", ".join(list_k8s_linux_incidents())
    raise ValueError(
        f"Unsupported Kubernetes incident '{incident}'. Supported: {supported}"
    )


def correlate_k8s_linux(
    incident: str,
) -> KubernetesLinuxCorrelation:
    return K8S_LINUX_CORRELATIONS[normalize_incident_name(incident)]
