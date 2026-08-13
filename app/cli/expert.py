from __future__ import annotations

import json

import click


KX_SHORTCUTS = {
    "oom": "OOMKilled",
    "crash": "CrashLoopBackOff",
    "image": "ImagePullBackOff",
    "pull": "ImagePullBackOff",
    "config": "CreateContainerConfigError",
    "runtime": "CreateContainerError",
    "schedule": "FailedScheduling",
    "pending": "FailedScheduling",
    "disk": "DiskPressure",
    "memory": "MemoryPressure",
    "pid": "PIDPressure",
    "node": "NodeNotReady",
    "notready": "NodeNotReady",
    "network": "NetworkUnavailable",
}


LX_SHORTCUTS = {
    "boot": "boot",
    "kernel": "kernel",
    "grub": "grub",
    "grubby": "grub",
    "storage": "storage",
    "lvm": "lvm",
    "dns": "dns",
    "nfs": "nfs",
    "limits": "limits",
    "ulimit": "limits",
    "selinux": "selinux",
    "runtime": "runtime",
    "container": "runtime",
}


LINUX_EXPERT_KNOWLEDGE = {
    "boot": {
        "title": "Linux Boot And Previous-Boot Investigation",
        "summary": (
            "Use this when a host rebooted unexpectedly, boot is slow, or "
            "the outage began around boot time."
        ),
        "first_checks": [
            "journalctl --list-boots",
            "journalctl -b -1 -p warning --no-pager",
            "who -b",
            "last reboot -n 10",
            "systemd-analyze blame",
            "systemd-analyze critical-chain",
        ],
        "aop_commands": [
            "aop linux boot",
            "aop linux kernel",
            "aop linux logs",
        ],
        "dangerous": [
            "reboot",
            "systemctl reboot",
            "grubby --update-kernel",
        ],
        "do_not_assume": (
            "Do not investigate only the current boot after an unexpected "
            "restart; previous-boot evidence is usually the important clue."
        ),
        "kubernetes_relation": (
            "NodeNotReady and pod restarts can begin with kubelet/runtime "
            "startup failures after host reboot."
        ),
        "cloud_relation": (
            "Check cloud stop/start/reboot events, host maintenance, and "
            "instance status checks after preserving Linux boot evidence."
        ),
    },
    "kernel": {
        "title": "Kernel Panic, OOM, Hung Task, And Driver Evidence",
        "summary": (
            "Use this when logs mention panic, OOM, hung tasks, filesystem "
            "errors, driver resets, or kernel warnings."
        ),
        "first_checks": [
            "journalctl -k -p warning --no-pager",
            "journalctl -b -1 -k -p warning --no-pager",
            "dmesg -T",
            "cat /proc/sys/kernel/panic",
            "kdumpctl status",
        ],
        "aop_commands": [
            "aop linux kernel",
            "aop linux boot",
            "aop linux internals --interval 5",
        ],
        "dangerous": [
            "sysctl -w kernel.panic=<value>",
            "echo c > /proc/sysrq-trigger",
            "modprobe -r <driver>",
        ],
        "do_not_assume": (
            "Do not call a reboot an application crash until kernel, power, "
            "OOM, storage, and cloud events are separated."
        ),
        "kubernetes_relation": (
            "Kernel OOM, hung tasks, and driver resets can surface as "
            "OOMKilled, NodeNotReady, DiskPressure, or network flaps."
        ),
        "cloud_relation": (
            "Map kernel timestamps to cloud host events, EBS/NIC impairment, "
            "and maintenance windows."
        ),
    },
    "grub": {
        "title": "GRUB, grubby, Kernel Selection, And Boot Arguments",
        "summary": (
            "Use this when multiple kernels are installed, the wrong kernel "
            "boots first, or cgroup/crashkernel boot arguments matter."
        ),
        "first_checks": [
            "grubby --default-kernel",
            "grubby --default-index",
            "grubby --info=ALL",
            "uname -r",
            "cat /proc/cmdline",
            "ls -1 /boot/vmlinuz-*",
        ],
        "aop_commands": [
            "aop linux boot",
            "aop linux kernel",
            "aop linux explain \"grubby --info=ALL\"",
        ],
        "dangerous": [
            "grubby --set-default <kernel>",
            "grubby --update-kernel=ALL --args=<args>",
            "grub2-mkconfig -o <path>",
        ],
        "do_not_assume": (
            "Do not change the default kernel or boot arguments without a "
            "rollback kernel and a reboot window."
        ),
        "kubernetes_relation": (
            "Kernel version and boot args affect cgroup mode, kubelet "
            "behavior, container runtime, and node readiness."
        ),
        "cloud_relation": (
            "For cloud hosts, confirm console access, rescue path, and image "
            "rollback before changing bootloader state."
        ),
    },
    "storage": {
        "title": "Linux Storage, Filesystem, And I/O Investigation",
        "summary": (
            "Use this for disk full, read-only remounts, I/O errors, device "
            "latency, filesystem mismatch, or storage-backed D-state tasks."
        ),
        "first_checks": [
            "lsblk -f",
            "findmnt",
            "df -hT",
            "df -i",
            "journalctl -k -p warning --no-pager",
            "iostat -xz 1 3",
        ],
        "aop_commands": [
            "aop linux disk --path /var",
            "aop investigate linux disk --path /var",
            "aop linux internals --interval 5",
        ],
        "dangerous": [
            "fsck <device>",
            "xfs_repair <device>",
            "mkfs",
            "mount -o remount,rw <mount>",
        ],
        "do_not_assume": (
            "Do not treat read-only filesystem as a cleanup issue; the kernel "
            "may have protected the filesystem after corruption or I/O risk."
        ),
        "kubernetes_relation": (
            "DiskPressure, evictions, image pull failures, and container "
            "create failures often begin in kubelet/runtime storage paths."
        ),
        "cloud_relation": (
            "Check volume size, attachment, burst balance, IOPS, throughput, "
            "and recent resize events."
        ),
    },
    "lvm": {
        "title": "LVM, Partition, And Filesystem Resize Mismatch",
        "summary": (
            "Use this when cloud disk was expanded but filesystem capacity did "
            "not change, or LVM layers disagree."
        ),
        "first_checks": [
            "lsblk -f",
            "pvs",
            "vgs",
            "lvs -a -o +devices",
            "findmnt",
            "df -hT",
        ],
        "aop_commands": [
            "aop linux plan scenario lvm",
            "aop linux disk --path /var",
        ],
        "dangerous": [
            "pvresize <device>",
            "lvextend",
            "resize2fs <device>",
            "xfs_growfs <mount>",
        ],
        "do_not_assume": (
            "Do not run resize commands until disk, partition, PV, VG, LV, "
            "filesystem type, and mount point are mapped."
        ),
        "kubernetes_relation": (
            "PVC expansion issues can mirror the same layer mismatch: cloud "
            "volume, node device, filesystem, and mounted capacity."
        ),
        "cloud_relation": (
            "Cloud volume expansion may complete before the guest partition, "
            "LVM, and filesystem are grown."
        ),
    },
    "dns": {
        "title": "Linux DNS, Resolver, Route, And Name Lookup",
        "summary": (
            "Use this when applications cannot resolve names, image pulls fail, "
            "or service discovery looks intermittent."
        ),
        "first_checks": [
            "cat /etc/resolv.conf",
            "getent hosts <name>",
            "resolvectl status",
            "ip route get <ip>",
            "ss -tanp",
        ],
        "aop_commands": [
            "aop linux network",
            "aop investigate linux network",
            "aop linux nic",
        ],
        "dangerous": [
            "systemctl restart systemd-resolved",
            "ip route add/change/delete",
            "nmcli connection modify",
        ],
        "do_not_assume": (
            "Do not blame the application before checking resolver, route, "
            "NIC, firewall, proxy, and upstream DNS behavior."
        ),
        "kubernetes_relation": (
            "DNS issues can surface as ImagePullBackOff, service timeouts, "
            "CoreDNS complaints, and readiness probe failures."
        ),
        "cloud_relation": (
            "Check VPC resolver, Route 53/private DNS, security groups, NACLs, "
            "proxy, and NAT path."
        ),
    },
    "nfs": {
        "title": "NFS, Stale Mounts, And D-State Tasks",
        "summary": (
            "Use this when commands hang on a path, tasks enter D state, or "
            "mounts report stale file handles."
        ),
        "first_checks": [
            "findmnt -t nfs,nfs4",
            "nfsstat -m",
            "nfsstat -c",
            "ss -tanp | grep ':2049'",
            "journalctl -k -p warning --no-pager",
        ],
        "aop_commands": [
            "aop linux plan scenario high-load",
            "aop investigate linux cpu",
            "aop linux internals --interval 5",
        ],
        "dangerous": [
            "umount -f <mount>",
            "umount -l <mount>",
            "systemctl restart nfs-client.target",
        ],
        "do_not_assume": (
            "Do not kill D-state tasks repeatedly; they are usually waiting "
            "inside the kernel for storage or NFS to return."
        ),
        "kubernetes_relation": (
            "PVC mount failures and stuck pods may originate from NFS or CSI "
            "mount behavior on the node."
        ),
        "cloud_relation": (
            "Check managed file service health, mount target reachability, "
            "security groups, and DNS."
        ),
    },
    "limits": {
        "title": "Linux Limits, File Descriptors, PIDs, And systemd Limits",
        "summary": (
            "Use this for too many open files, fork failures, socket creation "
            "errors, or service limits that differ from shell limits."
        ),
        "first_checks": [
            "ulimit -n",
            "cat /proc/<pid>/limits",
            "ls /proc/<pid>/fd | wc -l",
            "cat /proc/sys/fs/file-nr",
            "systemctl show <service> -p LimitNOFILE -p TasksMax",
        ],
        "aop_commands": [
            "aop linux processes --top 20",
            "aop linux cgroups --pid <pid>",
            "aop investigate linux service --service <service>",
        ],
        "dangerous": [
            "systemctl set-property <service> LimitNOFILE=<value>",
            "prlimit --pid <pid> --nofile=<value>",
            "kill -9 <pid>",
        ],
        "do_not_assume": (
            "Do not raise limits before finding the leak pattern; it may only "
            "delay the next incident."
        ),
        "kubernetes_relation": (
            "Container limits, process counts, and entrypoint shell limits may "
            "differ from host shell limits."
        ),
        "cloud_relation": (
            "For managed hosts, limits may come from images, bootstrap, systemd "
            "drop-ins, or configuration management."
        ),
    },
    "selinux": {
        "title": "SELinux, Access Denials, And Permission Context",
        "summary": (
            "Use this when permissions look correct but access is denied, "
            "services cannot bind/read/write, or AVC denials appear."
        ),
        "first_checks": [
            "getenforce",
            "sestatus",
            "ausearch -m avc -ts recent",
            "journalctl -t setroubleshoot --no-pager",
            "ls -Z <path>",
        ],
        "aop_commands": [
            "aop linux security",
            "aop linux logs",
            "aop investigate linux service --service <service>",
        ],
        "dangerous": [
            "setenforce 0",
            "semanage fcontext -a ...",
            "restorecon -Rv <path>",
        ],
        "do_not_assume": (
            "Do not disable SELinux as a first fix; preserve AVC evidence and "
            "identify the specific context or policy problem."
        ),
        "kubernetes_relation": (
            "SELinux labels can affect hostPath, CRI-O/container access, and "
            "volume mounts on enforcing nodes."
        ),
        "cloud_relation": (
            "Golden images and hardening baselines may introduce SELinux policy "
            "differences across environments."
        ),
    },
    "runtime": {
        "title": "Container Runtime, kubelet Paths, And Node Disk Pressure",
        "summary": (
            "Use this when image pulls, container creation, pod logs, or "
            "runtime storage behave badly on a Kubernetes node."
        ),
        "first_checks": [
            "systemctl status containerd --no-pager --full",
            "journalctl -u containerd --since '<SINCE>' --no-pager",
            "journalctl -u kubelet --since '<SINCE>' --no-pager",
            "df -hT /var/lib/kubelet /var/lib/containerd",
            "df -i /var/lib/kubelet /var/lib/containerd",
        ],
        "aop_commands": [
            "aop investigate linux service --service containerd",
            "aop investigate linux service --service kubelet",
            "aop investigate linux disk --path /var/lib/containerd",
        ],
        "dangerous": [
            "systemctl restart containerd",
            "systemctl restart kubelet",
            "rm -rf /var/lib/containerd",
            "crictl rmi --prune",
        ],
        "do_not_assume": (
            "Do not manually delete runtime directories without understanding "
            "kubelet/runtime ownership and recovery impact."
        ),
        "kubernetes_relation": (
            "Runtime failures map to ImagePullBackOff, CreateContainerError, "
            "DiskPressure, and NodeNotReady."
        ),
        "cloud_relation": (
            "Runtime pressure can be amplified by small root volumes, low IOPS, "
            "or image-heavy workloads."
        ),
    },
}


