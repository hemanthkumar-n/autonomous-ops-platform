from __future__ import annotations

import re

from app.schemas.linux import (
    LinuxMemoryFinding,
    LinuxMemoryInvestigation,
)


_OOM_PATTERN = re.compile(
    r"(out of memory|killed process|oom-kill|memory cgroup out of memory)",
    re.IGNORECASE,
)


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


def _parse_meminfo(output: str) -> dict[str, int]:
    values = {}
    for line in output.splitlines():
        key, separator, raw_value = line.partition(":")
        if not separator:
            continue
        fields = raw_value.strip().split()
        if not fields:
            continue
        try:
            values[key] = int(fields[0])
        except ValueError:
            continue
    return values


def _parse_vmstat_swap(output: str) -> tuple[int | None, int | None]:
    lines = _data_lines(output)
    if len(lines) < 3:
        return None, None

    header_index = None
    for index, line in enumerate(lines):
        fields = line.split()
        if "si" in fields and "so" in fields:
            header_index = index
            break
    if header_index is None:
        return None, None

    header = lines[header_index].split()
    si_index = header.index("si")
    so_index = header.index("so")
    samples = []
    for line in lines[header_index + 1 :]:
        fields = line.split()
        if len(fields) <= max(si_index, so_index):
            continue
        try:
            samples.append((int(fields[si_index]), int(fields[so_index])))
        except ValueError:
            continue
    if not samples:
        return None, None

    # vmstat's first data line is often since boot. Prefer live samples.
    live_samples = samples[1:] if len(samples) > 1 else samples
    swap_in = max(item[0] for item in live_samples)
    swap_out = max(item[1] for item in live_samples)
    return swap_in, swap_out


def _severity_for_available(percent: float) -> str:
    if percent <= 5:
        return "critical"
    if percent <= 10:
        return "warning"
    return "info"


def _finding(
    code: str,
    severity: str,
    confidence: int,
    summary: str,
    evidence: list[str],
    next_step: str,
) -> LinuxMemoryFinding:
    return LinuxMemoryFinding(
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
        "kernel_oom_kill": (
            "Kernel OOM evidence proves a process or cgroup could not satisfy "
            "memory allocation. Preserve the log line because it identifies "
            "the victim, allocation context, and sometimes the cgroup."
        ),
        "cgroup_memory_oom": (
            "A cgroup OOM means the workload hit its configured container or "
            "service memory boundary even if the host still had available "
            "memory."
        ),
        "active_swap_pressure": (
            "Active swap-in or swap-out during the sample means the system is "
            "moving memory pages under pressure, which can create severe "
            "latency before an OOM occurs."
        ),
        "low_available_memory": (
            "MemAvailable estimates reclaimable memory better than raw free "
            "memory. Low availability means new allocations may trigger "
            "reclaim, swap, stalls, or OOM."
        ),
        "cgroup_memory_high": (
            "memory.high events show the cgroup crossed its soft throttle "
            "boundary. This can slow workloads before a hard OOM is reached."
        ),
        "insufficient_evidence": (
            "AOP needs meminfo and swap evidence to distinguish cache use, "
            "real pressure, active swap, and OOM conditions."
        ),
    }
    return explanations.get(code, "")


