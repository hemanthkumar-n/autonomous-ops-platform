from __future__ import annotations

import os
import platform
import socket
from collections import Counter
from pathlib import Path

from app.schemas.linux import (
    CgroupEvidence,
    CgroupMembership,
    LinuxFinding,
    LinuxInternalsEvidence,
    PressureResource,
    PressureSample,
)


IMPORTANT_VM_COUNTERS = {
    "pgfault",
    "pgmajfault",
    "pswpin",
    "pswpout",
    "pgscan_kswapd",
    "pgscan_direct",
    "pgsteal_kswapd",
    "pgsteal_direct",
    "oom_kill",
    "compact_stall",
    "workingset_refault_anon",
    "workingset_refault_file",
}


def parse_pressure(text: str) -> PressureResource:
    values: dict[str, PressureSample] = {}

    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue

        category = parts[0]
        fields = {}
        for item in parts[1:]:
            key, value = item.split("=", 1)
            fields[key] = value

        values[category] = PressureSample(
            avg10=float(fields["avg10"]),
            avg60=float(fields["avg60"]),
            avg300=float(fields["avg300"]),
            total=int(fields["total"]),
        )

    return PressureResource(
        some=values.get("some"),
        full=values.get("full"),
    )


def parse_loadavg(
    text: str,
) -> tuple[list[float], int, int, int]:
    fields = text.split()
    running, total = fields[3].split("/", 1)
    return (
        [float(value) for value in fields[:3]],
        int(running),
        int(total),
        int(fields[4]),
    )


def parse_key_value_integers(text: str) -> dict[str, int]:
    values = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) >= 2:
            values[fields[0]] = int(fields[1])
    return values


def parse_cgroup_memberships(text: str) -> list[CgroupMembership]:
    memberships = []
    for line in text.splitlines():
        hierarchy, controllers, path = line.split(":", 2)
        memberships.append(
            CgroupMembership(
                hierarchy_id=int(hierarchy),
                controllers=[
                    item
                    for item in controllers.split(",")
                    if item
                ],
                path=path,
            )
        )
    return memberships


def parse_flat_values(text: str) -> dict[str, str | int]:
    values: dict[str, str | int] = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 2:
            continue
        key, raw = fields
        values[key] = int(raw) if raw.lstrip("-").isdigit() else raw
    return values


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None


def _process_states(proc_root: Path) -> dict[str, int]:
    states: Counter[str] = Counter()

    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        stat = _read(entry / "stat")
        if stat is None:
            continue

        closing = stat.rfind(")")
        if closing >= 0:
            remainder = stat[closing + 2 :].split()
            if remainder:
                states[remainder[0]] += 1

    return dict(sorted(states.items()))