def _dump_json(payload) -> None:
    click.echo(
        json.dumps(
            payload,
            indent=2,
            default=str,
        )
    )


@click.group("kx")
def kx() -> None:
    """
    Short Kubernetes expert troubleshooting shortcuts.
    """


@click.group("lx")
def lx() -> None:
    """
    Short Linux expert troubleshooting shortcuts.
    """


@kx.command("list")
def list_kx_shortcuts() -> None:
    """
    List Kubernetes expert shortcuts.
    """

    for shortcut, symptom in sorted(KX_SHORTCUTS.items()):
        click.echo(f"{shortcut:10} -> {symptom}")


@lx.command("list")
def list_lx_shortcuts() -> None:
    """
    List Linux expert shortcuts.
    """

    for shortcut, topic in sorted(LX_SHORTCUTS.items()):
        click.echo(f"{shortcut:10} -> {topic}")


@kx.command("explain")
@click.argument("shortcut")
@click.option("--json", "as_json", is_flag=True)
def explain(shortcut: str, as_json: bool) -> None:
    """
    Explain one Kubernetes shortcut.
    """

    from app.agents.sre.k8s_linux_correlation_agent import (
        correlate_k8s_linux,
    )
    from app.agents.sre.kubernetes_issue_training_agent import (
        get_kubernetes_issue_knowledge,
    )

    normalized = shortcut.strip().lower()
    symptom = KX_SHORTCUTS.get(normalized, shortcut)

    try:
        knowledge = get_kubernetes_issue_knowledge(symptom)
    except ValueError as exc:
        supported = ", ".join(sorted(KX_SHORTCUTS))
        raise click.ClickException(
            f"{exc} Shortcuts: {supported}"
        ) from exc

    try:
        correlation = correlate_k8s_linux(symptom)
    except ValueError:
        correlation = None

    if as_json:
        _dump_json(
            {
                "shortcut": normalized,
                "symptom": knowledge.symptom,
                "knowledge": knowledge.model_dump(mode="json"),
                "linux_correlation": (
                    correlation.model_dump(mode="json")
                    if correlation
                    else None
                ),
            }
        )
        return

    click.echo(f"aop kx {normalized} -> {knowledge.symptom}")
    click.echo(knowledge.summary)

    if knowledge.common_causes:
        click.echo()
        click.echo("Top causes")
        for cause in knowledge.common_causes[:5]:
            click.echo(f"- {cause}")

    if knowledge.safe_kubectl_commands:
        click.echo()
        click.echo("Kubernetes checks")
        for command in knowledge.safe_kubectl_commands[:4]:
            click.echo(f"- {command}")

    if correlation and correlation.next_aop_commands:
        click.echo()
        click.echo("Next AOP commands")
        for command in correlation.next_aop_commands:
            click.echo(f"- {command}")
    elif knowledge.safe_aop_commands:
        click.echo()
        click.echo("Next AOP commands")
        for command in knowledge.safe_aop_commands[:4]:
            click.echo(f"- {command}")

    do_not_assume = []
    do_not_assume.extend(knowledge.do_not_assume)
    if correlation:
        do_not_assume.extend(correlation.do_not_assume)
    if do_not_assume:
        click.echo()
        click.echo(f"Do not assume: {do_not_assume[0]}")


