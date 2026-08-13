from __future__ import annotations

from app.config.settings import settings
from app.memory.incident_history.store_linux_incident import (
    store_linux_host_incident,
)
from app.orchestration.linux_boot_kernel_workflow import (
    run_linux_boot_kernel_workflow,
)
from app.orchestration.linux_cpu_workflow import run_linux_cpu_workflow
from app.orchestration.linux_disk_workflow import run_linux_disk_workflow
from app.orchestration.linux_memory_workflow import run_linux_memory_workflow
from app.orchestration.linux_network_workflow import run_linux_network_workflow
from app.orchestration.linux_service_workflow import run_linux_service_workflow
from app.schemas.linux import (
    LinuxHostDomainSummary,
    LinuxHostFinding,
    LinuxHostInvestigation,
)


SEVERITY_RANK = {
    "critical": 4,
    "warning": 3,
    "info": 2,
    "unknown": 1,
}


def _domain_summary(domain: str, investigation) -> LinuxHostDomainSummary:
    return LinuxHostDomainSummary(
        domain=domain,
        primary_diagnosis=investigation.primary_diagnosis,
        severity=investigation.severity,
        confidence=investigation.confidence,
        summary=investigation.summary,
        findings=[finding.code for finding in investigation.findings],
        evidence_gaps=investigation.evidence_gaps,
    )


def _finding_for_summary(summary: LinuxHostDomainSummary) -> LinuxHostFinding:
    return LinuxHostFinding(
        code=f"{summary.domain}_{summary.primary_diagnosis}",
        severity=summary.severity,
        confidence=summary.confidence,
        summary=f"{summary.domain}: {summary.summary}",
        evidence=summary.findings[:5],
        next=_next_step(summary.domain, summary.primary_diagnosis),
        next_explanation=_next_explanation(summary.domain),
    )


def _next_step(domain: str, diagnosis: str) -> str:
    if domain == "disk":
        return (
            "Use the disk finding to decide whether the next check is "
            "capacity, inodes, LVM, multipath, NFS, read-only state, or I/O."
        )
    if domain == "memory":
        return (
            "Identify whether memory pressure is host-wide, process-specific, "
            "or cgroup-limited before killing or restarting anything."
        )
    if domain == "cpu":
        return (
            "Separate runnable CPU pressure from D-state, I/O wait, and steal "
            "time before blaming application code."
        )
    if domain == "network":
        return (
            "Confirm NIC carrier, errors, routes, resolver state, and cloud "
            "attachment before changing application settings."
        )
    if domain == "boot":
        return (
            "Preserve previous-boot/kernel evidence and confirm kdump, grubby, "
            "and boot arguments before changing kernels."
        )
    if domain == "service":
        return (
            "Inspect the first systemd/journal failure and restart policy "
            "before repeatedly restarting the service."
        )
    return f"Continue focused investigation for {diagnosis}."


def _next_explanation(domain: str) -> str:
    return {
        "disk": (
            "Disk-looking incidents often start below the filesystem: LVM, "
            "multipath, NFS, read-only state, or latency can be causal."
        ),
        "memory": (
            "Memory failures must distinguish host pressure from cgroup limits "
            "and kernel OOM evidence."
        ),
        "cpu": (
            "High load can be runnable CPU work or blocked kernel I/O; those "
            "need different fixes."
        ),
        "network": (
            "Network symptoms can be link, routing, resolver, firewall, or "
            "cloud attachment problems."
        ),
        "boot": (
            "Boot and kernel evidence can disappear after reboot unless the "
            "previous journal and crash data are preserved."
        ),
        "service": (
            "Systemd restart loops often hide the first failure; repeated "
            "restarts usually destroy useful timing context."
        ),
    }.get(domain, "")


def _rank(summary: LinuxHostDomainSummary) -> tuple[int, int]:
    return (
        SEVERITY_RANK.get(summary.severity, 0),
        summary.confidence,
    )


def run_linux_host_workflow(
    scan_path: str = "/",
    iface: str | None = None,
    pid: int | None = None,
    service: str | None = None,
    top: int = 10,
    recent_minutes: int = 60,
    large_size_mb: int = 1024,
    persist: bool | None = None,
) -> tuple[LinuxHostInvestigation, str | None]:
    """
    Correlate existing Linux domain investigations into one host diagnosis.
    """

    disk, _ = run_linux_disk_workflow(
        scan_path=scan_path,
        top=top,
        recent_minutes=recent_minutes,
        large_size_mb=large_size_mb,
        persist=False,
    )
    memory, _ = run_linux_memory_workflow(
        pid=pid,
        top=top,
        recent_minutes=recent_minutes,
        persist=False,
    )
    cpu, _ = run_linux_cpu_workflow(top=top, persist=False)
    network, _ = run_linux_network_workflow(iface=iface, persist=False)
    boot, _ = run_linux_boot_kernel_workflow(
        recent_minutes=recent_minutes,
        persist=False,
    )

    summaries = [
        _domain_summary("disk", disk),
        _domain_summary("memory", memory),
        _domain_summary("cpu", cpu),
        _domain_summary("network", network),
        _domain_summary("boot", boot),
    ]

    if service:
        service_investigation, _ = run_linux_service_workflow(
            service=service,
            persist=False,
        )
        summaries.append(_domain_summary("service", service_investigation))

    actionable = [
        summary
        for summary in summaries
        if summary.primary_diagnosis
        not in {
            "no_immediate_disk_pressure",
            "no_immediate_memory_pressure",
            "no_immediate_cpu_pressure",
            "no_immediate_network_issue",
            "no_immediate_service_issue",
            "no_immediate_boot_kernel_issue",
        }
    ]
    ranked = sorted(actionable or summaries, key=_rank, reverse=True)
    primary = ranked[0]
    findings = [
        _finding_for_summary(summary)
        for summary in ranked
        if summary.severity in {"critical", "warning"}
    ]
    evidence_gaps = [
        f"{summary.domain}: {gap}"
        for summary in summaries
        for gap in summary.evidence_gaps
    ]

    investigation = LinuxHostInvestigation(
        status="diagnosed",
        hostname=getattr(disk, "hostname", "unknown"),
        platform=getattr(disk, "platform", "unknown"),
        primary_diagnosis=f"{primary.domain}_{primary.primary_diagnosis}",
        severity=primary.severity,
        confidence=primary.confidence,
        summary=(
            f"Host-level correlation points first to {primary.domain}: "
            f"{primary.summary}"
        ),
        path=scan_path,
        iface=iface,
        pid=pid,
        service=service,
        domains=summaries,
        findings=findings,
        evidence_gaps=evidence_gaps,
        raw_evidence={
            "domain_order": [summary.domain for summary in ranked],
        },
    )

    should_persist = settings.PERSIST_INCIDENTS if persist is None else persist
    saved_path = None
    if should_persist:
        saved_path = store_linux_host_incident(investigation)

    return investigation, saved_path
