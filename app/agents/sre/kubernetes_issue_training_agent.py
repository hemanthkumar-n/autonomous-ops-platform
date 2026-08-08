from __future__ import annotations

from app.schemas.kubernetes_knowledge import (
    KubernetesIssueKnowledge,
    KubernetesIssueSource,
)


KUBERNETES_OFFICIAL_SOURCES = [
    KubernetesIssueSource(
        title="Debug Running Pods",
        url="https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/",
    ),
    KubernetesIssueSource(
        title="Node Status",
        url="https://kubernetes.io/docs/reference/node/node-status/",
    ),
    KubernetesIssueSource(
        title="Node-pressure Eviction",
        url="https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/",
    ),
    KubernetesIssueSource(
        title="Monitoring, Logging, and Debugging",
        url="https://kubernetes.io/docs/tasks/debug/",
    ),
]


def _sources(*titles: str) -> list[KubernetesIssueSource]:
    wanted = set(titles)
    return [
        source
        for source in KUBERNETES_OFFICIAL_SOURCES
        if source.title in wanted
    ]


KUBERNETES_ISSUE_KNOWLEDGE: dict[str, KubernetesIssueKnowledge] = {
    "CrashLoopBackOff": KubernetesIssueKnowledge(
        symptom="CrashLoopBackOff",
        summary=(
            "A container repeatedly starts and exits, so Kubernetes delays "
            "restart attempts with backoff."
        ),
        common_causes=[
            "application exits after startup",
            "bad command or arguments",
            "missing dependency",
            "failed liveness probe",
            "configuration or secret regression",
            "previous OOM termination hidden behind restart state",
        ],
        kubernetes_evidence=[
            "current and previous container state",
            "restart count",
            "previous logs",
            "events for probe failures, exit code, or backoff",
            "deployment or config changes near the incident time",
        ],
        linux_evidence=[
            "process exit behavior",
            "kernel OOM evidence",
            "service dependency connectivity",
            "node DNS and route health",
        ],
        safe_kubectl_commands=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl logs <pod> -n <namespace> --previous",
            "kubectl get events -n <namespace> --sort-by=.lastTimestamp",
        ],
        safe_aop_commands=[
            "aop investigate k8s-linux --incident CrashLoopBackOff",
            "aop linux logs",
            "aop investigate linux memory",
        ],
        do_not_assume=[
            "Do not treat CrashLoopBackOff itself as root cause.",
            "Do not ignore previous termination reason or previous logs.",
        ],
        escalation_signals=[
            "restart count rising continuously",
            "all replicas crash after rollout",
            "previous termination shows OOMKilled",
        ],
        sources=_sources("Debug Running Pods", "Monitoring, Logging, and Debugging"),
    ),
    "ImagePullBackOff": KubernetesIssueKnowledge(
        symptom="ImagePullBackOff",
        summary=(
            "The kubelet cannot pull the requested image and is retrying with "
            "backoff."
        ),
        common_causes=[
            "wrong image name or tag",
            "registry authentication failure",
            "registry unavailable",
            "node DNS or egress failure",
            "proxy, firewall, or NAT path issue",
            "container runtime disk pressure",
        ],
        kubernetes_evidence=[
            "pod events showing image pull error text",
            "image reference from pod spec",
            "imagePullSecrets and service account",
            "node name where pull failed",
        ],
        linux_evidence=[
            "node DNS resolver",
            "default route and egress path",
            "NIC link and errors",
            "container runtime filesystem usage",
        ],
        safe_kubectl_commands=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl get pod <pod> -n <namespace> -o yaml",
            "kubectl get secret -n <namespace>",
        ],
        safe_aop_commands=[
            "aop investigate k8s-linux --incident ImagePullBackOff",
            "aop investigate linux network",
            "aop linux nic",
            "aop investigate linux disk --path /var/lib",
        ],
        do_not_assume=[
            "Do not assume the image name is wrong before checking auth and node network.",
            "Do not store registry credentials or secret values in memory.",
        ],
        escalation_signals=[
            "many nodes fail pulling from the same registry",
            "private registry auth fails after secret rotation",
            "node has simultaneous DNS or route failures",
        ],
        sources=_sources("Debug Running Pods", "Monitoring, Logging, and Debugging"),
    ),
    "ErrImagePull": KubernetesIssueKnowledge(
        symptom="ErrImagePull",
        summary=(
            "The initial image pull failed before Kubernetes moved into "
            "ImagePullBackOff retries."
        ),
        common_causes=[
            "bad image reference",
            "registry authentication failure",
            "network egress or DNS failure",
            "registry rate limit or outage",
        ],
        kubernetes_evidence=[
            "first pull event text",
            "image reference",
            "imagePullSecrets",
            "node where the first failure occurred",
        ],
        linux_evidence=[
            "node DNS",
            "node egress route",
            "runtime disk availability",
        ],
        safe_kubectl_commands=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl get events -n <namespace> --sort-by=.lastTimestamp",
        ],
        safe_aop_commands=[
            "aop investigate k8s-linux --incident ErrImagePull",
            "aop investigate k8s-linux --incident ImagePullBackOff",
        ],
        do_not_assume=[
            "Do not wait for retries before preserving the first error text.",
        ],
        escalation_signals=[
            "same pull error across multiple workloads",
            "registry auth failures after credential rotation",
        ],
        sources=_sources("Debug Running Pods"),
    ),
    "OOMKilled": KubernetesIssueKnowledge(
        symptom="OOMKilled",
        summary=(
            "A container was killed because memory allocation exceeded a "
            "container/cgroup or node-level boundary."
        ),
        common_causes=[
            "container limit too low",
            "memory leak",
            "large request spike",
            "node memory pressure",
            "cgroup memory.high or memory.max pressure",
            "swap or reclaim storm",
        ],
        kubernetes_evidence=[
            "last termination reason and exit code",
            "container memory requests and limits",
            "restart count",
            "pod metrics if available",
            "node MemoryPressure condition and eviction events",
        ],
        linux_evidence=[
            "kernel OOM logs",
            "MemAvailable and swap activity",
            "cgroup memory events",
            "PSI memory stall",
            "top RSS processes",
        ],
        safe_kubectl_commands=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl top pod <pod> -n <namespace>",
            "kubectl describe node <node>",
        ],
        safe_aop_commands=[
            "aop investigate k8s-linux --incident OOMKilled",
            "aop investigate linux memory --pid <container-pid>",
            "aop linux cgroups --pid <container-pid> --interval 5",
        ],
        do_not_assume=[
            "Do not assume the whole node is out of memory from a pod OOM alone.",
            "Do not raise limits without checking allocation pattern and node capacity.",
        ],
        escalation_signals=[
            "OOMKilled repeats after restart",
            "node also reports MemoryPressure",
            "multiple pods on the same node are evicted",
        ],
        sources=_sources(
            "Debug Running Pods",
            "Node Status",
            "Node-pressure Eviction",
        ),
    ),
    "CreateContainerConfigError": KubernetesIssueKnowledge(
        symptom="CreateContainerConfigError",
        summary=(
            "Kubernetes cannot construct the container config, usually due to "
            "missing or invalid referenced objects."
        ),
        common_causes=[
            "missing ConfigMap",
            "missing Secret",
            "missing key in ConfigMap or Secret",
            "invalid environment or volume reference",
            "external secret or CSI provider issue",
        ],
        kubernetes_evidence=[
            "pod describe events",
            "pod spec env and volume references",
            "ConfigMap and Secret object existence",
            "service account and projected volume references",
        ],
        linux_evidence=[
            "kubelet logs if projected volume setup is involved",
        ],
        safe_kubectl_commands=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl get configmap,secret -n <namespace>",
            "kubectl get pod <pod> -n <namespace> -o yaml",
        ],
        safe_aop_commands=[
            "aop investigate k8s-linux --incident CreateContainerConfigError",
            "aop linux logs",
        ],
        do_not_assume=[
            "Do not print secret values into incident records.",
            "Do not debug app code before checking missing config references.",
        ],
        escalation_signals=[
            "many workloads fail after config or secret rotation",
            "external secret provider errors appear in events",
        ],
        sources=_sources("Debug Running Pods"),
    ),
    "CreateContainerError": KubernetesIssueKnowledge(
        symptom="CreateContainerError",
        summary=(
            "The runtime failed while creating or starting the container after "
            "Kubernetes accepted the pod spec."
        ),
        common_causes=[
            "container runtime failure",
            "mount or volume setup failure",
            "runtime storage issue",
            "invalid entrypoint behavior during setup",
            "cgroup or permission setup failure",
        ],
        kubernetes_evidence=[
            "pod events",
            "container runtime error text",
            "node where creation failed",
            "volume and mount configuration",
        ],
        linux_evidence=[
            "kubelet and runtime logs",
            "runtime disk usage",
            "cgroup setup evidence",
            "kernel filesystem errors",
        ],
        safe_kubectl_commands=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl get events -n <namespace> --sort-by=.lastTimestamp",
        ],
        safe_aop_commands=[
            "aop investigate k8s-linux --incident CreateContainerError",
            "aop linux logs",
            "aop investigate linux disk --path /var/lib",
        ],
        do_not_assume=[
            "Do not treat runtime creation failure as application crash until events prove it.",
        ],
        escalation_signals=[
            "many pods fail on the same node",
            "runtime or kubelet service has warning logs",
            "runtime storage path is full or read-only",
        ],
        sources=_sources("Debug Running Pods", "Monitoring, Logging, and Debugging"),
    ),
    "FailedScheduling": KubernetesIssueKnowledge(
        symptom="FailedScheduling",
        summary=(
            "The scheduler cannot place the pod on a node because constraints "
            "or available capacity do not match."
        ),
        common_causes=[
            "insufficient CPU or memory",
            "taints without tolerations",
            "node selector or affinity mismatch",
            "volume topology conflict",
            "pod count or quota pressure",
            "cluster autoscaler or cloud quota limit",
        ],
        kubernetes_evidence=[
            "scheduler event reason",
            "pod requests and limits",
            "node taints and labels",
            "affinity and topology constraints",
            "namespace quota",
        ],
        linux_evidence=[
            "actual node CPU, memory, disk, and pressure if scheduler capacity looks stale",
        ],
        safe_kubectl_commands=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl describe node <node>",
            "kubectl get nodes",
            "kubectl get resourcequota -n <namespace>",
        ],
        safe_aop_commands=[
            "aop investigate k8s-linux --incident FailedScheduling",
            "aop linux cpu",
            "aop linux memory",
            "aop investigate linux disk --path /var",
        ],
        do_not_assume=[
            "Do not assume adding nodes fixes taints, affinity, or quota.",
        ],
        escalation_signals=[
            "autoscaler cannot add nodes",
            "cloud quota or subnet capacity blocks scale-out",
            "many pods remain Pending",
        ],
        sources=_sources("Debug Running Pods", "Node Status"),
    ),
    "DiskPressure": KubernetesIssueKnowledge(
        symptom="DiskPressure",
        summary=(
            "The node reports disk pressure, often from filesystem bytes, "
            "inodes, image storage, container logs, or runtime paths."
        ),
        common_causes=[
            "node filesystem full",
            "inode exhaustion",
            "container image or writable-layer growth",
            "deleted-open files",
            "log growth",
            "storage I/O or read-only remount",
        ],
        kubernetes_evidence=[
            "node DiskPressure condition",
            "eviction events",
            "pods evicted from the node",
            "image filesystem and node filesystem signals",
        ],
        linux_evidence=[
            "df bytes and inodes",
            "mount options",
            "kubelet and runtime path usage",
            "deleted-open files",
            "kernel storage errors",
        ],
        safe_kubectl_commands=[
            "kubectl describe node <node>",
            "kubectl get events --all-namespaces --sort-by=.lastTimestamp",
        ],
        safe_aop_commands=[
            "aop investigate k8s-linux --incident DiskPressure",
            "aop investigate linux disk --path /var/lib/kubelet",
            "aop investigate linux disk --path /var/lib",
        ],
        do_not_assume=[
            "Do not delete files before separating bytes, inodes, deleted-open files, and storage errors.",
        ],
        escalation_signals=[
            "evictions are active",
            "runtime storage path is full",
            "kernel logs show I/O or filesystem errors",
        ],
        sources=_sources("Node Status", "Node-pressure Eviction"),
    ),
    "MemoryPressure": KubernetesIssueKnowledge(
        symptom="MemoryPressure",
        summary=(
            "The node reports memory pressure and Kubernetes may evict pods."
        ),
        common_causes=[
            "node overcommit",
            "workload memory leak",
            "system daemon memory growth",
            "swap or reclaim pressure",
            "many pods exceeding working set expectations",
        ],
        kubernetes_evidence=[
            "node MemoryPressure condition",
            "eviction events",
            "pod requests and limits",
            "node and pod memory metrics",
        ],
        linux_evidence=[
            "MemAvailable",
            "swap activity",
            "kernel OOM logs",
            "PSI memory pressure",
            "top RSS processes",
        ],
        safe_kubectl_commands=[
            "kubectl describe node <node>",
            "kubectl top node <node>",
            "kubectl get events --all-namespaces --sort-by=.lastTimestamp",
        ],
        safe_aop_commands=[
            "aop investigate k8s-linux --incident MemoryPressure",
            "aop investigate linux memory",
            "aop linux internals --interval 5",
        ],
        do_not_assume=[
            "Do not blame one pod until node pressure, pod limits, and cgroup evidence are compared.",
        ],
        escalation_signals=[
            "evictions are active",
            "node OOM evidence appears",
            "multiple unrelated pods restart or evict",
        ],
        sources=_sources("Node Status", "Node-pressure Eviction"),
    ),
    "PIDPressure": KubernetesIssueKnowledge(
        symptom="PIDPressure",
        summary=(
            "The node is running low on available process IDs, which can "
            "prevent new processes or containers from starting."
        ),
        common_causes=[
            "process leak",
            "fork storm",
            "too many pods or sidecars",
            "low pids limit",
            "runaway job workload",
        ],
        kubernetes_evidence=[
            "node PIDPressure condition",
            "pod density and restart events",
            "events about process or runtime creation failures",
        ],
        linux_evidence=[
            "process count",
            "cgroup pids.current and pids.max",
            "top process families",
        ],
        safe_kubectl_commands=[
            "kubectl describe node <node>",
            "kubectl get pods --all-namespaces -o wide",
        ],
        safe_aop_commands=[
            "aop linux processes --top 20",
            "aop linux cgroups --pid <pid>",
        ],
        do_not_assume=[
            "Do not kill processes before identifying ownership and blast radius.",
        ],
        escalation_signals=[
            "new containers cannot start",
            "process count keeps rising",
            "runtime logs show fork or PID errors",
        ],
        sources=_sources("Node Status", "Node-pressure Eviction"),
    ),
    "NodeNotReady": KubernetesIssueKnowledge(
        symptom="NodeNotReady",
        summary=(
            "The control plane cannot rely on the node as healthy. The cause "
            "may be kubelet, runtime, network, host pressure, or cloud health."
        ),
        common_causes=[
            "kubelet stopped or unhealthy",
            "container runtime unhealthy",
            "node network failure",
            "disk or memory pressure",
            "CPU starvation",
            "cloud instance or network interface issue",
        ],
        kubernetes_evidence=[
            "node conditions",
            "last heartbeat and transition time",
            "node events",
            "affected pods on the node",
        ],
        linux_evidence=[
            "kubelet service state",
            "container runtime service state",
            "NIC and route evidence",
            "disk, memory, and CPU pressure",
            "kernel errors",
        ],
        safe_kubectl_commands=[
            "kubectl describe node <node>",
            "kubectl get events --all-namespaces --sort-by=.lastTimestamp",
            "kubectl get pods --all-namespaces -o wide",
        ],
        safe_aop_commands=[
            "aop investigate k8s-linux --incident NodeNotReady",
            "aop investigate linux service --service kubelet",
            "aop investigate linux network",
            "aop investigate linux disk --path /var",
        ],
        do_not_assume=[
            "Do not drain, reboot, or replace the node before preserving evidence when possible.",
        ],
        escalation_signals=[
            "many pods impacted on the node",
            "multiple nodes become NotReady",
            "cloud instance health is impaired",
        ],
        sources=_sources("Node Status", "Monitoring, Logging, and Debugging"),
    ),
    "NetworkUnavailable": KubernetesIssueKnowledge(
        symptom="NetworkUnavailable",
        summary=(
            "The node reports that the network is not correctly configured or "
            "available."
        ),
        common_causes=[
            "CNI failure",
            "node route or DNS issue",
            "NIC carrier or packet errors",
            "cloud network interface or security group issue",
            "kube-proxy or network policy problem",
        ],
        kubernetes_evidence=[
            "node NetworkUnavailable condition",
            "CNI pod status and logs",
            "node events",
            "affected services or pods",
        ],
        linux_evidence=[
            "NIC state and errors",
            "routes",
            "DNS resolver",
            "neighbor table",
            "kubelet and CNI logs",
        ],
        safe_kubectl_commands=[
            "kubectl describe node <node>",
            "kubectl get pods -n kube-system -o wide",
            "kubectl get events --all-namespaces --sort-by=.lastTimestamp",
        ],
        safe_aop_commands=[
            "aop investigate k8s-linux --incident NodeNotReady",
            "aop investigate linux network",
            "aop linux nic",
        ],
        do_not_assume=[
            "Do not blame the application before checking node and CNI network state.",
        ],
        escalation_signals=[
            "many pods lose service connectivity",
            "CNI pods fail on multiple nodes",
            "cloud network interface reports impairment",
        ],
        sources=_sources("Node Status", "Monitoring, Logging, and Debugging"),
    ),
}