@lx.command("explain")
@click.argument("shortcut")
@click.option("--json", "as_json", is_flag=True)
def explain_lx(shortcut: str, as_json: bool) -> None:
    """
    Explain one Linux expert shortcut.
    """

    normalized = shortcut.strip().lower()
    topic = LX_SHORTCUTS.get(normalized, normalized)
    knowledge = LINUX_EXPERT_KNOWLEDGE.get(topic)
    if not knowledge:
        supported = ", ".join(sorted(LX_SHORTCUTS))
        raise click.ClickException(
            f"Unsupported Linux shortcut '{shortcut}'. Shortcuts: {supported}"
        )

    if as_json:
        _dump_json(
            {
                "shortcut": normalized,
                "topic": topic,
                **knowledge,
            }
        )
        return

    click.echo(f"aop lx {normalized} -> {knowledge['title']}")
    click.echo(knowledge["summary"])

    click.echo()
    click.echo("First safe checks")
    for command in knowledge["first_checks"]:
        click.echo(f"- {command}")

    click.echo()
    click.echo("Next AOP commands")
    for command in knowledge["aop_commands"]:
        click.echo(f"- {command}")

    click.echo()
    click.echo("Dangerous commands to avoid")
    for command in knowledge["dangerous"]:
        click.echo(f"- {command}")

    click.echo()
    click.echo(f"Do not assume: {knowledge['do_not_assume']}")
    click.echo(f"Kubernetes relation: {knowledge['kubernetes_relation']}")
    click.echo(f"Cloud relation: {knowledge['cloud_relation']}")


def _shortcut_command(shortcut_name: str):
    @click.command(shortcut_name)
    @click.option("--json", "as_json", is_flag=True)
    def shortcut(as_json: bool) -> None:
        explain.callback(shortcut_name, as_json)

    return shortcut


def _linux_shortcut_command(shortcut_name: str):
    @click.command(shortcut_name)
    @click.option("--json", "as_json", is_flag=True)
    def shortcut(as_json: bool) -> None:
        explain_lx.callback(shortcut_name, as_json)

    return shortcut


for _shortcut in KX_SHORTCUTS:
    kx.add_command(_shortcut_command(_shortcut))

for _shortcut in LX_SHORTCUTS:
    lx.add_command(_linux_shortcut_command(_shortcut))
