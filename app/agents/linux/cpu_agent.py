from __future__ import annotations

from app.schemas.linux import LinuxCpuFinding, LinuxCpuInvestigation


def _result_map(evidence: dict) -> dict[str, dict]:
    return {
        item["key"]: item
        for item in evidence.get("results", [])
    }


def _data_lines(output: str, header_prefix: str | None = None) -> list[str]:
    lines = [
        line.strip()
        for line in output.splitlines()
        if line.strip()
    ]
    if header_prefix and lines:
        if lines[0].lower().startswith(header_prefix.lower()):
            return lines[1:]
    return lines


def _parse_vmstat_cpu(output: str) -> dict[str, int]:
    lines = _data_lines(output)
    header_index = None
    for index, line in enumerate(lines):
        fields = line.split()
        if {"us", "sy", "id", "wa", "st"}.issubset(set(fields)):
            header_index = index
            break
    if header_index is None:
        return {}

    header = lines[header_index].split()
    samples = []
    for line in lines[header_index + 1 :]:
        fields = line.split()
        if len(fields) < len(header):
            continue
        try:
            samples.append(
                {
                    key: int(fields[header.index(key)])
                    for key in ("us", "sy", "id", "wa", "st")
                }
            )
        except (ValueError, IndexError):
            continue
    if not samples:
        return {}

    # The first vmstat sample is often since boot. Prefer live samples.
    live_samples = samples[1:] if len(samples) > 1 else samples
    return {
        key: max(sample[key] for sample in live_samples)
        for key in ("us", "sy", "id", "wa", "st")
    }


def _pressure_avg10(internals: dict, resource: str, scope: str = "some") -> float:
    pressure = internals.get("pressure", {})
    resource_pressure = pressure.get(resource) or {}
    sample = resource_pressure.get(scope) or {}
    return float(sample.get("avg10") or 0.0)


def _finding(
    code: str,
    severity: str,
    confidence: int,
    summary: str,
    evidence: list[str],
    next_step: str,
) -> LinuxCpuFinding:
    return LinuxCpuFinding(
        code=code,
        severity=severity,
        confidence=confidence,
        summary=summary,
        evidence=evidence,
        next=next_step,
        next_explanation=_next_explanation(code),
    )


def _next_explanation(code: str) -> str:
    explanations = {
        "d_state_blocked_tasks": (
            "Uninterruptible D-state tasks count toward load average but are "
            "usually waiting inside the kernel, often on storage, NFS, or "
            "device I/O. Treat this as blocked work, not pure CPU saturation."
        ),
        "io_pressure_behind_load": (
            "High load with I/O wait or I/O PSI means work is losing time "
            "below the process layer. Correlate disk, filesystem, network "
            "storage, and cloud-volume latency before blaming the application."
        ),
        "cpu_saturation": (
            "High user/system CPU or CPU PSI means runnable work is competing "
            "for CPU time. Inspect top CPU consumers, run queue, limits, and "
            "recent workload change."
        ),
        "steal_time_pressure": (
            "Steal time means the hypervisor did not schedule this VM when it "
            "wanted CPU. On cloud hosts, correlate instance type, noisy "
            "neighbors, host health, and CPU credits where relevant."
        ),
        "high_load_low_cpu": (
            "Load average includes runnable and uninterruptible tasks. Low CPU "
            "busy with high load means the next step is task state and wait "
            "analysis, not CPU tuning."
        ),
        "insufficient_evidence": (
            "AOP needs load, task state, and vmstat or PSI evidence to safely "
            "separate CPU saturation from blocked work."
        ),
    }
    return explanations.get(code, "")


