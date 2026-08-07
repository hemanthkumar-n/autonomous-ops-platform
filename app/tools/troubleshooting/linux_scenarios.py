from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class LinuxScenario:
    """
    Senior Linux troubleshooting scenario preserved as read-only guidance.
    """

    key: str
    title: str
    summary: str
    symptoms: tuple[str, ...]
    likely_causes: tuple[str, ...]
    first_safe_checks: tuple[str, ...]
    interpretation: tuple[str, ...]
    common_traps: tuple[str, ...]
    kubernetes_correlation: tuple[str, ...] = ()
    aws_correlation: tuple[str, ...] = ()
    cgroup_context: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)


LINUX_COMPLEX_SCENARIOS: tuple[LinuxScenario, ...] = (
    LinuxScenario(
        key="high-load",
        title="High Load With Low CPU Usage",
        summary=(
            "Load average is high, but CPU utilization does not explain the "
            "pressure. Start by separating runnable work from blocked kernel "
            "waits."
        ),
        symptoms=(
            "Load average is higher than logical CPU count.",
            "top shows idle CPU or low user/system CPU.",
            "Applications are slow even though CPU is not saturated.",
        ),
        likely_causes=(
            "Uninterruptible I/O wait in D state.",
            "Slow disk, NFS, block device, or storage backend.",
            "Kernel lock contention or blocked filesystem operations.",
            "Container or cgroup throttling hiding true workload pressure.",
        ),
        first_safe_checks=(
            "uptime",
            "top -c",
            "ps -eo state,pid,ppid,comm,wchan:32,cmd | awk '$1 ~ /D/ {print}'",
            "vmstat 1 5",
            "iostat -xz 1 5",
            "cat /proc/pressure/io",
            "journalctl -k --since '1 hour ago' --no-pager",
        ),
        interpretation=(
            "High load with many D-state tasks points away from CPU and "
            "toward blocked kernel operations.",
            "High iowait, device await, or PSI I/O stall means the service is "
            "waiting below the process layer.",
            "A blocked wchan helps identify whether the wait is filesystem, "
            "network storage, block I/O, or locking related.",
        ),
        common_traps=(
            "Treating load average as CPU percentage.",
            "Restarting the app before checking whether the kernel is blocking "
            "its threads.",
            "Ignoring storage errors because df still has free space.",
        ),
        kubernetes_correlation=(
            "Correlate with node pressure, kubelet logs, pod restarts, and "
            "container runtime storage paths.",
            "Check whether only pods on one node are slow; that usually means "
            "node-level Linux evidence matters.",
        ),
        aws_correlation=(
            "Correlate with EBS latency, queue length, throughput, IOPS, "
            "burst balance, and instance EBS bandwidth limits.",
        ),
        cgroup_context=(
            "If the process is inside a container, inspect cgroup CPU, memory, "
            "I/O, and PSI counters before blaming host-wide CPU.",
        ),
    ),
    LinuxScenario(
        key="memory-pressure",
        title="Memory Pressure And OOM Evidence",
        summary=(
            "Memory incidents need allocator, reclaim, swap, and OOM evidence "
            "before blaming one process."
        ),
        symptoms=(
            "Application latency rises before restarts.",
            "OOMKilled pods or killed Linux processes appear.",
            "Swap activity, direct reclaim, or PSI memory stall increases.",
        ),
        likely_causes=(
            "Process memory growth or leak.",
            "Page cache pressure combined with application allocation spikes.",
            "Cgroup memory.max or memory.high pressure.",
            "Kernel OOM killer terminating the largest eligible process.",
        ),
        first_safe_checks=(
            "free -h",
            "vmstat 1 5",
            "cat /proc/pressure/memory",
            "grep -E 'oom|kill|out of memory' /var/log/messages /var/log/syslog 2>/dev/null",
            "journalctl -k -g 'Out of memory|Killed process|oom' --no-pager",
            "ps aux --sort=-%mem | head -20",
        ),
        interpretation=(
            "Low available memory plus swap-in/swap-out activity means active "
            "memory pressure.",
            "OOM logs identify victim process, allocation context, and whether "
            "a cgroup limit was involved.",
            "PSI memory stall shows how much time workloads lost to memory "
            "contention.",
        ),
        common_traps=(
            "Calling cached memory 'used memory' without checking available.",
            "Only checking the current process list after the OOM victim has "
            "already been killed.",
            "Missing cgroup-level OOM events in Kubernetes containers.",
        ),
        kubernetes_correlation=(
            "Compare node memory pressure, pod OOMKilled events, requests, "
            "limits, and container restart timing.",
        ),
        cgroup_context=(
            "Read memory.current, memory.high, memory.max, memory.events, and "
            "memory PSI for the target cgroup.",
        ),
    ),
    LinuxScenario(
        key="df-du-mismatch",
        title="df And du Mismatch",
        summary=(
            "df reports filesystem allocation, while du walks visible files. "
            "A mismatch usually means deleted-open files, hidden mount data, "
            "or reserved filesystem blocks."
        ),
        symptoms=(
            "df shows the filesystem is full.",
            "du cannot find enough visible data under the mount.",
            "Space does not return after deleting files.",
        ),
        likely_causes=(
            "Deleted files still held open by a process.",
            "Data hidden under an active mount point.",
            "Reserved blocks or filesystem metadata.",
            "Container overlay or runtime layer accounting.",
        ),
        first_safe_checks=(
            "df -hT /path",
            "du -x -h --max-depth=1 /path | sort -h",
            "lsof +L1 /path",
            "findmnt -R /path",
            "mount | grep ' /path '",
        ),
        interpretation=(
            "Deleted-open files keep blocks allocated until the owning process "
            "closes the file descriptor.",
            "A mount over a non-empty directory can hide older data from du.",
            "Use filesystem and mount evidence before deleting more files.",
        ),
        common_traps=(
            "Deleting more files without checking lsof +L1.",
            "Restarting the wrong service and losing useful evidence.",
            "Scanning across filesystems without -xdev or du -x.",
        ),
        kubernetes_correlation=(
            "Pod logs and container runtime layers can hold deleted-open files "
            "on the node even after Kubernetes objects change.",
        ),
    ),
    LinuxScenario(
        key="inode-exhaustion",
        title="Inode Exhaustion",
        summary=(
            "A filesystem can return no-space errors even when byte capacity "
            "looks healthy if it runs out of inode entries."
        ),
        symptoms=(
            "Application gets 'No space left on device'.",
            "df -h shows free bytes.",
            "df -i shows IUse% near 100%.",
        ),
        likely_causes=(
            "Too many small files.",
            "Exploded cache, mail queue, session files, or temporary files.",
            "Container runtime metadata or pod log churn.",
        ),
        first_safe_checks=(
            "df -i /path",
            "find /path -xdev -type f | sed 's#/[^/]*$##' | sort | uniq -c | sort -n | tail",
            "find /path -xdev -type f -mtime -1 | wc -l",
        ),
        interpretation=(
            "High inode use means cleanup must target file count, not file "
            "size.",
            "Directory counts reveal where small-file growth is concentrated.",
        ),
        common_traps=(
            "Looking only at df -h.",
            "Deleting a few large files when the incident is small-file count.",
        ),
        kubernetes_correlation=(
            "Many small pod files or runtime metadata can create inode "
            "pressure and trigger node DiskPressure.",
        ),
    ),
    LinuxScenario(
        key="read-only-filesystem",
        title="Read-Only Filesystem Remount",
        summary=(
            "A sudden read-only filesystem is usually a storage or filesystem "
            "health incident, not a normal cleanup incident."
        ),
        symptoms=(
            "Writes fail with read-only filesystem errors.",
            "Services fail to create lock, pid, spool, or log files.",
            "Mount options show ro.",
        ),
        likely_causes=(
            "Filesystem detected corruption or serious I/O errors.",
            "Underlying block device, multipath, or controller failure.",
            "Cloud volume or network storage disruption.",
        ),
        first_safe_checks=(
            "findmnt -no SOURCE,FSTYPE,OPTIONS,TARGET /path",
            "mount | grep ' ro,'",
            "journalctl -k -g 'read-only|EXT4-fs|XFS|I/O error|Buffer I/O' --no-pager",
            "lsblk -f",
        ),
        interpretation=(
            "Kernel logs decide whether this is filesystem protection after "
            "errors.",
            "Filesystem repair usually requires a maintenance window, backup "
            "awareness, and often an unmounted filesystem.",
        ),
        common_traps=(
            "Trying chmod or chown for a read-only mount.",
            "Running repair commands on mounted production filesystems.",
        ),
        aws_correlation=(
            "On EC2, verify EBS health, attachment state, impaired volumes, "
            "and instance storage events.",
        ),
    ),
    LinuxScenario(
        key="file-descriptor-exhaustion",
        title="File Descriptor Exhaustion",
        summary=(
            "FD exhaustion breaks accepts, opens, logs, sockets, and pipes. "
            "Find whether pressure is per-process or system-wide."
        ),
        symptoms=(
            "Too many open files errors.",
            "Service accepts fail or logs stop writing.",
            "Process count looks normal but descriptors are high.",
        ),
        likely_causes=(
            "Application FD leak.",
            "Connection storm.",
            "Low systemd LimitNOFILE or shell ulimit.",
            "System-wide file table pressure.",
        ),
        first_safe_checks=(
            "cat /proc/sys/fs/file-nr",
            "ulimit -n",
            "systemctl show SERVICE -p LimitNOFILE",
            "lsof -p PID | wc -l",
            "ls /proc/PID/fd | wc -l",
            "ss -tanp | head",
        ),
        interpretation=(
            "Per-process limits differ from system-wide file table capacity.",
            "A growing fd count over time points to a leak or unclosed "
            "connections.",
        ),
        common_traps=(
            "Changing shell ulimit but forgetting systemd service limits.",
            "Only increasing limits without finding the leak pattern.",
        ),
        kubernetes_correlation=(
            "Container limits and entrypoint shells may differ from host "
            "limits; inspect the running process context.",
        ),
    ),
    LinuxScenario(
        key="port-conflict",
        title="Port Conflict Or Missing Listener",
        summary=(
            "When a service cannot bind or clients cannot connect, prove "
            "whether the listener, route, firewall, and process ownership "
            "match expectations."
        ),
        symptoms=(
            "Address already in use during startup.",
            "Connection refused or timeout.",
            "Expected process is not visible on the port.",
        ),
        likely_causes=(
            "Another process already owns the port.",
            "Service bound to localhost or the wrong interface.",
            "Firewall, route, or security group blocking traffic.",
            "IPv4/IPv6 bind mismatch.",
        ),
        first_safe_checks=(
            "ss -ltnp",
            "netstat -plane | grep :3045",
            "lsof -i :3045",
            "ip addr",
            "ip route",
            "systemctl status SERVICE --no-pager",
        ),
        interpretation=(
            "LISTEN confirms bind address, port, protocol, and owning PID.",
            "Connection refused usually means no listener; timeout usually "
            "means path, firewall, or packet filtering.",
        ),
        common_traps=(
            "Checking only localhost when clients connect through another "
            "interface.",
            "Ignoring IPv6 listeners.",
            "Using netstat on modern systems without knowing ss is preferred.",
        ),
        kubernetes_correlation=(
            "Map containerPort, targetPort, service port, nodePort, endpoint "
            "readiness, and hostNetwork usage.",
        ),
        aws_correlation=(
            "Check security groups, NACLs, route tables, load balancer target "
            "health, and listener rules.",
        ),
    ),
    LinuxScenario(
        key="systemd-restart-loop",
        title="systemd Restart Loop",
        summary=(
            "A restart loop is usually a symptom. Preserve exit status, "
            "journal context, environment, limits, and dependency evidence."
        ),
        symptoms=(
            "Service repeatedly starts and exits.",
            "systemctl shows activating, failed, or start-limit-hit.",
            "Application has short uptime.",
        ),
        likely_causes=(
            "Bad config, missing file, permission issue, or failed dependency.",
            "Resource limit or environment mismatch under systemd.",
            "Application crash hidden by automatic restart.",
        ),
        first_safe_checks=(
            "systemctl status SERVICE --no-pager",
            "journalctl -u SERVICE --since '1 hour ago' --no-pager",
            "systemctl show SERVICE -p ExecMainStatus -p ExecMainCode -p Restart -p RestartUSec -p LimitNOFILE",
            "systemctl cat SERVICE",
        ),
        interpretation=(
            "Exit code and recent journal lines identify whether systemd or "
            "the application rejected startup.",
            "Unit files reveal environment, working directory, limits, and "
            "dependency ordering.",
        ),
        common_traps=(
            "Only reading application logs while systemd has the real failure.",
            "Running the command manually as root and missing service-user "
            "permissions.",
        ),
        kubernetes_correlation=(
            "The equivalent Kubernetes pattern is CrashLoopBackOff; preserve "
            "previous logs and termination state.",
        ),
    ),
    LinuxScenario(
        key="kernel-panic",
        title="Kernel Panic Or Previous Boot Crash",
        summary=(
            "After an unexpected reboot, separate hardware, kernel, driver, "
            "OOM, storage, and power events using previous-boot evidence."
        ),
        symptoms=(
            "Host rebooted unexpectedly.",
            "Application outage started at boot time.",
            "No normal shutdown marker is present.",
        ),
        likely_causes=(
            "Kernel panic or watchdog.",
            "OOM-triggered instability.",
            "Storage path failure.",
            "Hypervisor or cloud maintenance event.",
            "Power or hardware issue.",
        ),
        first_safe_checks=(
            "last -x | head -20",
            "journalctl -b -1 -p warning --no-pager",
            "journalctl -b -1 -k --no-pager",
            "dmesg -T | tail -100",
            "ls -lh /var/crash /var/lib/systemd/coredump 2>/dev/null",
        ),
        interpretation=(
            "Previous-boot kernel logs are more valuable than current dmesg "
            "after a reboot.",
            "A clean shutdown trail differs from panic, watchdog, or forced "
            "hypervisor reset evidence.",
        ),
        common_traps=(
            "Only checking current boot logs.",
            "Assuming every reboot is an application crash.",
            "Missing kdump, vmcore, or systemd coredump artifacts.",
        ),
        aws_correlation=(
            "Check EC2 status checks, scheduled events, instance retirement, "
            "underlying host events, and CloudTrail stop/reboot actions.",
        ),
    ),
    LinuxScenario(
        key="lvm-expansion-mismatch",
        title="LVM, Partition, And Filesystem Expansion Mismatch",
        summary=(
            "Storage expansion has layers. Cloud volume, disk, partition, PV, "
            "LV, and filesystem must all reflect the intended size."
        ),
        symptoms=(
            "Cloud console shows larger disk but df still shows old size.",
            "lsblk shows size mismatch across disk, partition, LV, and mount.",
            "Application remains out of space after volume expansion.",
        ),
        likely_causes=(
            "Partition not grown after disk expansion.",
            "PV not resized.",
            "LV not extended.",
            "Filesystem not grown.",
            "Wrong mount or wrong volume expanded.",
        ),
        first_safe_checks=(
            "lsblk -f",
            "findmnt -no SOURCE,FSTYPE,SIZE,USED,AVAIL,TARGET /path",
            "df -hT /path",
            "sudo fdisk -l",
            "pvs",
            "vgs",
            "lvs -a -o +devices",
        ),
        interpretation=(
            "The smallest layer in the chain explains where expansion stopped.",
            "XFS and ext filesystems use different grow procedures.",
            "Do not run destructive partition or filesystem commands without "
            "backup and change approval.",
        ),
        common_traps=(
            "Expanding only the cloud volume and expecting df to change.",
            "Growing the wrong filesystem.",
            "Confusing fdisk inspection with partition modification.",
        ),
        aws_correlation=(
            "For EBS, confirm ModifyVolume completed, then verify OS disk "
            "size, partition, LVM, and filesystem layers.",
        ),
    ),
    LinuxScenario(
        key="container-runtime-disk-pressure",
        title="Container Runtime Disk Pressure",
        summary=(
            "Kubernetes DiskPressure often begins as normal Linux disk, inode, "
            "overlay, image, or log pressure on the node."
        ),
        symptoms=(
            "Node shows DiskPressure.",
            "Pods are evicted.",
            "Image pulls fail or kubelet garbage collection struggles.",
            "Filesystem usage is high under kubelet or container runtime paths.",
        ),
        likely_causes=(
            "Large container logs.",
            "Unused images or snapshots.",
            "Overlay layer growth.",
            "Orphaned pod directories.",
            "Ephemeral-storage requests and limits not aligned with workload.",
        ),
        first_safe_checks=(
            "df -hT /var/lib/kubelet /var/lib/containerd",
            "df -i /var/lib/kubelet /var/lib/containerd",
            "du -x -h --max-depth=1 /var/lib/containerd | sort -h",
            "du -x -h --max-depth=1 /var/lib/kubelet | sort -h",
            "journalctl -u kubelet --since '1 hour ago' --no-pager",
            "crictl images",
            "crictl ps -a",
        ),
        interpretation=(
            "Separate filesystem pressure from kubelet eviction policy and "
            "runtime garbage collection behavior.",
            "Large pod logs require application and log-rotation context, not "
            "blind deletion.",
        ),
        common_traps=(
            "Deleting runtime directories manually without kubelet/runtime "
            "awareness.",
            "Only checking pod status and missing node filesystem pressure.",
        ),
        kubernetes_correlation=(
            "Correlate node conditions, events, kubelet logs, pod ephemeral "
            "storage, and runtime garbage collection.",
        ),
        cgroup_context=(
            "Use cgroup data when pressure is workload-specific rather than "
            "whole-node.",
        ),
    ),
)


