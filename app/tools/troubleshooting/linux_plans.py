from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class LinuxPlanStep:
    """
    One read-only step in a Linux troubleshooting plan.
    """

    order: int
    title: str
    command: str
    why: str
    interpretation: str
    risk: str = "safe"
    requires_root: bool = False
    aop_command: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LinuxTroubleshootingPlan:
    """
    Ordered Linux troubleshooting plan.

    Plans explain what an experienced operator would inspect next. They do
    not execute commands and do not remediate the host.
    """

    key: str
    title: str
    symptom: str
    path: str
    safety: str
    steps: tuple[LinuxPlanStep, ...]
    kubernetes_correlation: tuple[str, ...] = ()
    aws_correlation: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        result = asdict(self)
        result["steps"] = [step.to_dict() for step in self.steps]
        return result


def build_disk_plan(path: str = "/") -> dict:
    """
    Build the Linux disk troubleshooting plan for a path.
    """

    target = path or "/"
    plan = LinuxTroubleshootingPlan(
        key="linux.disk",
        title=f"Linux disk investigation plan for {target}",
        symptom="Disk full, DiskPressure, write failure, or filesystem growth",
        path=target,
        safety=(
            "Read-only plan. Do not delete, truncate, restart, unmount, "
            "repair, or resize until evidence supports the cause."
        ),
        steps=(
            LinuxPlanStep(
                order=1,
                title="Confirm filesystem bytes and type",
                command=f"df -hT {target}",
                why=(
                    "Checks whether the backing filesystem is actually full "
                    "and records the filesystem type."
                ),
                interpretation=(
                    "High Use% points to byte capacity pressure. Filesystem "
                    "type helps separate ext4, XFS, NFS, tmpfs, and overlay "
                    "behavior."
                ),
                aop_command=f"aop linux disk --path {target}",
            ),
            LinuxPlanStep(
                order=2,
                title="Check inode exhaustion",
                command=f"df -i {target}",
                why=(
                    "A filesystem can fail with 'No space left on device' "
                    "when inodes are exhausted even if bytes are available."
                ),
                interpretation=(
                    "High IUse% usually means too many small files, cache "
                    "entries, temporary files, or container/runtime artifacts."
                ),
            ),
            LinuxPlanStep(
                order=3,
                title="Confirm mount identity and options",
                command=f"findmnt -no SOURCE,FSTYPE,OPTIONS,TARGET {target}",
                why=(
                    "Verifies the source device, filesystem type, mount "
                    "options, and target path before scanning directories."
                ),
                interpretation=(
                    "A missing or wrong mount can hide data under a mount "
                    "point. A read-only option changes the incident from "
                    "cleanup to filesystem or storage health."
                ),
            ),
            LinuxPlanStep(
                order=4,
                title="Locate visible growth safely",
                command=f"du -x -h --max-depth=1 {target} | sort -h",
                why=(
                    "Finds the largest immediate directories while staying "
                    "on the same filesystem and bounding recursion."
                ),
                interpretation=(
                    "Follow the largest directory one level at a time. Avoid "
                    "unbounded scans from / during production incidents."
                ),
                risk="careful",
            ),
            LinuxPlanStep(
                order=5,
                title="Find recent large files",
                command=(
                    f"find {target} -xdev -type f -size +100M -printf "
                    "'%s %p\\n' | sort -n | tail -n 20"
                ),
                why=(
                    "Identifies large files that may explain recent growth "
                    "without crossing into other filesystems."
                ),
                interpretation=(
                    "Large files should be correlated with owning service, "
                    "recent deployment, log rotation, backup, or core dump "
                    "behavior before remediation."
                ),
                risk="careful",
            ),
            LinuxPlanStep(
                order=6,
                title="Check deleted-open files",
                command=f"lsof +L1 {target}",
                why=(
                    "Explains cases where df shows space used but du cannot "
                    "find enough visible files."
                ),
                interpretation=(
                    "The space is released only when the owning process "
                    "closes the deleted file. Preserve evidence before "
                    "restarting a service."
                ),
                risk="elevated",
                requires_root=True,
            ),
            LinuxPlanStep(
                order=7,
                title="Check kernel filesystem and storage errors",
                command=(
                    "journalctl -k -g "
                    "'I/O error|EXT4-fs|XFS|BTRFS|nvme|scsi|reset|read-only' "
                    "--no-pager"
                ),
                why=(
                    "Detects device errors, filesystem warnings, controller "
                    "resets, and read-only remounts."
                ),
                interpretation=(
                    "Storage or filesystem errors change the next step from "
                    "space cleanup to storage-layer investigation."
                ),
            ),
            LinuxPlanStep(
                order=8,
                title="Separate capacity from I/O latency",
                command="iostat -xz 1 5",
                why=(
                    "A filesystem does not need to be full to cause service "
                    "latency or write failures."
                ),
                interpretation=(
                    "Correlate await, queue depth, utilization, device type, "
                    "and workload baseline before blaming disk capacity."
                ),
            ),
        ),
        kubernetes_correlation=(
            "If the host is a Kubernetes node, inspect /var/lib/kubelet and "
            "/var/lib/containerd for pod logs, image layers, snapshots, and "
            "orphaned pod data.",
            "Correlate Linux evidence with Node DiskPressure, pod evictions, "
            "ephemeral-storage requests and limits, and kubelet garbage "
            "collection.",
        ),
        aws_correlation=(
            "For EC2/EBS, confirm the volume, partition, and filesystem were "
            "all expanded when capacity changed.",
            "Correlate CloudWatch EBS IOPS, throughput, queue length, burst "
            "balance, and instance EBS bandwidth limits before concluding the "
            "issue is only filesystem usage.",
        ),
    )
    return plan.to_dict()
