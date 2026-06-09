from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_TIMEOUT_SECONDS = 8
DEFAULT_OUTPUT_LIMIT = 40_000


@dataclass(frozen=True)
class CommandSpec:
    key: str
    label: str
    argv: tuple[str, ...]
    requires_root: bool = False


@dataclass
class CommandResult:
    key: str
    label: str
    command: str
    status: str
    output: str = ""
    error: str = ""
    exit_code: int | None = None
    requires_root: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def run_command(
    spec: CommandSpec,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
) -> CommandResult:
    """
    Run one bounded, read-only diagnostic command without invoking a shell.
    """

    executable = shutil.which(spec.argv[0])
    command = " ".join(spec.argv)

    if executable is None:
        return CommandResult(
            key=spec.key,
            label=spec.label,
            command=command,
            status="unavailable",
            error=f"{spec.argv[0]} is not installed or not in PATH",
            requires_root=spec.requires_root,
        )

    try:
        completed = subprocess.run(
            [executable, *spec.argv[1:]],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
            env={
                **os.environ,
                "LC_ALL": "C",
                "LANG": "C",
            },
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            key=spec.key,
            label=spec.label,
            command=command,
            status="timeout",
            output=(exc.stdout or "")[:output_limit],
            error=f"command exceeded {timeout} seconds",
            requires_root=spec.requires_root,
        )
    except OSError as exc:
        return CommandResult(
            key=spec.key,
            label=spec.label,
            command=command,
            status="error",
            error=str(exc),
            requires_root=spec.requires_root,
        )

    stdout = completed.stdout[:output_limit].rstrip()
    stderr = completed.stderr[:output_limit].rstrip()
    status = "ok" if completed.returncode == 0 else "error"

    if spec.requires_root and os.geteuid() != 0 and completed.returncode != 0:
        status = "permission"

    return CommandResult(
        key=spec.key,
        label=spec.label,
        command=command,
        status=status,
        output=stdout,
        error=stderr,
        exit_code=completed.returncode,
        requires_root=spec.requires_root,
    )


def _spec(
    key: str,
    label: str,
    *argv: str,
    requires_root: bool = False,
) -> CommandSpec:
    return CommandSpec(
        key=key,
        label=label,
        argv=tuple(argv),
        requires_root=requires_root,
    )