def collect_internals(
    proc_root: Path = Path("/proc"),
) -> LinuxInternalsEvidence:
    if platform.system() != "Linux":
        return LinuxInternalsEvidence(
            status="unsupported",
            hostname=socket.gethostname(),
            cpu_count=os.cpu_count() or 1,
            unavailable=["Linux internals require a Linux host"],
        )

    unavailable = []
    load_average: list[float] = []
    running_tasks = total_tasks = last_pid = None

    load_text = _read(proc_root / "loadavg")
    if load_text:
        try:
            (
                load_average,
                running_tasks,
                total_tasks,
                last_pid,
            ) = parse_loadavg(load_text)
        except (ValueError, IndexError):
            unavailable.append("Unable to parse /proc/loadavg")
    else:
        unavailable.append("/proc/loadavg")

    uptime_seconds = None
    uptime_text = _read(proc_root / "uptime")
    if uptime_text:
        try:
            uptime_seconds = float(uptime_text.split()[0])
        except (ValueError, IndexError):
            unavailable.append("Unable to parse /proc/uptime")

    pressure = {}
    for resource in ("cpu", "memory", "io"):
        text = _read(proc_root / "pressure" / resource)
        if text:
            try:
                pressure[resource] = parse_pressure(text)
            except (ValueError, KeyError):
                unavailable.append(
                    f"Unable to parse /proc/pressure/{resource}"
                )
        else:
            unavailable.append(f"/proc/pressure/{resource}")

    vm_counters = {}
    vmstat_text = _read(proc_root / "vmstat")
    if vmstat_text:
        try:
            all_counters = parse_key_value_integers(vmstat_text)
            vm_counters = {
                key: value
                for key, value in all_counters.items()
                if key in IMPORTANT_VM_COUNTERS
            }
        except ValueError:
            unavailable.append("Unable to parse /proc/vmstat")

    try:
        process_states = _process_states(proc_root)
    except OSError:
        process_states = {}
        unavailable.append("Process states")

    cpu_count = os.cpu_count() or 1
    findings = _internals_findings(
        load_average=load_average,
        cpu_count=cpu_count,
        process_states=process_states,
        pressure=pressure,
        vm_counters=vm_counters,
    )

    return LinuxInternalsEvidence(
        status="collected",
        hostname=socket.gethostname(),
        load_average=load_average,
        running_tasks=running_tasks,
        total_tasks=total_tasks,
        last_pid=last_pid,
        uptime_seconds=uptime_seconds,
        cpu_count=cpu_count,
        process_states=process_states,
        pressure=pressure,
        vm_counters=vm_counters,
        findings=findings,
        unavailable=unavailable,
    )


def _internals_findings(
    load_average: list[float],
    cpu_count: int,
    process_states: dict[str, int],
    pressure: dict[str, PressureResource],
    vm_counters: dict[str, int],
) -> list[LinuxFinding]:
    findings = []

    if load_average and load_average[0] > cpu_count:
        findings.append(
            LinuxFinding(
                severity="warning",
                area="scheduler",
                summary=(
                    f"1-minute load {load_average[0]:.2f} exceeds "
                    f"{cpu_count} logical CPUs."
                ),
                next=(
                    "Correlate runnable tasks, D-state tasks, CPU PSI, "
                    "and I/O PSI before calling this CPU saturation."
                ),
            )
        )

    blocked = process_states.get("D", 0)
    if blocked:
        findings.append(
            LinuxFinding(
                severity="warning",
                area="scheduler",
                summary=f"{blocked} process(es) are in uninterruptible D state.",
                next=(
                    "Inspect process wchan/stack and correlate storage, "
                    "NFS, device, and kernel evidence."
                ),
            )
        )

    for resource, evidence in pressure.items():
        samples = [
            (scope, sample)
            for scope, sample in (
                ("some", evidence.some),
                ("full", evidence.full),
            )
            if sample is not None
        ]
        if samples:
            scope, sample = max(
                samples,
                key=lambda item: item[1].avg10,
            )
        else:
            continue
        if sample.avg10 >= 10:
            findings.append(
                LinuxFinding(
                    severity="warning",
                    area=f"{resource}_pressure",
                    summary=(
                        f"{resource} PSI {scope} avg10 is "
                        f"{sample.avg10:.2f}%."
                    ),
                    next=(
                        f"Correlate {resource} pressure with workload and "
                        "cgroup limits."
                    ),
                )
            )

    if vm_counters.get("oom_kill", 0) > 0:
        findings.append(
            LinuxFinding(
                severity="info",
                area="memory",
                summary=(
                    "Kernel vmstat records one or more cumulative OOM kills "
                    "since boot."
                ),
                next=(
                    "Use incident timestamps and kernel logs to determine "
                    "whether an OOM belongs to the current incident."
                ),
            )
        )

    return findings


