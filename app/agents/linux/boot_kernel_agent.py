from __future__ import annotations

from app.schemas.linux import (
    LinuxBootKernelFinding,
    LinuxBootKernelInvestigation,
)


PANIC_PATTERNS = (
    "kernel panic",
    "panic:",
    "Oops:",
    "BUG:",
    "Call Trace",
)
OOM_PATTERNS = (
    "Out of memory",
    "Killed process",
    "oom-kill",
    "Memory cgroup out of memory",
)
HUNG_PATTERNS = (
    "blocked for more than",
    "hung task",
    "task .* blocked",
)
STORAGE_PATTERNS = (
    "I/O error",
    "EXT4-fs error",
    "XFS",
    "Buffer I/O error",
    "blk_update_request",
    "nvme",
    "scsi",
    "reset",
    "read-only",
)


def _result_map(evidence: dict) -> dict[str, dict]:
    return {item["key"]: item for item in evidence.get("results", [])}


def _output(results: dict[str, dict], key: str) -> str:
    item = results.get(key, {})
    return item.get("output", "") if item.get("status") == "ok" else ""


def _data_lines(output: str) -> list[str]:
    return [
        line.strip()
        for line in output.splitlines()
        if line.strip() and line.strip() != "-- No entries --"
    ]


def _contains_any(lines: list[str], patterns: tuple[str, ...]) -> list[str]:
    matches = []
    lowered_patterns = [pattern.lower() for pattern in patterns]
    for line in lines:
        lower_line = line.lower()
        if any(pattern.lower() in lower_line for pattern in lowered_patterns):
            matches.append(line)
    return matches


def _finding(
    code: str,
    severity: str,
    confidence: int,
    summary: str,
    evidence: list[str],
    next_step: str,
) -> LinuxBootKernelFinding:
    return LinuxBootKernelFinding(
        code=code,
        severity=severity,
        confidence=confidence,
        summary=summary,
        evidence=evidence[:8],
        next=next_step,
        next_explanation=_next_explanation(code),
    )


def _next_explanation(code: str) -> str:
    explanations = {
        "previous_boot_panic": (
            "Previous-boot panic evidence is stronger than current clean logs "
            "after a reboot. Preserve it before rotating or truncating journals."
        ),
        "current_kernel_panic": (
            "Current kernel panic/oops evidence can point to driver, hardware, "
            "filesystem, or kernel regressions and should be preserved before reboot."
        ),
        "kernel_oom_or_reboot": (
            "OOM evidence near boot/reboot time separates memory exhaustion "
            "from application crash, power loss, and planned maintenance."
        ),
        "hung_task_or_storage_wait": (
            "Hung tasks and D-state waits usually mean work is blocked inside "
            "the kernel, often on storage, NFS, driver, or filesystem paths."
        ),
        "kernel_storage_error": (
            "Storage and filesystem errors can cause read-only remounts, "
            "D-state tasks, kubelet instability, and data-risk incidents."
        ),
        "kdump_unavailable": (
            "Without kdump, post-panic root cause evidence may be missing. "
            "Do not claim panic root cause without crash capture or logs."
        ),
        "default_kernel_mismatch": (
            "A running/default kernel mismatch may be normal before reboot, "
            "but it matters after patching and when cgroup or driver behavior changed."
        ),
        "risky_boot_args": (
            "Boot arguments affect kernel behavior at next boot. Changes need "
            "rollback kernel, console/rescue access, and a reboot window."
        ),
        "insufficient_evidence": (
            "AOP needs boot history, previous boot logs, current kernel logs, "
            "running kernel, boot args, and grubby context to diagnose safely."
        ),
    }
    return explanations.get(code, "")


