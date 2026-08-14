from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


CommandDomain = Literal["linux", "kubernetes"]
CommandRisk = Literal["safe", "elevated", "careful"]


@dataclass(frozen=True)
class TroubleshootingCommand:
    """
    Structured troubleshooting command metadata.

    The catalog is intentionally metadata-first. Commands listed here are not
    automatically executed. Collectors and CLI commands decide which evidence
    to gather and keep execution bounded, read-only, and context-aware.
    """

    key: str
    domain: CommandDomain
    category: str
    command: str
    description: str
    risk: CommandRisk = "safe"
    requires_root: bool = False
    agent_hint: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


LINUX_TROUBLESHOOTING_COMMANDS: tuple[TroubleshootingCommand, ...] = (
    TroubleshootingCommand(
        key="linux_cpu_load",
        domain="linux",
        category="cpu",
        command="uptime",
        description="Show host uptime and 1/5/15 minute load averages.",
        agent_hint="Use when checking whether load is high relative to CPU count.",
    ),
    TroubleshootingCommand(
        key="linux_cpu_topology",
        domain="linux",
        category="cpu",
        command="lscpu",
        description="Show CPU architecture, socket, core, and thread topology.",
    ),
    TroubleshootingCommand(
        key="linux_cpu_runqueue",
        domain="linux",
        category="cpu",
        command="vmstat 1 3",
        description="Sample run queue, context switching, CPU wait, and system activity.",
        agent_hint="Use to separate CPU saturation from IO wait or memory pressure.",
    ),
    TroubleshootingCommand(
        key="linux_cpu_per_core",
        domain="linux",
        category="cpu",
        command="mpstat -P ALL 1 3",
        description="Sample per-CPU utilization and imbalance.",
    ),
    TroubleshootingCommand(
        key="linux_memory_overview",
        domain="linux",
        category="memory",
        command="free -h",
        description="Show memory and swap usage in human-readable form.",
    ),
    TroubleshootingCommand(
        key="linux_memory_kernel_counters",
        domain="linux",
        category="memory",
        command="cat /proc/meminfo",
        description="Show detailed kernel memory counters.",
    ),
    TroubleshootingCommand(
        key="linux_memory_pressure",
        domain="linux",
        category="memory",
        command="cat /proc/pressure/memory",
        description="Show memory pressure stall information when PSI is enabled.",
        agent_hint="Use for latency incidents where memory reclaim may be stalling workloads.",
    ),
    TroubleshootingCommand(
        key="linux_disk_capacity",
        domain="linux",
        category="disk",
        command="df -hT",
        description="Show filesystem capacity, usage, and filesystem type.",
    ),
    TroubleshootingCommand(
        key="linux_disk_inodes",
        domain="linux",
        category="disk",
        command="df -i",
        description="Show inode usage by filesystem.",
        agent_hint="Use when disk appears available but file creation fails.",
    ),
    TroubleshootingCommand(
        key="linux_disk_mounts",
        domain="linux",
        category="disk",
        command="findmnt -r",
        description="Show mounted filesystems and mount relationships.",
    ),
    TroubleshootingCommand(
        key="linux_disk_largest_dirs",
        domain="linux",
        category="disk",
        command="du -x -h --max-depth=1 /",
        description="Show largest top-level directories on the current filesystem only.",
        risk="careful",
        agent_hint="Keep scan path bounded; avoid unbounded recursive scans on production hosts.",
    ),
    TroubleshootingCommand(
        key="linux_disk_deleted_open_files",
        domain="linux",
        category="disk",
        command="lsof +L1",
        description="Find deleted files still held open by running processes.",
        risk="elevated",
        requires_root=True,
        agent_hint="Useful when df shows space used but du cannot find matching files.",
    ),
    TroubleshootingCommand(
        key="linux_disk_io_latency",
        domain="linux",
        category="disk",
        command="iostat -xz 1 5",
        description="Sample extended block-device utilization and latency.",
    ),
    TroubleshootingCommand(
        key="linux_network_sockets_summary",
        domain="linux",
        category="network",
        command="ss -s",
        description="Show socket summary by protocol and state.",
    ),
    TroubleshootingCommand(
        key="linux_network_listeners",
        domain="linux",
        category="network",
        command="ss -tulnp",
        description="Show listening TCP and UDP sockets with owning processes when available.",
    ),
    TroubleshootingCommand(
        key="linux_network_conntrack_count",
        domain="linux",
        category="network",
        command="sysctl net.netfilter.nf_conntrack_count net.netfilter.nf_conntrack_max",
        description="Show conntrack table usage and configured maximum.",
        agent_hint="Use for intermittent Kubernetes networking failures and DNS timeouts.",
    ),
    TroubleshootingCommand(
        key="linux_kernel_recent_errors",
        domain="linux",
        category="kernel",
        command="journalctl -k -p warning -n 100 --no-pager",
        description="Show recent kernel warnings and errors.",
    ),
    TroubleshootingCommand(
        key="linux_process_top_cpu",
        domain="linux",
        category="process",
        command="ps -eo pid,ppid,user,state,etimes,%cpu,%mem,comm,args --sort=-%cpu",
        description="Show processes sorted by CPU consumption.",
    ),
    TroubleshootingCommand(
        key="linux_process_tree",
        domain="linux",
        category="process",
        command="pstree -ap",
        description="Show process hierarchy with PIDs and arguments.",
    ),
)