def collect_cgroups(
    pid: int,
    proc_root: Path = Path("/proc"),
    cgroup_root: Path = Path("/sys/fs/cgroup"),
) -> CgroupEvidence:
    if platform.system() != "Linux":
        return CgroupEvidence(
            status="unsupported",
            hostname=socket.gethostname(),
            pid=pid,
            unavailable=["Cgroup diagnostics require a Linux host"],
        )

    membership_text = _read(proc_root / str(pid) / "cgroup")
    if membership_text is None:
        return CgroupEvidence(
            status="unavailable",
            hostname=socket.gethostname(),
            pid=pid,
            unavailable=[f"/proc/{pid}/cgroup"],
        )

    try:
        memberships = parse_cgroup_memberships(membership_text)
    except (ValueError, IndexError):
        return CgroupEvidence(
            status="error",
            hostname=socket.gethostname(),
            pid=pid,
            unavailable=[f"Unable to parse /proc/{pid}/cgroup"],
        )

    is_v2 = (cgroup_root / "cgroup.controllers").exists()
    if not is_v2:
        return CgroupEvidence(
            status="collected",
            hostname=socket.gethostname(),
            pid=pid,
            version=1,
            memberships=memberships,
            findings=[
                LinuxFinding(
                    severity="info",
                    area="cgroups",
                    summary="Cgroup v1 or hybrid hierarchy detected.",
                    next=(
                        "Inspect each controller-specific mount; v1 "
                        "normalization will be expanded separately."
                    ),
                )
            ],
        )

    unified = next(
        (
            membership
            for membership in memberships
            if membership.hierarchy_id == 0
            and not membership.controllers
        ),
        None,
    )
    relative_path = unified.path if unified else "/"
    group_path = cgroup_root / relative_path.lstrip("/")
    unavailable = []

    controllers_text = _read(group_path / "cgroup.controllers")
    controllers = controllers_text.split() if controllers_text else []

    cpu = _collect_cgroup_cpu(group_path, unavailable)
    memory = _collect_cgroup_memory(group_path, unavailable)
    io = _collect_cgroup_io(group_path, unavailable)
    pids = _collect_cgroup_pids(group_path, unavailable)
    pressure = _collect_cgroup_pressure(group_path, unavailable)
    findings = _cgroup_findings(cpu, memory, pids, pressure)

    return CgroupEvidence(
        status="collected",
        hostname=socket.gethostname(),
        pid=pid,
        version=2,
        memberships=memberships,
        cgroup_path=str(group_path),
        controllers=controllers,
        cpu=cpu,
        memory=memory,
        io=io,
        pids=pids,
        pressure=pressure,
        findings=findings,
        unavailable=unavailable,
    )


def _read_value(
    path: Path,
    unavailable: list[str],
) -> str | int | None:
    text = _read(path)
    if text is None:
        unavailable.append(path.name)
        return None
    return int(text) if text.lstrip("-").isdigit() else text


def _collect_cgroup_cpu(
    path: Path,
    unavailable: list[str],
) -> dict[str, str | int]:
    values: dict[str, str | int] = {}
    max_value = _read_value(path / "cpu.max", unavailable)
    if max_value is not None:
        values["max"] = max_value
    weight = _read_value(path / "cpu.weight", unavailable)
    if weight is not None:
        values["weight"] = weight
    stat = _read(path / "cpu.stat")
    if stat:
        values.update(parse_flat_values(stat))
    return values


def _collect_cgroup_memory(
    path: Path,
    unavailable: list[str],
) -> dict[str, str | int]:
    values: dict[str, str | int] = {}
    for filename in (
        "memory.current",
        "memory.min",
        "memory.low",
        "memory.high",
        "memory.max",
        "memory.swap.current",
        "memory.swap.max",
    ):
        value = _read_value(path / filename, unavailable)
        if value is not None:
            values[filename.removeprefix("memory.")] = value

    events = _read(path / "memory.events")
    if events:
        for key, value in parse_flat_values(events).items():
            values[f"event_{key}"] = value
    return values


