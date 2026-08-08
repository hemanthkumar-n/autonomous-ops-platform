from __future__ import annotations

from app.schemas.linux import LinuxServiceFinding, LinuxServiceInvestigation


def _result_map(evidence: dict) -> dict[str, dict]:
    return {item["key"]: item for item in evidence.get("results", [])}


def _data_lines(output: str) -> list[str]:
    return [
        line.strip()
        for line in output.splitlines()
        if line.strip() and line.strip() != "-- No entries --"
    ]


def _parse_properties(output: str) -> dict[str, str]:
    properties = {}
    for line in output.splitlines():
        key, separator, value = line.partition("=")
        if separator:
            properties[key] = value
    return properties


def _finding(
    code: str,
    severity: str,
    confidence: int,
    summary: str,
    evidence: list[str],
    next_step: str,
) -> LinuxServiceFinding:
    return LinuxServiceFinding(
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
        "start_limit_hit": (
            "start-limit-hit means systemd stopped trying after repeated "
            "failures. Inspect the first failure and unit policy before "
            "resetting the failed state."
        ),
        "service_failed": (
            "A failed unit is a symptom, not the root cause. Preserve status, "
            "exit code, unit config, and journal context before restarting."
        ),
        "nonzero_exit_status": (
            "ExecMainStatus identifies the process exit code seen by systemd. "
            "Map it to application config, permissions, dependencies, or "
            "runtime errors."
        ),
        "restart_policy_loop": (
            "Restart= with repeated restarts can hide a crash loop. Compare "
            "NRestarts, journal timing, and ExecMainStatus before intervention."
        ),
        "journal_error_evidence": (
            "Recent warning/error journal lines often contain the actual "
            "reason systemd or the service rejected startup."
        ),
        "insufficient_evidence": (
            "AOP needs systemctl show/status and journal evidence to diagnose "
            "a service failure without guessing."
        ),
    }
    return explanations.get(code, "")


def analyze_service_evidence(evidence: dict) -> LinuxServiceInvestigation:
    """
    Convert one service's systemd evidence into deterministic diagnosis.
    """

    service = evidence.get("service", "unknown")
    if evidence.get("status") != "collected":
        return LinuxServiceInvestigation(
            status="unsupported",
            hostname=evidence.get("host", "unknown"),
            platform=evidence.get("platform", "unknown"),
            service=service,
            primary_diagnosis="unsupported_platform",
            severity="info",
            confidence=100,
            summary=evidence.get(
                "message",
                "Linux service evidence is unavailable.",
            ),
            raw_evidence=evidence,
        )

    results = _result_map(evidence)
    gaps = [
        f"{item['label']}: {item['status']}"
        for item in evidence.get("results", [])
        if item.get("status") != "ok"
    ]
    properties_result = results.get("properties", {})
    journal_result = results.get("journal", {})
    properties = (
        _parse_properties(properties_result.get("output", ""))
        if properties_result.get("status") == "ok"
        else {}
    )
    journal_errors = (
        _data_lines(journal_result.get("output", ""))
        if journal_result.get("status") == "ok"
        else []
    )

    findings: list[LinuxServiceFinding] = []
    result = properties.get("Result", "")
    active_state = properties.get("ActiveState", "")
    exec_status = properties.get("ExecMainStatus", "")
    restart = properties.get("Restart", "")
    restarts = int(properties.get("NRestarts", "0") or 0)

    if result == "start-limit-hit":
        findings.append(
            _finding(
                "start_limit_hit",
                "critical",
                97,
                f"{service} hit the systemd start limit.",
                [f"Result={result}", f"NRestarts={restarts}"],
                "Inspect the earliest failure, unit policy, and recent journal before resetting failed state.",
            )
        )

    if active_state == "failed" or result in {"exit-code", "signal", "core-dump"}:
        findings.append(
            _finding(
                "service_failed",
                "critical",
                94,
                f"{service} is failed or exited abnormally.",
                [
                    f"ActiveState={active_state}",
                    f"Result={result}",
                ],
                "Inspect systemctl status, ExecMainStatus, unit config, and journal context before restart.",
            )
        )

    if exec_status and exec_status not in {"0", ""}:
        findings.append(
            _finding(
                "nonzero_exit_status",
                "warning",
                90,
                f"{service} exited with status {exec_status}.",
                [f"ExecMainStatus={exec_status}"],
                "Map the exit code to service docs, config, permissions, or dependency errors.",
            )
        )

    if restart not in {"", "no"} and restarts > 0:
        findings.append(
            _finding(
                "restart_policy_loop",
                "warning",
                86,
                f"{service} has restart policy {restart} and {restarts} restart(s).",
                [f"Restart={restart}", f"NRestarts={restarts}"],
                "Compare restart timing with logs and dependencies before changing restart policy.",
            )
        )

    if journal_errors:
        findings.append(
            _finding(
                "journal_error_evidence",
                "warning",
                80,
                f"{len(journal_errors)} recent warning/error journal line(s) found.",
                journal_errors[:5],
                "Read the earliest relevant journal error and correlate with unit config and exit status.",
            )
        )

    if not properties:
        findings.append(
            _finding(
                "insufficient_evidence",
                "warning",
                100,
                "systemctl show properties could not be parsed.",
                gaps or ["systemctl show output missing"],
                "Restore access to systemctl show/status evidence and repeat the investigation.",
            )
        )

    priority = {
        "start_limit_hit": 0,
        "service_failed": 1,
        "nonzero_exit_status": 2,
        "restart_policy_loop": 3,
        "journal_error_evidence": 4,
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
        diagnosis = "no_immediate_service_failure"
        severity = "info"
        confidence = max(60, 95 - (len(gaps) * 8))
        summary = (
            "No immediate failed state, restart loop, non-zero exit, or "
            "recent service journal error was identified."
        )

    if gaps and diagnosis != "insufficient_evidence":
        confidence = max(50, confidence - min(20, len(gaps) * 4))

    return LinuxServiceInvestigation(
        status="diagnosed",
        hostname=evidence.get("host", "unknown"),
        platform=evidence.get("platform", "unknown"),
        service=service,
        primary_diagnosis=diagnosis,
        severity=severity,
        confidence=confidence,
        summary=summary,
        unit_properties=properties,
        journal_errors=journal_errors,
        findings=findings,
        evidence_gaps=gaps,
        raw_evidence=evidence,
    )