KUBERNETES_TROUBLESHOOTING_COMMANDS: tuple[TroubleshootingCommand, ...] = (
    TroubleshootingCommand(
        key="k8s_cluster_info",
        domain="kubernetes",
        category="cluster",
        command="kubectl cluster-info",
        description="Show Kubernetes control-plane endpoint information.",
    ),
    TroubleshootingCommand(
        key="k8s_nodes",
        domain="kubernetes",
        category="node",
        command="kubectl get nodes -o wide",
        description="List nodes with readiness, roles, versions, and addresses.",
    ),
    TroubleshootingCommand(
        key="k8s_node_describe",
        domain="kubernetes",
        category="node",
        command="kubectl describe node <node>",
        description="Show node conditions, pressure, allocatable resources, and events.",
        agent_hint="Use for scheduling failures, DiskPressure, MemoryPressure, and NodeNotReady.",
    ),
    TroubleshootingCommand(
        key="k8s_top_nodes",
        domain="kubernetes",
        category="node",
        command="kubectl top node",
        description="Show node CPU and memory usage from metrics-server.",
    ),
    TroubleshootingCommand(
        key="k8s_pods_all",
        domain="kubernetes",
        category="pod",
        command="kubectl get pods -A -o wide",
        description="List pods across namespaces with status, restarts, IPs, and nodes.",
    ),
    TroubleshootingCommand(
        key="k8s_pod_describe",
        domain="kubernetes",
        category="pod",
        command="kubectl describe pod <pod> -n <namespace>",
        description="Show pod conditions, container states, resources, volumes, and events.",
    ),
    TroubleshootingCommand(
        key="k8s_pod_logs",
        domain="kubernetes",
        category="pod",
        command="kubectl logs <pod> -n <namespace> --tail=100",
        description="Read bounded current container logs.",
    ),
    TroubleshootingCommand(
        key="k8s_pod_previous_logs",
        domain="kubernetes",
        category="pod",
        command="kubectl logs <pod> -n <namespace> --previous --tail=100",
        description="Read bounded previous container logs after a restart.",
        agent_hint="Use for CrashLoopBackOff, OOMKilled, and exit-code analysis.",
    ),
    TroubleshootingCommand(
        key="k8s_events_warnings",
        domain="kubernetes",
        category="event",
        command="kubectl get events -A --field-selector type=Warning --sort-by=.lastTimestamp",
        description="Show warning events across namespaces ordered by timestamp.",
    ),
    TroubleshootingCommand(
        key="k8s_deployments",
        domain="kubernetes",
        category="workload",
        command="kubectl get deployments -A",
        description="Show deployment readiness and replica state across namespaces.",
    ),
    TroubleshootingCommand(
        key="k8s_rollout_status",
        domain="kubernetes",
        category="workload",
        command="kubectl rollout status deployment/<deployment> -n <namespace>",
        description="Show deployment rollout progress.",
    ),
    TroubleshootingCommand(
        key="k8s_replicasets",
        domain="kubernetes",
        category="workload",
        command="kubectl get rs -A",
        description="Show ReplicaSets and desired/current/ready replica counts.",
    ),
    TroubleshootingCommand(
        key="k8s_services",
        domain="kubernetes",
        category="network",
        command="kubectl get svc -A -o wide",
        description="Show services, types, cluster IPs, external IPs, and ports.",
    ),
    TroubleshootingCommand(
        key="k8s_endpoints",
        domain="kubernetes",
        category="network",
        command="kubectl get endpoints -A",
        description="Show service endpoint population.",
        agent_hint="Use when Service exists but traffic has no backend endpoints.",
    ),
    TroubleshootingCommand(
        key="k8s_ingress",
        domain="kubernetes",
        category="network",
        command="kubectl get ingress -A",
        description="Show ingress resources and assigned addresses.",
    ),
    TroubleshootingCommand(
        key="k8s_network_policies",
        domain="kubernetes",
        category="network",
        command="kubectl get networkpolicy -A",
        description="Show network policies that may restrict pod-to-pod traffic.",
    ),
    TroubleshootingCommand(
        key="k8s_pvc",
        domain="kubernetes",
        category="storage",
        command="kubectl get pvc -A",
        description="Show persistent volume claims and binding status.",
    ),
    TroubleshootingCommand(
        key="k8s_pv",
        domain="kubernetes",
        category="storage",
        command="kubectl get pv",
        description="Show persistent volumes and lifecycle state.",
    ),
    TroubleshootingCommand(
        key="k8s_storageclass",
        domain="kubernetes",
        category="storage",
        command="kubectl get storageclass",
        description="Show available storage classes and default class.",
    ),
    TroubleshootingCommand(
        key="k8s_pdb",
        domain="kubernetes",
        category="availability",
        command="kubectl get pdb -A",
        description="Show PodDisruptionBudgets and allowed disruptions.",
    ),
    TroubleshootingCommand(
        key="k8s_resource_quota",
        domain="kubernetes",
        category="governance",
        command="kubectl get resourcequota -A",
        description="Show namespace resource quotas.",
    ),
    TroubleshootingCommand(
        key="k8s_limit_range",
        domain="kubernetes",
        category="governance",
        command="kubectl get limitrange -A",
        description="Show namespace default and maximum resource constraints.",
    ),
)