def _collect_cgroup_io(
    path: Path,
    unavailable: list[str],
) -> dict[str, str | int]:
    values: dict[str, str | int] = {}
    for filename in ("io.max", "io.weight", "io.stat"):
        value = _read_value(path / filename, unavailable)
        if value is not None:
            values[filename.removeprefix("io.")] = value
    return values


def _collect_cgroup_pids(
    path: Path,
    unavailable: list[str],
) -> dict[str, str | int]:
    values: dict[str, str | int] = {}
    for filename in ("pids.current", "pids.max"):
        value = _read_value(path / filename, unavailable)
        if value is not None:
            values[filename.removeprefix("pids.")] = value
    events = _read(path / "pids.events")
    if events:
        for key, value in parse_flat_values(events).items():
            values[f"event_{key}"] = value
    return values


def _collect_cgroup_pressure(
    path: Path,
    unavailable: list[str],
) -> dict[str, PressureResource]:
    pressure = {}
    for resource in ("cpu", "memory", "io"):
        text = _read(path / f"{resource}.pressure")
        if text:
            try:
                pressure[resource] = parse_pressure(text)
            except (ValueError, KeyError):
                unavailable.append(f"{resource}.pressure parse")
        else:
            unavailable.append(f"{resource}.pressure")
    return pressure


def _cgroup_findings(
    cpu: dict[str, str | int],
    memory: dict[str, str | int],
    pids: dict[str, str | int],
    pressure: dict[str, PressureResource],
) -> list[LinuxFinding]:
    findings = []

    if int(cpu.get("nr_throttled", 0)) > 0:
        findings.append(
            LinuxFinding(
                severity="info",
                area="cgroup_cpu",
                summary=(
                    "The cgroup records cumulative CPU throttling since "
                    "its counters were created."
                ),
                next=(
                    "Collect a timed delta for nr_throttled and "
                    "throttled_usec before calling throttling active."
                ),
            )
        )

    if int(memory.get("event_oom_kill", 0)) > 0:
        findings.append(
            LinuxFinding(
                severity="warning",
                area="cgroup_memory",
                summary=(
                    "The cgroup records one or more cumulative OOM kills."
                ),
                next=(
                    "Correlate memory.current, memory.max, process RSS, "
                    "kernel timestamps, and Kubernetes limits."
                ),
            )
        )
    elif int(memory.get("event_high", 0)) > 0:
        findings.append(
            LinuxFinding(
                severity="info",
                area="cgroup_memory",
                summary=(
                    "The cgroup records cumulative memory.high events."
                ),
                next=(
                    "Use PSI and timed event deltas to determine whether "
                    "reclaim pressure is active."
                ),
            )
        )

    current = pids.get("current")
    maximum = pids.get("max")
    if isinstance(current, int) and isinstance(maximum, int) and maximum > 0:
        if current / maximum >= 0.9:
            findings.append(
                LinuxFinding(
                    severity="warning",
                    area="cgroup_pids",
                    summary=(
                        f"PID usage is {current}/{maximum} "
                        "for this cgroup."
                    ),
                    next=(
                        "Inspect thread/process growth and pids.events "
                        "before increasing the limit."
                    ),
                )
            )

    for resource, evidence in pressure.items():
        samples = [
            (scope, sample)
            for scope, sample in (
                ("some", evidence.some),
                ("full", evidence.full),
            )
            if sample is not None
        ]
        if samples:
            scope, sample = max(
                samples,
                key=lambda item: item[1].avg10,
            )
        else:
            continue
        if sample.avg10 >= 10:
            findings.append(
                LinuxFinding(
                    severity="warning",
                    area=f"cgroup_{resource}_pressure",
                    summary=(
                        f"Cgroup {resource} PSI {scope} avg10 is "
                        f"{sample.avg10:.2f}%."
                    ),
                    next=(
                        "Compare cgroup pressure with host pressure to "
                        "separate local limits from host contention."
                    ),
                )
            )

    return findings