def analyze_boot_kernel_evidence(evidence: dict) -> LinuxBootKernelInvestigation:
    """
    Diagnose boot, kernel, panic, kdump, and grubby/default-kernel evidence.
    """

    if evidence.get("status") != "collected":
        return LinuxBootKernelInvestigation(
            status="unsupported",
            hostname=evidence.get("host", "unknown"),
            platform=evidence.get("platform", "unknown"),
            primary_diagnosis="unsupported_platform",
            severity="info",
            confidence=100,
            summary=evidence.get(
                "message",
                "Linux boot/kernel evidence is unavailable.",
            ),
            raw_evidence=evidence,
        )

    results = _result_map(evidence)
    gaps = [
        f"{item['label']}: {item['status']}"
        for item in evidence.get("results", [])
        if item.get("status") not in {"ok", "permission"}
    ]
    running_kernel = _output(results, "running_kernel").strip() or None
    default_kernel = _output(results, "grubby_default").strip() or None
    default_index = _output(results, "grubby_index").strip() or None
    boot_args = _output(results, "boot_args").strip() or None
    kdump_status = _output(results, "kdump_status").strip() or None
    current_kernel_errors = _data_lines(_output(results, "current_kernel_errors"))
    previous_boot_errors = _data_lines(_output(results, "previous_boot_errors"))
    boot_history = _data_lines(_output(results, "boot_history"))

    findings: list[LinuxBootKernelFinding] = []
    previous_panic = _contains_any(previous_boot_errors, PANIC_PATTERNS)
    current_panic = _contains_any(current_kernel_errors, PANIC_PATTERNS)
    oom_lines = _contains_any(
        previous_boot_errors + current_kernel_errors,
        OOM_PATTERNS,
    )
    hung_lines = _contains_any(
        previous_boot_errors + current_kernel_errors,
        HUNG_PATTERNS,
    )
    storage_lines = _contains_any(
        previous_boot_errors + current_kernel_errors,
        STORAGE_PATTERNS,
    )

    if previous_panic:
        findings.append(
            _finding(
                "previous_boot_panic",
                "critical",
                96,
                "Previous boot contains kernel panic/oops evidence.",
                previous_panic,
                "Preserve previous-boot journal, check kdump crash capture, and correlate with hardware, driver, storage, and patch history.",
            )
        )

    if current_panic:
        findings.append(
            _finding(
                "current_kernel_panic",
                "critical",
                94,
                "Current boot contains kernel panic/oops evidence.",
                current_panic,
                "Preserve kernel logs and avoid rebooting before collecting crash, driver, and storage context.",
            )
        )

    if oom_lines:
        findings.append(
            _finding(
                "kernel_oom_or_reboot",
                "critical",
                92,
                "Kernel OOM evidence appears in boot/kernel logs.",
                oom_lines,
                "Correlate OOM timestamp with reboot, service restarts, cgroup limits, and workload memory pressure.",
            )
        )

    if hung_lines:
        findings.append(
            _finding(
                "hung_task_or_storage_wait",
                "warning",
                88,
                "Kernel logs show hung task or blocked-task evidence.",
                hung_lines,
                "Inspect D-state tasks, storage/NFS latency, and kernel stack context before killing processes.",
            )
        )

    if storage_lines:
        findings.append(
            _finding(
                "kernel_storage_error",
                "critical",
                90,
                "Kernel logs show storage or filesystem error evidence.",
                storage_lines,
                "Check filesystem mount state, device health, cloud volume health, and recent storage changes.",
            )
        )

    if kdump_status and "not operational" in kdump_status.lower():
        findings.append(
            _finding(
                "kdump_unavailable",
                "warning",
                85,
                "kdump is not operational.",
                [kdump_status],
                "Enable or repair kdump in a maintenance window so future kernel panics preserve crash evidence.",
            )
        )

    if running_kernel and default_kernel and running_kernel not in default_kernel:
        findings.append(
            _finding(
                "default_kernel_mismatch",
                "info",
                82,
                "Running kernel differs from grubby default kernel.",
                [
                    f"running={running_kernel}",
                    f"default={default_kernel}",
                    f"default_index={default_index or 'unknown'}",
                ],
                "Confirm whether a reboot is pending after patching and keep a known-good rollback kernel.",
            )
        )

    if boot_args:
        risky_args = [
            arg
            for arg in boot_args.split()
            if arg.startswith(("crashkernel=", "systemd.unified_cgroup_hierarchy=", "cgroup_no_v1=", "selinux=", "enforcing="))
        ]
        if risky_args:
            findings.append(
                _finding(
                    "risky_boot_args",
                    "info",
                    78,
                    "Boot arguments include kernel behavior controls.",
                    risky_args,
                    "Validate boot arguments against kubelet/container runtime requirements before changing them.",
                )
            )

    if not findings and gaps:
        findings.append(
            _finding(
                "insufficient_evidence",
                "warning",
                100,
                "Some boot/kernel evidence could not be collected.",
                gaps,
                "Restore access to missing read-only evidence and repeat boot/kernel investigation.",
            )
        )

    priority = {
        "previous_boot_panic": 0,
        "current_kernel_panic": 1,
        "kernel_oom_or_reboot": 2,
        "kernel_storage_error": 3,
        "hung_task_or_storage_wait": 4,
        "kdump_unavailable": 5,
        "default_kernel_mismatch": 6,
        "risky_boot_args": 7,
        "insufficient_evidence": 8,
    }
    findings.sort(key=lambda item: priority[item.code])

    if findings:
        primary = findings[0]
        diagnosis = primary.code
        severity = primary.severity
        confidence = primary.confidence
        summary = primary.summary
    else:
        diagnosis = "no_immediate_boot_kernel_failure"
        severity = "info"
        confidence = 90
        summary = (
            "No immediate panic, OOM, hung-task, storage-error, kdump, or "
            "default-kernel mismatch finding was identified."
        )

    if gaps and diagnosis != "insufficient_evidence":
        confidence = max(50, confidence - min(20, len(gaps) * 3))

    return LinuxBootKernelInvestigation(
        status="diagnosed",
        hostname=evidence.get("host", "unknown"),
        platform=evidence.get("platform", "unknown"),
        primary_diagnosis=diagnosis,
        severity=severity,
        confidence=confidence,
        summary=summary,
        running_kernel=running_kernel,
        default_kernel=default_kernel,
        default_index=default_index,
        boot_args=boot_args,
        kdump_status=kdump_status,
        current_kernel_errors=current_kernel_errors,
        previous_boot_errors=previous_boot_errors,
        boot_history=boot_history,
        findings=findings,
        evidence_gaps=gaps,
        raw_evidence=evidence,
    )