ALL_TROUBLESHOOTING_COMMANDS: tuple[TroubleshootingCommand, ...] = (
    *LINUX_TROUBLESHOOTING_COMMANDS,
    *KUBERNETES_TROUBLESHOOTING_COMMANDS,
)


def list_commands(
    domain: CommandDomain | None = None,
    category: str | None = None,
) -> list[dict]:
    """
    Return command metadata filtered by domain and optional category.
    """

    results = []
    for command in ALL_TROUBLESHOOTING_COMMANDS:
        if domain is not None and command.domain != domain:
            continue
        if category is not None and command.category != category:
            continue
        results.append(command.to_dict())
    return results


def list_categories(domain: CommandDomain | None = None) -> list[str]:
    """
    Return sorted troubleshooting categories for the selected domain.
    """

    return sorted(
        {
            command.category
            for command in ALL_TROUBLESHOOTING_COMMANDS
            if domain is None or command.domain == domain
        }
    )


def get_command(key: str) -> TroubleshootingCommand:
    """
    Return a troubleshooting command by stable key.
    """

    for command in ALL_TROUBLESHOOTING_COMMANDS:
        if command.key == key:
            return command

    raise KeyError(f"unknown troubleshooting command: {key}")


def search_commands(query: str) -> list[dict]:
    """
    Search command metadata by key, category, command text, and guidance.
    """

    needle = query.lower()
    results = []
    for command in ALL_TROUBLESHOOTING_COMMANDS:
        haystack = " ".join(
            (
                command.key,
                command.domain,
                command.category,
                command.command,
                command.description,
                command.agent_hint,
            )
        ).lower()
        if needle in haystack:
            results.append(command.to_dict())
    return results
