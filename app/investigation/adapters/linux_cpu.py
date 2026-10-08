from __future__ import annotations

from app.schemas.evidence import EvidenceItem
from app.schemas.linux import LinuxCpuInvestigation


def linux_cpu_evidence(investigation: LinuxCpuInvestigation) -> list[EvidenceItem]:
    """Expose observed CPU signals and findings to the canonical investigation case."""

    evidence: list[EvidenceItem] = []
    if investigation.load_average and investigation.cpu_count is not None:
        evidence.append(
            EvidenceItem(
                id="linux.cpu.load",
                domain="linux",
                source="aop-linux-cpu",
                title="Load and runnable tasks",
                summary=(
                    f"Load averages {investigation.load_average} on "
                    f"{investigation.cpu_count} CPU(s)."
                ),
                structured={
                    "load_average": investigation.load_average,
                    "cpu_count": investigation.cpu_count,
                    "running_tasks": investigation.running_tasks,
                    "total_tasks": investigation.total_tasks,
                    "process_states": investigation.process_states,
                },
                tags=["cpu", "load", "scheduler"],
            )
        )

    if investigation.vmstat_cpu:
        command = next(
            (
                item.get("command")
                for item in investigation.raw_evidence.get("results", [])
                if item.get("key") == "vmstat" and item.get("status") == "ok"
            ),
            None,
        )
        evidence.append(
            EvidenceItem(
                id="linux.cpu.vmstat",
                domain="linux",
                source="aop-linux-cpu",
                title="CPU time sample",
                summary=f"vmstat CPU percentages: {investigation.vmstat_cpu}.",
                command=command,
                structured=dict(investigation.vmstat_cpu),
                tags=["cpu", "vmstat"],
            )
        )

    for resource in ("cpu", "io"):
        pressure = investigation.pressure.get(resource)
        if pressure is None:
            continue
        evidence.append(
            EvidenceItem(
                id=f"linux.cpu.psi.{resource}",
                domain="linux",
                source="aop-linux-cpu",
                title=f"{resource.upper()} pressure",
                summary=f"{resource.upper()} pressure sample was collected.",
                structured=pressure.model_dump(exclude_none=True),
                tags=["cpu", "psi", resource],
            )
        )

    for finding in investigation.findings:
        evidence.append(
            EvidenceItem(
                id=f"linux.cpu.finding.{finding.code}",
                domain="linux",
                source="aop-linux-cpu",
                title=finding.code,
                summary=finding.summary,
                severity=(
                    finding.severity
                    if finding.severity in {"info", "warning", "critical"}
                    else "info"
                ),
                raw="\n".join(finding.evidence) if finding.evidence else None,
                structured={
                    "source_confidence": finding.confidence,
                    "next": finding.next,
                    "next_explanation": finding.next_explanation,
                },
                tags=["cpu", "finding", finding.code],
            )
        )

    return evidence