def domain_specs(
    domain: str,
    scan_path: str = "/",
    top: int = 10,
) -> list[CommandSpec]:
    """
    Return explicit read-only commands for a Linux diagnostic domain.
    """

    count = str(max(1, min(top, 100)))
    specs = {
        "cpu": [
            _spec("uptime", "Load average and uptime", "uptime"),
            _spec("lscpu", "CPU topology", "lscpu"),
            _spec(
                "cpu_processes",
                "Top CPU-consuming processes",
                "ps",
                "-eo",
                "pid,ppid,state,etimes,%cpu,%mem,comm,args",
                "--sort=-%cpu",
            ),
            _spec("vmstat", "Run queue and CPU activity", "vmstat", "1", "3"),
        ],
        "memory": [
            _spec("free", "Memory and swap overview", "free", "-h"),
            _spec("vmstat", "Memory and swap activity", "vmstat", "1", "3"),
            _spec(
                "memory_processes",
                "Top memory-consuming processes",
                "ps",
                "-eo",
                "pid,ppid,state,etimes,rss,vsz,%mem,comm,args",
                "--sort=-%mem",
            ),
            _spec(
                "meminfo",
                "Kernel memory counters",
                "cat",
                "/proc/meminfo",
            ),
        ],
        "disk": [
            _spec(
                "filesystems",
                "Filesystem capacity and types",
                "df",
                "-hT",
            ),
            _spec("inodes", "Filesystem inode usage", "df", "-i"),
            _spec(
                "mounts",
                "Mounted filesystems and options",
                "findmnt",
                "-r",
            ),
            _spec(
                "largest_paths",
                f"Directory usage under {scan_path}",
                "du",
                "-x",
                "-h",
                f"--max-depth=1",
                scan_path,
            ),
            _spec(
                "deleted_open_files",
                "Deleted files still held open",
                "lsof",
                "+L1",
                requires_root=True,
            ),
        ],
        "network": [
            _spec(
                "addresses",
                "Network interfaces and addresses",
                "ip",
                "-br",
                "address",
            ),
            _spec(
                "link_stats",
                "Interface packet errors and drops",
                "ip",
                "-s",
                "link",
            ),
            _spec("routes", "Routing tables", "ip", "route", "show", "table", "all"),
            _spec("neighbors", "Neighbor and ARP state", "ip", "neighbor"),
            _spec(
                "listening",
                "Listening TCP and UDP sockets",
                "ss",
                "-tulnp",
            ),
            _spec(
                "connections",
                "Established TCP connections",
                "ss",
                "-tnp",
                "state",
                "established",
            ),
            _spec(
                "resolvers",
                "Configured DNS resolvers",
                "cat",
                "/etc/resolv.conf",
            ),
        ],
        "processes": [
            _spec(
                "processes",
                "Processes by CPU usage",
                "ps",
                "-eo",
                "pid,ppid,user,state,etimes,%cpu,%mem,comm,args",
                "--sort=-%cpu",
            ),
            _spec(
                "process_tree",
                "Process hierarchy",
                "pstree",
                "-ap",
            ),
        ],
        "services": [
            _spec(
                "failed_services",
                "Failed systemd units",
                "systemctl",
                "--failed",
                "--no-pager",
            ),
            _spec(
                "running_services",
                "Running systemd services",
                "systemctl",
                "list-units",
                "--type=service",
                "--state=running",
                "--no-pager",
            ),
        ],
        "logs": [
            _spec(
                "priority_logs",
                "Recent warning and error journal",
                "journalctl",
                "-p",
                "warning",
                "-n",
                "80",
                "--no-pager",
            ),
            _spec(
                "kernel_logs",
                "Recent kernel messages",
                "journalctl",
                "-k",
                "-n",
                "80",
                "--no-pager",
            ),
            _spec(
                "auth_logs",
                "Recent SSH service messages",
                "journalctl",
                "-u",
                "ssh",
                "-u",
                "sshd",
                "-n",
                "40",
                "--no-pager",
            ),
        ],
        "kernel": [
            _spec("kernel", "Kernel release", "uname", "-a"),
            _spec(
                "kernel_errors",
                "Kernel warnings and errors",
                "journalctl",
                "-k",
                "-p",
                "warning",
                "-n",
                "100",
                "--no-pager",
            ),
        ],
        "boot": [
            _spec(
                "boot_health",
                "Current boot health",
                "systemctl",
                "is-system-running",
            ),
            _spec(
                "boot_time",
                "Boot performance",
                "systemd-analyze",
                "time",
            ),
            _spec(
                "previous_boot",
                "Previous boot warnings and errors",
                "journalctl",
                "-b",
                "-1",
                "-p",
                "warning",
                "-n",
                "80",
                "--no-pager",
            ),
        ],
        "security": [
            _spec("identity", "Current identity and groups", "id"),
            _spec(
                "failed_logins",
                "Recent failed login attempts",
                "lastb",
                "-n",
                "20",
                requires_root=True,
            ),
            _spec(
                "selinux",
                "SELinux status",
                "getenforce",
            ),
            _spec(
                "apparmor",
                "AppArmor status",
                "aa-status",
                requires_root=True,
            ),
        ],
    }

    selected = specs.get(domain)
    if selected is None:
        raise ValueError(f"unknown Linux diagnostic domain: {domain}")

    if domain in {"cpu", "memory", "processes"}:
        for index, item in enumerate(selected):
            if item.key.endswith("processes"):
                selected[index] = CommandSpec(
                    key=item.key,
                    label=f"{item.label} (review top {count})",
                    argv=item.argv,
                    requires_root=item.requires_root,
                )

    return selected


def collect_domain(
    domain: str,
    scan_path: str = "/",
    top: int = 10,
) -> dict:
    """
    Collect one Linux diagnostic domain as normalized command records.
    """

    if platform.system() != "Linux":
        return {
            "domain": domain,
            "status": "unsupported",
            "host": socket.gethostname(),
            "platform": platform.platform(),
            "message": "Linux diagnostics require a Linux host",
            "results": [],
        }

    results = [
        run_command(spec)
        for spec in domain_specs(domain, scan_path=scan_path, top=top)
    ]

    for result in results:
        if result.key in {
            "cpu_processes",
            "memory_processes",
            "processes",
        }:
            lines = result.output.splitlines()
            result.output = "\n".join(lines[: top + 1])

    return {
        "domain": domain,
        "status": "collected",
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "message": "",
        "results": [result.to_dict() for result in results],
    }


