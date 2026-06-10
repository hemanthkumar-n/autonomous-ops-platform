from __future__ import annotations

import re

from app.schemas.linux import (
    LinuxDiskFinding,
    LinuxDiskInvestigation,
)


_PERCENT_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)%")
_KERNEL_ERROR_PATTERN = re.compile(
    r"(i/o error|buffer i/o|blk_update_request|end_request|"
    r"ext4-fs error|xfs.*corrupt|btrfs.*error|nvme.*reset|"
    r"scsi.*error|read-only)",
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


def _parse_percent(output: str) -> float | None:
    lines = _data_lines(output, "filesystem")
    if not lines:
        return None

    matches = list(_PERCENT_PATTERN.finditer(lines[-1]))
    if not matches:
        return None
    return float(matches[-1].group("value"))


def _parse_mount(
    output: str,
) -> tuple[str | None, str | None, list[str], str | None]:
    lines = _data_lines(output, "source")
    if not lines:
        return None, None, [], None

    fields = lines[-1].split(None, 3)
    if len(fields) < 4:
        return None, None, [], None

    source, filesystem_type, options, mount_point = fields
    return (
        source,
        filesystem_type,
        [item for item in options.split(",") if item],
        mount_point,
    )


def _use_severity(percent: float) -> str:
    if percent >= 95:
        return "critical"
    if percent >= 85:
        return "warning"
    return "info"


def _finding(
    code: str,
    severity: str,
    confidence: int,
    summary: str,
    evidence: list[str],
    next_step: str,
) -> LinuxDiskFinding:
    return LinuxDiskFinding(
        code=code,
        severity=severity,
        confidence=confidence,
        summary=summary,
        evidence=evidence,
        next=next_step,
    )


def analyze_disk_evidence(evidence: dict) -> LinuxDiskInvestigation:
    """
    Convert ordered disk command evidence into deterministic diagnosis.
    """

    if evidence.get("status") != "collected":
        return LinuxDiskInvestigation(
            status="unsupported",
            hostname=evidence.get("host", "unknown"),
            path=evidence.get("path", "/"),
            platform=evidence.get("platform", "unknown"),
            primary_diagnosis="unsupported_platform",
            severity="info",
            confidence=100,
            summary=evidence.get(
                "message",
                "Linux disk evidence is unavailable.",
            ),
            raw_evidence=evidence,
        )

    results = _result_map(evidence)
    gaps = [
        f"{item['label']}: {item['status']}"
        for item in evidence.get("results", [])
        if item.get("status") != "ok"
    ]

    filesystem = results.get("filesystem", {})
    inodes = results.get("inodes", {})
    mount = results.get("mount", {})
    directory_usage = results.get("directory_usage", {})
    recent_files = results.get("large_recent_files", {})
    deleted_files = results.get("deleted_open_files", {})
    kernel_errors = results.get("kernel_storage_errors", {})

    filesystem_percent = (
        _parse_percent(filesystem.get("output", ""))
        if filesystem.get("status") == "ok"
        else None
    )
    inode_percent = (
        _parse_percent(inodes.get("output", ""))
        if inodes.get("status") == "ok"
        else None
    )
    source, filesystem_type, mount_options, mount_point = _parse_mount(
        mount.get("output", "")
        if mount.get("status") == "ok"
        else ""
    )

    largest_paths = _data_lines(directory_usage.get("output", ""))
    recent_large_files = _data_lines(recent_files.get("output", ""))
    deleted_open_files = _data_lines(
        deleted_files.get("output", ""),
        "command",
    )
    kernel_lines = _data_lines(kernel_errors.get("output", ""))
    kernel_storage_errors = [
        line
        for line in kernel_lines
        if line != "-- No entries --"
        and _KERNEL_ERROR_PATTERN.search(line)
    ]

    findings: list[LinuxDiskFinding] = []
    read_only = "ro" in mount_options or any(
        "read-only" in line.lower()
        for line in kernel_storage_errors
    )

    if read_only:
        findings.append(
            _finding(
                "read_only_filesystem",
                "critical",
                98,
                "The selected filesystem is read-only or was remounted read-only.",
                [
                    *(
                        [f"mount options: {','.join(mount_options)}"]
                        if mount_options
                        else []
                    ),
                    *kernel_storage_errors[:3],
                ],
                (
                    "Protect data and inspect kernel storage errors, device "
                    "health, and filesystem state before attempting a remount."
                ),
            )
        )

    non_read_only_errors = [
        line
        for line in kernel_storage_errors
        if "read-only" not in line.lower()
    ]
    if non_read_only_errors:
        findings.append(
            _finding(
                "storage_io_errors",
                "critical",
                95,
                "Recent kernel evidence indicates filesystem or storage errors.",
                non_read_only_errors[:5],
                (
                    "Correlate the affected device and mount with SMART, NVMe, "
                    "SAN, cloud-volume, or filesystem diagnostics."
                ),
            )
        )

    if inode_percent is not None and inode_percent >= 85:
        severity = _use_severity(inode_percent)
        findings.append(
            _finding(
                "inode_exhaustion",
                severity,
                98,
                f"Inode utilization is {inode_percent:.0f}%.",
                [inodes.get("output", "").splitlines()[-1]],
                (
                    "Find directories creating many small files on this "
                    "filesystem; do not assume large files are the cause."
                ),
            )
        )

    if filesystem_percent is not None and filesystem_percent >= 85:
        severity = _use_severity(filesystem_percent)
        findings.append(
            _finding(
                "filesystem_capacity_exhaustion",
                severity,
                97,
                f"Filesystem byte utilization is {filesystem_percent:.0f}%.",
                [filesystem.get("output", "").splitlines()[-1]],
                (
                    "Inspect the largest paths, recent growth, deleted-open "
                    "files, snapshots, and expected retention before cleanup."
                ),
            )
        )

    pressured = filesystem_percent is not None and filesystem_percent >= 80
    if deleted_open_files:
        findings.append(
            _finding(
                "deleted_open_files",
                "warning" if pressured else "info",
                94 if pressured else 80,
                (
                    f"{len(deleted_open_files)} deleted file record(s) remain "
                    "open by running processes."
                ),
                deleted_open_files[:5],
                (
                    "Identify the owning process and service. Plan a controlled "
                    "reload or restart only after checking operational impact."
                ),
            )
        )

    if recent_large_files:
        findings.append(
            _finding(
                "rapid_file_growth",
                "warning" if pressured else "info",
                88 if pressured else 70,
                (
                    f"{len(recent_large_files)} recently changed large file(s) "
                    "were found in the configured window."
                ),
                recent_large_files[:5],
                (
                    "Map the files to their writer, retention policy, rotation "
                    "state, and expected workload before changing them."
                ),
            )
        )

    if filesystem_percent is None:
        findings.append(
            _finding(
                "insufficient_evidence",
                "warning",
                100,
                "Filesystem utilization could not be determined.",
                gaps or ["df output was missing or unparseable"],
                (
                    "Restore access to df/findmnt evidence and repeat the "
                    "read-only investigation."
                ),
            )
        )

    priority = {
        "read_only_filesystem": 0,
        "storage_io_errors": 1,
        "inode_exhaustion": 2,
        "filesystem_capacity_exhaustion": 3,
        "deleted_open_files": 4,
        "rapid_file_growth": 5,
        "insufficient_evidence": 6,
    }
    findings.sort(key=lambda item: priority[item.code])

    if findings:
        primary = findings[0]
        diagnosis = primary.code
        severity = primary.severity
        confidence = primary.confidence
        summary = primary.summary
    else:
        diagnosis = "no_immediate_disk_pressure"
        severity = "info"
        confidence = max(60, 95 - (len(gaps) * 8))
        summary = (
            "No immediate capacity, inode, deleted-file, growth, mount, or "
            "kernel storage problem was identified."
        )

    if gaps and diagnosis != "insufficient_evidence":
        confidence = max(50, confidence - min(20, len(gaps) * 4))

    return LinuxDiskInvestigation(
        status="diagnosed",
        hostname=evidence.get("host", "unknown"),
        path=evidence.get("path", "/"),
        platform=evidence.get("platform", "unknown"),
        primary_diagnosis=diagnosis,
        severity=severity,
        confidence=confidence,
        summary=summary,
        filesystem_use_percent=filesystem_percent,
        inode_use_percent=inode_percent,
        mount_source=source,
        filesystem_type=filesystem_type,
        mount_point=mount_point,
        mount_options=mount_options,
        largest_paths=largest_paths,
        recent_large_files=recent_large_files,
        deleted_open_files=deleted_open_files,
        kernel_storage_errors=kernel_storage_errors,
        findings=findings,
        evidence_gaps=gaps,
        raw_evidence=evidence,
    )
