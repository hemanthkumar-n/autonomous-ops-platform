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
    r"scsi.*error|read-only|nfs: server .*not responding|"
    r"task .*blocked|multipath.*failed)",
    re.IGNORECASE,
)
_SIZE_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)(?P<unit>[kmgtp])", re.I)


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


def _parse_size_to_gib(value: str) -> float | None:
    match = _SIZE_PATTERN.search(value.strip())
    if not match:
        return None

    number = float(match.group("value"))
    unit = match.group("unit").lower()
    multipliers = {
        "k": 1 / (1024 * 1024),
        "m": 1 / 1024,
        "g": 1,
        "t": 1024,
        "p": 1024 * 1024,
    }
    return number * multipliers[unit]


def _lowest_vg_free_percent(lines: list[str]) -> float | None:
    lowest: float | None = None
    for line in lines:
        fields = line.split()
        if len(fields) < 3:
            continue
        total = _parse_size_to_gib(fields[1])
        free = _parse_size_to_gib(fields[2])
        if total is None or free is None or total <= 0:
            continue
        percent = (free / total) * 100
        lowest = percent if lowest is None else min(lowest, percent)
    return lowest


def _thin_pool_high_watermark(lines: list[str]) -> float | None:
    highest: float | None = None
    for line in lines:
        for token in line.split():
            try:
                value = float(token)
            except ValueError:
                continue
            if 0 <= value <= 100:
                highest = value if highest is None else max(highest, value)
    return highest


def _parse_iostat_sample(lines: list[str]) -> dict[str, str | float]:
    headers: list[str] = []
    best: dict[str, str | float] = {}
    best_util = 0.0

    for line in lines:
        parts = line.split()
        if not parts:
            continue
        if parts[0].lower() == "device":
            headers = [item.lower() for item in parts]
            continue
        if not headers or len(parts) < len(headers):
            continue
        row = dict(zip(headers, parts, strict=False))
        try:
            util = float(row.get("%util", "0"))
        except ValueError:
            continue
        if util >= best_util:
            best_util = util
            best = {
                "device": row.get("device", ""),
                "await_ms": _float_or_zero(row.get("await", "0")),
                "read_await_ms": _float_or_zero(row.get("r_await", "0")),
                "write_await_ms": _float_or_zero(row.get("w_await", "0")),
                "util_percent": util,
            }

    return best


def _float_or_zero(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


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
        next_explanation=_next_explanation(code),
    )