def collect_health() -> dict:
    """
    Return a concise, deterministic Linux host health snapshot.
    """

    if platform.system() != "Linux":
        return {
            "status": "unsupported",
            "host": {
                "hostname": socket.gethostname(),
                "platform": platform.platform(),
                "kernel": platform.release(),
                "architecture": platform.machine(),
                "cpu_count": os.cpu_count() or 1,
                "load_average": None,
            },
            "memory": None,
            "filesystems": [],
            "services": CommandResult(
                key="failed_services",
                label="Failed systemd units",
                command="systemctl --failed --no-pager",
                status="unavailable",
                error="Linux diagnostics require a Linux host",
            ).to_dict(),
            "findings": [
                {
                    "severity": "info",
                    "area": "platform",
                    "summary": "The current host is not Linux.",
                    "next": "Run `aop linux` on the Linux server being investigated.",
                }
            ],
        }

    cpu_count = os.cpu_count() or 1
    load = None
    findings: list[dict[str, str]] = []

    try:
        load = os.getloadavg()
    except OSError:
        pass

    if load and load[0] > cpu_count:
        findings.append(
            {
                "severity": "warning",
                "area": "cpu",
                "summary": (
                    f"1-minute load {load[0]:.2f} exceeds "
                    f"{cpu_count} logical CPUs"
                ),
                "next": "Run `aop linux cpu` and inspect blocked tasks and I/O wait.",
            }
        )

    memory = _memory_health(findings)
    filesystems = _filesystem_health(findings)
    service_result = run_command(
        domain_specs("services")[0],
        timeout=5,
        output_limit=10_000,
    )

    if service_result.status == "ok":
        output = service_result.output.lower()
        if output and "0 loaded units listed" not in output:
            findings.append(
                {
                    "severity": "warning",
                    "area": "services",
                    "summary": "One or more systemd units are failed.",
                    "next": "Run `aop linux services` before restarting anything.",
                }
            )

    status = "healthy"
    if any(item["severity"] == "critical" for item in findings):
        status = "critical"
    elif findings:
        status = "warning"

    return {
        "status": status,
        "host": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "cpu_count": cpu_count,
            "load_average": list(load) if load else None,
        },
        "memory": memory,
        "filesystems": filesystems,
        "services": service_result.to_dict(),
        "findings": findings,
    }


def _memory_health(findings: list[dict[str, str]]) -> dict | None:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return None

    values: dict[str, int] = {}
    try:
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            key, raw = line.split(":", 1)
            number = raw.strip().split()[0]
            values[key] = int(number)
    except (OSError, ValueError, IndexError):
        return None

    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", values.get("MemFree", 0))
    available_percent = (available / total * 100) if total else None

    if available_percent is not None and available_percent < 10:
        findings.append(
            {
                "severity": "critical",
                "area": "memory",
                "summary": (
                    f"Available memory is {available_percent:.1f}% "
                    "of total memory."
                ),
                "next": "Run `aop linux memory` and correlate swap, RSS, cgroups, and OOM logs.",
            }
        )
    elif available_percent is not None and available_percent < 20:
        findings.append(
            {
                "severity": "warning",
                "area": "memory",
                "summary": (
                    f"Available memory is {available_percent:.1f}% "
                    "of total memory."
                ),
                "next": "Run `aop linux memory`; low free memory alone is not sufficient evidence.",
            }
        )

    return {
        "total_kib": total,
        "available_kib": available,
        "available_percent": (
            round(available_percent, 1)
            if available_percent is not None
            else None
        ),
        "swap_total_kib": values.get("SwapTotal", 0),
        "swap_free_kib": values.get("SwapFree", 0),
    }


def _filesystem_health(
    findings: list[dict[str, str]],
) -> list[dict]:
    records = []

    for mount in ("/", "/var", "/tmp"):
        path = Path(mount)
        if not path.exists():
            continue

        try:
            usage = shutil.disk_usage(path)
        except OSError:
            continue

        used_percent = (
            usage.used / usage.total * 100
            if usage.total
            else 0.0
        )
        records.append(
            {
                "mount": mount,
                "total_bytes": usage.total,
                "free_bytes": usage.free,
                "used_percent": round(used_percent, 1),
            }
        )

        if used_percent >= 95:
            severity = "critical"
        elif used_percent >= 85:
            severity = "warning"
        else:
            continue

        findings.append(
            {
                "severity": severity,
                "area": "disk",
                "summary": f"{mount} is {used_percent:.1f}% full.",
                "next": "Run `aop linux disk`; check inodes and deleted-open files before deleting data.",
            }
        )

    return records


def collect_all(
    scan_path: str = "/",
    top: int = 10,
) -> dict:
    domains = (
        "cpu",
        "memory",
        "disk",
        "network",
        "processes",
        "services",
        "logs",
    )
    return {
        "health": collect_health(),
        "domains": {
            domain: collect_domain(
                domain,
                scan_path=scan_path,
                top=top,
            )
            for domain in domains
        },
    }