def analyze_memory_evidence(evidence: dict) -> LinuxMemoryInvestigation:
    """
    Convert ordered memory evidence into deterministic diagnosis.
    """

    if evidence.get("status") != "collected":
        return LinuxMemoryInvestigation(
            status="unsupported",
            hostname=evidence.get("host", "unknown"),
            platform=evidence.get("platform", "unknown"),
            pid=evidence.get("pid"),
            primary_diagnosis="unsupported_platform",
            severity="info",
            confidence=100,
            summary=evidence.get(
                "message",
                "Linux memory evidence is unavailable.",
            ),
            raw_evidence=evidence,
        )

    results = _result_map(evidence)
    gaps = [
        f"{item['label']}: {item['status']}"
        for item in evidence.get("results", [])
        if item.get("status") != "ok"
    ]

    meminfo_result = results.get("meminfo", {})
    vmstat_result = results.get("vmstat", {})
    processes_result = results.get("memory_processes", {})
    oom_result = results.get("kernel_oom", {})

    meminfo = (
        _parse_meminfo(meminfo_result.get("output", ""))
        if meminfo_result.get("status") == "ok"
        else {}
    )
    mem_total = meminfo.get("MemTotal")
    mem_available = meminfo.get("MemAvailable")
    swap_total = meminfo.get("SwapTotal")
    swap_free = meminfo.get("SwapFree")

    available_percent = None
    if mem_total and mem_available is not None:
        available_percent = (mem_available / mem_total) * 100

    swap_used_percent = None
    if swap_total and swap_total > 0 and swap_free is not None:
        swap_used_percent = ((swap_total - swap_free) / swap_total) * 100

    swap_in, swap_out = (
        _parse_vmstat_swap(vmstat_result.get("output", ""))
        if vmstat_result.get("status") == "ok"
        else (None, None)
    )

    oom_events = [
        line
        for line in _data_lines(oom_result.get("output", ""))
        if line != "-- No entries --" and _OOM_PATTERN.search(line)
    ]
    top_memory_processes = _data_lines(
        processes_result.get("output", ""),
        "pid",
    )

    cgroup = evidence.get("cgroup") or {}
    cgroup_memory = (
        cgroup.get("memory", {})
        if cgroup.get("status") == "collected"
        else {}
    )
    if cgroup and cgroup.get("status") != "collected":
        gaps.extend(cgroup.get("unavailable", []))

    findings: list[LinuxMemoryFinding] = []

    if oom_events:
        findings.append(
            _finding(
                "kernel_oom_kill",
                "critical",
                98,
                "Recent kernel evidence contains OOM kill activity.",
                oom_events[:5],
                (
                    "Identify the victim process, owning service or pod, "
                    "allocation context, and whether the OOM was host-wide or "
                    "cgroup-limited."
                ),
            )
        )

    cgroup_oom_count = int(cgroup_memory.get("event_oom", 0) or 0)
    cgroup_oom_kill_count = int(cgroup_memory.get("event_oom_kill", 0) or 0)
    if cgroup_oom_count or cgroup_oom_kill_count:
        findings.append(
            _finding(
                "cgroup_memory_oom",
                "critical",
                96,
                (
                    "The selected process cgroup records memory OOM or "
                    "OOM-kill events."
                ),
                [
                    f"memory.events oom={cgroup_oom_count}",
                    f"memory.events oom_kill={cgroup_oom_kill_count}",
                ],
                (
                    "Compare memory.current, memory.max, workload requests "
                    "and limits, and container restart timing."
                ),
            )
        )

    active_swap = (swap_in or 0) > 0 or (swap_out or 0) > 0
    if active_swap:
        findings.append(
            _finding(
                "active_swap_pressure",
                "warning",
                92,
                (
                    f"Active swap movement detected "
                    f"(si={swap_in or 0}, so={swap_out or 0})."
                ),
                [vmstat_result.get("output", "")],
                (
                    "Correlate swap activity with memory availability, PSI, "
                    "top memory consumers, and workload latency."
                ),
            )
        )

    if available_percent is not None and available_percent <= 10:
        severity = _severity_for_available(available_percent)
        findings.append(
            _finding(
                "low_available_memory",
                severity,
                90,
                f"MemAvailable is {available_percent:.1f}% of MemTotal.",
                [
                    f"MemTotal={mem_total} kB",
                    f"MemAvailable={mem_available} kB",
                ],
                (
                    "Inspect top RSS consumers, page cache behavior, swap, "
                    "kernel reclaim, and cgroup limits before remediation."
                ),
            )
        )

    cgroup_high_count = int(cgroup_memory.get("event_high", 0) or 0)
    if cgroup_high_count:
        findings.append(
            _finding(
                "cgroup_memory_high",
                "warning",
                86,
                "The selected process cgroup crossed memory.high.",
                [f"memory.events high={cgroup_high_count}"],
                (
                    "Inspect whether memory.high throttling aligns with "
                    "application latency, pod limits, or service settings."
                ),
            )
        )

    if mem_total is None or mem_available is None:
        findings.append(
            _finding(
                "insufficient_evidence",
                "warning",
                100,
                "MemTotal or MemAvailable could not be determined.",
                gaps or ["meminfo output was missing or unparseable"],
                "Restore access to /proc/meminfo and repeat the investigation.",
            )
        )

    priority = {
        "kernel_oom_kill": 0,
        "cgroup_memory_oom": 1,
        "active_swap_pressure": 2,
        "low_available_memory": 3,
        "cgroup_memory_high": 4,
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
        diagnosis = "no_immediate_memory_pressure"
        severity = "info"
        confidence = max(60, 95 - (len(gaps) * 8))
        summary = (
            "No immediate OOM, active swap, low availability, or cgroup "
            "memory pressure was identified."
        )

    if gaps and diagnosis != "insufficient_evidence":
        confidence = max(50, confidence - min(20, len(gaps) * 4))

    return LinuxMemoryInvestigation(
        status="diagnosed",
        hostname=evidence.get("host", "unknown"),
        platform=evidence.get("platform", "unknown"),
        pid=evidence.get("pid"),
        primary_diagnosis=diagnosis,
        severity=severity,
        confidence=confidence,
        summary=summary,
        mem_total_kb=mem_total,
        mem_available_kb=mem_available,
        mem_available_percent=available_percent,
        swap_total_kb=swap_total,
        swap_free_kb=swap_free,
        swap_used_percent=swap_used_percent,
        swap_in_per_second=swap_in,
        swap_out_per_second=swap_out,
        cgroup_memory=cgroup_memory,
        oom_events=oom_events,
        top_memory_processes=top_memory_processes,
        findings=findings,
        evidence_gaps=gaps,
        raw_evidence=evidence,
    )