def _next_explanation(code: str) -> str:
    explanations = {
        "read_only_filesystem": (
            "A read-only remount usually means the kernel or storage layer "
            "protected the filesystem after an error. Cleanup is not the "
            "first action; inspect mount options and kernel storage logs."
        ),
        "storage_io_errors": (
            "Filesystem and block-device errors can cause latency, failed "
            "writes, or read-only remounts even when capacity is available. "
            "Correlate kernel messages with the affected device and storage "
            "backend."
        ),
        "nfs_mount_risk": (
            "NFS symptoms can look like application hangs, D-state load, or "
            "slow writes. Confirm server reachability, mount options, and RPC "
            "latency before blaming local disk capacity."
        ),
        "multipath_path_loss": (
            "Multipath path loss means the host may be surviving on fewer SAN "
            "paths or queueing I/O. Check HBA, fabric, array, and path policy "
            "before restarting workloads."
        ),
        "lvm_low_free_space": (
            "Low VG free space is a planning and recovery constraint. It can "
            "block snapshot growth, LV extension, and emergency expansion "
            "even when the mounted filesystem is not full yet."
        ),
        "lvm_thin_pool_pressure": (
            "Thin-pool data or metadata pressure can fail writes suddenly. "
            "Treat pool usage separately from filesystem usage and expand or "
            "clean with a controlled plan."
        ),
        "block_device_read_only": (
            "A read-only block device points below the filesystem layer. "
            "Check device state, hypervisor/cloud volume state, SAN paths, "
            "and kernel errors before remounting."
        ),
        "storage_latency_pressure": (
            "High await or utilization means applications may be blocked on "
            "I/O even when free space is available. Correlate with D-state "
            "tasks, filesystem logs, and storage backend metrics."
        ),
        "inode_exhaustion": (
            "Inode exhaustion can produce 'No space left on device' even "
            "when byte capacity is still available. The next check should "
            "look for directories creating many small files."
        ),
        "filesystem_capacity_exhaustion": (
            "High byte usage must be explained before cleanup. Compare "
            "visible directory growth, recent large files, deleted-open "
            "files, snapshots, and retention expectations."
        ),
        "deleted_open_files": (
            "Deleted files can keep consuming disk blocks while a process "
            "still has them open. Space is released only when the process "
            "closes the file, so identify the owner before restarting."
        ),
        "rapid_file_growth": (
            "Recent large files show what changed near the incident window. "
            "Map the file to the writer, service, deployment, rotation, or "
            "backup behavior before remediation."
        ),
        "insufficient_evidence": (
            "AOP cannot make a reliable disk diagnosis without filesystem "
            "and mount evidence. Restore read access to the missing command "
            "outputs and repeat the investigation."
        ),
    }
    return explanations.get(code, "")


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
    block_devices_result = results.get("block_devices", {})
    lvm_pvs_result = results.get("lvm_pvs", {})
    lvm_vgs_result = results.get("lvm_vgs", {})
    lvm_lvs_result = results.get("lvm_lvs", {})
    multipath_result = results.get("multipath", {})
    nfs_mountstats_result = results.get("nfs_mountstats", {})
    io_stats_result = results.get("io_stats", {})

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
    block_devices = _data_lines(block_devices_result.get("output", ""), "name")
    lvm_physical_volumes = _data_lines(lvm_pvs_result.get("output", ""))
    lvm_volume_groups = _data_lines(lvm_vgs_result.get("output", ""))
    lvm_logical_volumes = _data_lines(lvm_lvs_result.get("output", ""))
    multipath_devices = _data_lines(multipath_result.get("output", ""))
    nfs_mounts = [
        line
        for line in _data_lines(nfs_mountstats_result.get("output", ""))
        if " type nfs" in line.lower() or " type nfs4" in line.lower()
    ]
    io_sample = _parse_iostat_sample(
        _data_lines(io_stats_result.get("output", ""))
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
    fs_type = (filesystem_type or "").lower()
    nfs_like = fs_type in {"nfs", "nfs4"} or bool(nfs_mounts)
    multipath_loss = any(
        any(token in line.lower() for token in ("failed", "faulty", "undef"))
        for line in multipath_devices
    )
    block_read_only = any(
        line.split()[-2:-1] == ["1"] or line.endswith(" 1")
        for line in block_devices
        if line.split()
    )
    vg_free_percent = _lowest_vg_free_percent(lvm_volume_groups)
    thin_pool_percent = _thin_pool_high_watermark(lvm_logical_volumes)
    util_percent = float(io_sample.get("util_percent", 0.0) or 0.0)
    await_ms = max(
        float(io_sample.get("await_ms", 0.0) or 0.0),
        float(io_sample.get("read_await_ms", 0.0) or 0.0),
        float(io_sample.get("write_await_ms", 0.0) or 0.0),
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

    if block_read_only:
        findings.append(
            _finding(
                "block_device_read_only",
                "critical",
                94,
                "One or more block devices report read-only state.",
                block_devices[:5],
                (
                    "Identify the read-only device and correlate with cloud, "
                    "SAN, hypervisor, kernel, and filesystem state."
                ),
            )
        )

    non_read_only_errors = [
        line
        for line in kernel_storage_errors
        if "read-only" not in line.lower()
        and not (nfs_like and "nfs" in line.lower())
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

    if multipath_loss:
        findings.append(
            _finding(
                "multipath_path_loss",
                "critical",
                94,
                "Multipath evidence shows failed, faulty, or undefined paths.",
                multipath_devices[:8],
                (
                    "Check HBA, fabric, array, cloud storage attachment, and "
                    "multipath policy before moving or restarting workloads."
                ),
            )
        )

    if nfs_like:
        risky_options = [
            option
            for option in mount_options
            if option in {"soft", "intr"} or option.startswith("timeo=")
        ]
        nfs_errors = [
            line
            for line in kernel_storage_errors
            if "nfs" in line.lower()
        ]
        if risky_options or nfs_errors:
            nfs_evidence = [
                *(
                    [f"mount options: {','.join(risky_options)}"]
                    if risky_options
                    else []
                ),
                *nfs_errors[:4],
            ]
            findings.append(
                _finding(
                    "nfs_mount_risk",
                    "warning" if not nfs_errors else "critical",
                    90 if not nfs_errors else 96,
                    "NFS evidence may explain application I/O hangs or write failures.",
                    nfs_evidence,
                    (
                        "Check NFS server health, network path, mount options, "
                        "RPC latency, and client kernel messages."
                    ),
                )
            )

    if vg_free_percent is not None and vg_free_percent <= 5:
        findings.append(
            _finding(
                "lvm_low_free_space",
                "warning",
                88,
                f"Lowest LVM volume-group free space is {vg_free_percent:.1f}%.",
                lvm_volume_groups[:5],
                (
                    "Review VG free space before planning snapshots, LV "
                    "extension, filesystem growth, or emergency remediation."
                ),
            )
        )

    if thin_pool_percent is not None and thin_pool_percent >= 85:
        findings.append(
            _finding(
                "lvm_thin_pool_pressure",
                "critical" if thin_pool_percent >= 95 else "warning",
                86,
                f"LVM thin-pool usage signal is {thin_pool_percent:.1f}%.",
                lvm_logical_volumes[:5],
                (
                    "Check thin-pool data and metadata usage before writes "
                    "fail or snapshots exhaust the pool."
                ),
            )
        )

    if util_percent >= 90 or await_ms >= 100:
        findings.append(
            _finding(
                "storage_latency_pressure",
                "warning",
                84,
                (
                    f"iostat shows util={util_percent:.1f}% and "
                    f"await={await_ms:.1f}ms on {io_sample.get('device', 'device')}."
                ),
                [
                    " ".join(f"{key}={value}" for key, value in io_sample.items())
                ],
                (
                    "Correlate I/O wait, D-state tasks, filesystem logs, and "
                    "backend volume metrics before blaming CPU or application code."
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
        "block_device_read_only": 1,
        "storage_io_errors": 2,
        "multipath_path_loss": 3,
        "nfs_mount_risk": 4,
        "lvm_thin_pool_pressure": 5,
        "inode_exhaustion": 6,
        "filesystem_capacity_exhaustion": 7,
        "storage_latency_pressure": 8,
        "lvm_low_free_space": 9,
        "deleted_open_files": 10,
        "rapid_file_growth": 11,
        "insufficient_evidence": 12,
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
        block_devices=block_devices,
        lvm_physical_volumes=lvm_physical_volumes,
        lvm_volume_groups=lvm_volume_groups,
        lvm_logical_volumes=lvm_logical_volumes,
        multipath_devices=multipath_devices,
        nfs_mounts=nfs_mounts,
        io_sample=io_sample,
        largest_paths=largest_paths,
        recent_large_files=recent_large_files,
        deleted_open_files=deleted_open_files,
        kernel_storage_errors=kernel_storage_errors,
        findings=findings,
        evidence_gaps=gaps,
        raw_evidence=evidence,
    )