SCENARIO_ALIASES = {
    "load": "high-load",
    "high-load-low-cpu": "high-load",
    "d-state": "high-load",
    "blocked-tasks": "high-load",
    "memory": "memory-pressure",
    "oom": "memory-pressure",
    "oomkiller": "memory-pressure",
    "swap": "memory-pressure",
    "df-du": "df-du-mismatch",
    "disk-mismatch": "df-du-mismatch",
    "deleted-open": "df-du-mismatch",
    "inode": "inode-exhaustion",
    "inodes": "inode-exhaustion",
    "readonly": "read-only-filesystem",
    "read-only": "read-only-filesystem",
    "fd": "file-descriptor-exhaustion",
    "fd-exhaustion": "file-descriptor-exhaustion",
    "nofile": "file-descriptor-exhaustion",
    "port": "port-conflict",
    "listener": "port-conflict",
    "netstat": "port-conflict",
    "systemd": "systemd-restart-loop",
    "restart-loop": "systemd-restart-loop",
    "panic": "kernel-panic",
    "crash": "kernel-panic",
    "lvm": "lvm-expansion-mismatch",
    "fdisk": "lvm-expansion-mismatch",
    "resize": "lvm-expansion-mismatch",
    "container-disk": "container-runtime-disk-pressure",
    "diskpressure": "container-runtime-disk-pressure",
    "kubelet-disk": "container-runtime-disk-pressure",
}


def _normalize_scenario_key(value: str) -> str:
    return value.strip().lower().replace("_", "-").replace(" ", "-")


def list_linux_scenarios() -> list[dict]:
    """
    Return all known Linux complex scenarios in CLI/UI friendly form.
    """

    return [
        {
            "key": scenario.key,
            "title": scenario.title,
            "summary": scenario.summary,
        }
        for scenario in LINUX_COMPLEX_SCENARIOS
    ]


def get_linux_scenario(key: str) -> dict | None:
    """
    Return a complex Linux troubleshooting scenario by key or alias.
    """

    normalized_key = _normalize_scenario_key(key)
    canonical_key = SCENARIO_ALIASES.get(normalized_key, normalized_key)
    for scenario in LINUX_COMPLEX_SCENARIOS:
        if scenario.key == canonical_key:
            return scenario.to_dict()
    return None