def analyze_cpu_evidence(evidence: dict) -> LinuxCpuInvestigation:
    """
    Convert CPU and scheduler evidence into deterministic diagnosis.
    """

    if evidence.get("status") != "collected":
        return LinuxCpuInvestigation(
            status="unsupported",
            hostname=evidence.get("host", "unknown"),
            platform=evidence.get("platform", "unknown"),
            primary_diagnosis="unsupported_platform",
            severity="info",
            confidence=100,
            summary=evidence.get(
                "message",
                "Linux CPU evidence is unavailable.",
            ),
            raw_evidence=evidence,
        )

    results = _result_map(evidence)
    gaps = [
        f"{item['label']}: {item['status']}"
        for item in evidence.get("results", [])
        if item.get("status") != "ok"
    ]
    internals = evidence.get("internals") or {}
    if internals.get("status") != "collected":
        gaps.extend(internals.get("unavailable", ["Linux internals"]))

    vmstat = results.get("vmstat", {})
    cpu_processes = results.get("cpu_processes", {})
    vmstat_cpu = (
        _parse_vmstat_cpu(vmstat.get("output", ""))
        if vmstat.get("status") == "ok"
        else {}
    )
    top_cpu_processes = _data_lines(cpu_processes.get("output", ""), "pid")

    load_average = internals.get("load_average", []) or []
    cpu_count = internals.get("cpu_count")
    running_tasks = internals.get("running_tasks")
    total_tasks = internals.get("total_tasks")
    process_states = internals.get("process_states", {}) or {}
    pressure = internals.get("pressure", {}) or {}

    load1 = load_average[0] if load_average else None
    high_load = (
        load1 is not None
        and cpu_count is not None
        and load1 > cpu_count
    )
    cpu_busy = None
    if vmstat_cpu:
        cpu_busy = vmstat_cpu.get("us", 0) + vmstat_cpu.get("sy", 0)
    cpu_psi = _pressure_avg10(internals, "cpu")
    io_psi = _pressure_avg10(internals, "io")
    blocked = int(process_states.get("D", 0) or 0)

    findings: list[LinuxCpuFinding] = []

    if high_load and blocked:
        findings.append(
            _finding(
                "d_state_blocked_tasks",
                "warning",
                96,
                (
                    f"Load {load1:.2f} exceeds {cpu_count} CPU(s) and "
                    f"{blocked} task(s) are in D state."
                ),
                [
                    f"load1={load1:.2f}",
                    f"cpu_count={cpu_count}",
                    f"D={blocked}",
                ],
                (
                    "Inspect blocked process wchan/stack and correlate disk, "
                    "NFS, device, and kernel I/O evidence."
                ),
            )
        )

    if high_load and (vmstat_cpu.get("wa", 0) >= 20 or io_psi >= 10):
        findings.append(
            _finding(
                "io_pressure_behind_load",
                "warning",
                92,
                (
                    "High load is correlated with I/O wait or I/O pressure."
                ),
                [
                    f"wa={vmstat_cpu.get('wa', 0)}",
                    f"io_psi_some_avg10={io_psi:.2f}",
                ],
                (
                    "Run disk, filesystem, NIC, and storage checks before "
                    "calling this CPU saturation."
                ),
            )
        )

    if (cpu_busy is not None and cpu_busy >= 85) or cpu_psi >= 10:
        findings.append(
            _finding(
                "cpu_saturation",
                "warning",
                90,
                "CPU busy time or CPU PSI indicates runnable work contention.",
                [
                    *( [f"cpu_busy={cpu_busy}"] if cpu_busy is not None else [] ),
                    f"cpu_psi_some_avg10={cpu_psi:.2f}",
                ],
                (
                    "Inspect top CPU consumers, run queue, cgroup CPU limits, "
                    "and recent workload changes."
                ),
            )
        )

    if vmstat_cpu.get("st", 0) >= 10:
        findings.append(
            _finding(
                "steal_time_pressure",
                "warning",
                88,
                f"CPU steal time is {vmstat_cpu['st']}%.",
                [f"st={vmstat_cpu['st']}"],
                (
                    "Correlate with hypervisor, cloud instance, host health, "
                    "or CPU credit signals."
                ),
            )
        )

    if high_load and cpu_busy is not None and cpu_busy < 50 and not findings:
        findings.append(
            _finding(
                "high_load_low_cpu",
                "warning",
                84,
                (
                    f"Load {load1:.2f} exceeds CPU count but CPU busy is "
                    f"{cpu_busy}%."
                ),
                [f"load1={load1:.2f}", f"cpu_busy={cpu_busy}"],
                (
                    "Inspect runnable versus blocked task state, PSI, and "
                    "I/O wait before changing CPU allocation."
                ),
            )
        )

    if load1 is None or cpu_count is None:
        findings.append(
            _finding(
                "insufficient_evidence",
                "warning",
                100,
                "Load average or CPU count could not be determined.",
                gaps or ["load or CPU count missing"],
                "Restore access to /proc/loadavg and repeat the investigation.",
            )
        )

    priority = {
        "d_state_blocked_tasks": 0,
        "io_pressure_behind_load": 1,
        "cpu_saturation": 2,
        "steal_time_pressure": 3,
        "high_load_low_cpu": 4,
        "insufficient_evidence": 5,
    }
    findings.sort(key=lambda item: priority[item.code])

    if findings:
        primary = findings[0]
        diagnosis = primary.code
        severity = primary.severity
        confidence = primary.confidence
        summary = primary.summary
    else:
        diagnosis = "no_immediate_cpu_pressure"
        severity = "info"
        confidence = max(60, 95 - (len(gaps) * 8))
        summary = (
            "No immediate high-load, D-state, CPU saturation, I/O wait, or "
            "steal-time pressure was identified."
        )

    if gaps and diagnosis != "insufficient_evidence":
        confidence = max(50, confidence - min(20, len(gaps) * 4))

    return LinuxCpuInvestigation(
        status="diagnosed",
        hostname=evidence.get("host", "unknown"),
        platform=evidence.get("platform", "unknown"),
        primary_diagnosis=diagnosis,
        severity=severity,
        confidence=confidence,
        summary=summary,
        load_average=load_average,
        cpu_count=cpu_count,
        running_tasks=running_tasks,
        total_tasks=total_tasks,
        process_states=process_states,
        vmstat_cpu=vmstat_cpu,
        pressure=pressure,
        top_cpu_processes=top_cpu_processes,
        findings=findings,
        evidence_gaps=gaps,
        raw_evidence=evidence,
    )
