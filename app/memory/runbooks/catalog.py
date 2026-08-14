from __future__ import annotations

from app.schemas.memory import RunbookChunk


RUNBOOK_CHUNKS: tuple[RunbookChunk, ...] = (
    RunbookChunk(
        runbook_id="k8s-oom-linux-memory",
        chunk_id="k8s-oom-linux-memory-001",
        title="Kubernetes OOMKilled With Linux Memory Correlation",
        domain="kubernetes",
        incident_types=["MemoryExhaustion", "OOMKilled"],
        keywords=[
            "oom",
            "oomkilled",
            "memory",
            "limit",
            "rss",
            "cgroup",
            "kernel",
            "restart",
        ],
        summary=(
            "Separate container limit exhaustion from node-wide memory pressure "
            "before declaring root cause."
        ),
        guidance=[
            "Check pod last termination reason, exit code 137, restart count, and memory limits.",
            "Correlate with node MemoryPressure and Linux OOM/kern logs before blaming the app.",
            "If cgroup memory events increase, treat the container limit as stronger evidence.",
            "If host PSI, swap, or kernel OOM is active, escalate to node-level memory investigation.",
        ],
        commands=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl logs <pod> -n <namespace> --previous --tail=100",
            "aop investigate linux memory --pid <container-pid>",
        ],
        source="app/memory/runbooks/catalog.py",
    ),
    RunbookChunk(
        runbook_id="k8s-imagepull-network-dns",
        chunk_id="k8s-imagepull-network-dns-001",
        title="ImagePullBackOff With Registry, DNS, And Node Network Checks",
        domain="kubernetes",
        incident_types=["ImagePullBackOff"],
        keywords=[
            "imagepullbackoff",
            "errimagepull",
            "registry",
            "dns",
            "pull",
            "secret",
            "network",
        ],
        summary=(
            "Image pulls fail because of image names, credentials, registry "
            "availability, DNS, routes, proxy, or node runtime issues."
        ),
        guidance=[
            "Read warning events before testing random network paths.",
            "Separate authentication errors from DNS, timeout, and TLS failures.",
            "Correlate registry failures with node DNS and container runtime evidence.",
            "Do not delete pods as a fix until the pull failure class is known.",
        ],
        commands=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl get events -n <namespace> --sort-by=.lastTimestamp",
            "aop investigate linux network",
            "aop investigate linux runtime",
        ],
        source="app/memory/runbooks/catalog.py",
    ),
    RunbookChunk(
        runbook_id="k8s-node-diskpressure-linux-storage",
        chunk_id="k8s-node-diskpressure-linux-storage-001",
        title="Kubernetes DiskPressure To Linux Storage Investigation",
        domain="kubernetes",
        incident_types=["DiskPressure", "FailedScheduling"],
        keywords=[
            "diskpressure",
            "eviction",
            "ephemeral",
            "imagegc",
            "kubelet",
            "containerd",
            "inode",
            "filesystem",
        ],
        summary=(
            "DiskPressure needs Linux filesystem, inode, kubelet, runtime, and "
            "deleted-open-file evidence before cleanup advice."
        ),
        guidance=[
            "Check node conditions and kubelet events first.",
            "Map pressure to filesystem capacity, inode usage, runtime paths, and open deleted files.",
            "Treat read-only remounts and I/O errors as storage risk, not cleanup tasks.",
            "Avoid deleting runtime content manually without runtime-aware evidence.",
        ],
        commands=[
            "kubectl describe node <node>",
            "aop investigate linux disk --path /var/lib/kubelet",
            "aop investigate linux disk --path /var/lib/containerd",
        ],
        source="app/memory/runbooks/catalog.py",
    ),
    RunbookChunk(
        runbook_id="linux-disk-df-du-deleted-open",
        chunk_id="linux-disk-df-du-deleted-open-001",
        title="Linux Disk Full With df/du Mismatch",
        domain="linux.disk",
        incident_types=["DiskPressure", "DiskFull", "FilesystemFull"],
        keywords=[
            "disk",
            "df",
            "du",
            "deleted",
            "open",
            "inode",
            "lsof",
            "filesystem",
        ],
        summary=(
            "When df shows space used but du cannot find it, deleted files held "
            "open by processes or mount boundaries are common causes."
        ),
        guidance=[
            "Start with df -hT and df -i to separate block usage from inode exhaustion.",
            "Use du with -x to stay inside one filesystem.",
            "Check lsof +L1 for deleted files still held open.",
            "Restarting a process can release space, but confirm owner and impact first.",
        ],
        commands=[
            "df -hT",
            "df -i",
            "du -x -h --max-depth=1 /var",
            "lsof +L1",
        ],
        source="app/memory/runbooks/catalog.py",
    ),
    RunbookChunk(
        runbook_id="linux-cgroup-memory-pressure",
        chunk_id="linux-cgroup-memory-pressure-001",
        title="Linux Cgroup Memory Pressure And Container Limits",
        domain="linux.memory",
        incident_types=["MemoryPressure", "OOMKilled", "MemoryExhaustion"],
        keywords=[
            "cgroup",
            "memory.current",
            "memory.max",
            "memory.events",
            "psi",
            "oom",
            "container",
        ],
        summary=(
            "Cgroup counters explain whether pressure is host-wide or limited "
            "to a workload boundary."
        ),
        guidance=[
            "Detect cgroup v1, v2, or hybrid before applying cgroup v2 assumptions.",
            "Compare memory.current with memory.max for the workload cgroup.",
            "Use memory.events for oom, oom_kill, high, and max counters.",
            "Use PSI to understand stall impact; do not rely on free memory alone.",
        ],
        commands=[
            "cat /proc/cgroups",
            "findmnt -t cgroup2",
            "cat /proc/pressure/memory",
            "cat <cgroup>/memory.events",
        ],
        source="app/memory/runbooks/catalog.py",
    ),
)


def list_runbook_chunks(
    domain: str | None = None,
    incident_type: str | None = None,
) -> list[RunbookChunk]:
    """
    List source-controlled runbook chunks with optional filters.
    """

    results = []
    incident = incident_type.lower() if incident_type else None
    for chunk in RUNBOOK_CHUNKS:
        if domain is not None and chunk.domain != domain:
            continue
        if incident is not None and incident not in {
            value.lower() for value in chunk.incident_types
        }:
            continue
        results.append(chunk)
    return results