ALIASES = {
    "crashloop": "CrashLoopBackOff",
    "imagepull": "ImagePullBackOff",
    "imagepullfailure": "ImagePullBackOff",
    "errimagepull": "ErrImagePull",
    "oom": "OOMKilled",
    "memoryexhaustion": "OOMKilled",
    "configerror": "CreateContainerConfigError",
    "containerconfig": "CreateContainerConfigError",
    "containerstartup": "CreateContainerError",
    "schedulingfailure": "FailedScheduling",
    "disk": "DiskPressure",
    "memory": "MemoryPressure",
    "pid": "PIDPressure",
    "notready": "NodeNotReady",
    "node-not-ready": "NodeNotReady",
    "network": "NetworkUnavailable",
}


def list_kubernetes_issue_symptoms() -> list[str]:
    return sorted(KUBERNETES_ISSUE_KNOWLEDGE)


def normalize_symptom(symptom: str) -> str:
    key = symptom.strip()
    if key in KUBERNETES_ISSUE_KNOWLEDGE:
        return key

    alias_key = key.lower().replace("_", "-").replace(" ", "-")
    compact_key = key.lower().replace("_", "").replace("-", "").replace(" ", "")

    if alias_key in ALIASES:
        return ALIASES[alias_key]
    if compact_key in ALIASES:
        return ALIASES[compact_key]

    for known in KUBERNETES_ISSUE_KNOWLEDGE:
        if known.lower() == key.lower():
            return known

    supported = ", ".join(list_kubernetes_issue_symptoms())
    raise ValueError(
        f"Unsupported Kubernetes symptom '{symptom}'. Supported: {supported}"
    )


def get_kubernetes_issue_knowledge(
    symptom: str,
) -> KubernetesIssueKnowledge:
    return KUBERNETES_ISSUE_KNOWLEDGE[normalize_symptom(symptom)]
