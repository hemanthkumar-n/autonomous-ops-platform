from __future__ import annotations

from uuid import uuid4

from app.investigation.confidence import evaluate_case_confidence
from app.investigation.models import (
    AffectedResource,
    AuditEvent,
    EvidenceGap,
    Hypothesis,
    InvestigationCase,
)
from app.schemas.evidence import EvidenceItem
from app.schemas.linux import LinuxMemoryInvestigation


def _evidence_item(
    *,
    item_id: str,
    title: str,
    summary: str,
    severity: str = "info",
    structured: dict | None = None,
    raw: str | None = None,
    tags: list[str] | None = None,
) -> EvidenceItem:
    return EvidenceItem(
        id=item_id,
        domain="linux",
        source="aop-linux-memory",
        title=title,
        summary=summary,
        severity=severity if severity in {"info", "warning", "critical"} else "info",
        structured=structured or {},
        raw=raw,
        tags=tags or [],
    )


def _positive_counter(value: str | int | None) -> bool:
    try:
        return int(value or 0) > 0
    except (TypeError, ValueError):
        return False


def linux_memory_to_case(
    investigation: LinuxMemoryInvestigation,
    *,
    case_id: str | None = None,
    environment: str = "unknown",
) -> InvestigationCase:
    """Convert an existing deterministic Linux memory result into InvestigationCase."""

    case = InvestigationCase(
        id=case_id or f"aop-{uuid4().hex[:12]}",
        title=f"Linux memory investigation on {investigation.hostname}",
        source="linux-memory-investigator",
        environment=environment,
        severity=investigation.severity,
        symptoms=[investigation.summary],
        affected_resources=[
            AffectedResource(
                domain="linux",
                kind="host",
                name=investigation.hostname,
            )
        ],
        audit_timeline=[
            AuditEvent(
                action="case_created",
                summary="Created canonical investigation case from Linux memory workflow.",
            )
        ],
    )

    if investigation.pid:
        case.affected_resources.append(
            AffectedResource(
                domain="linux",
                kind="process",
                name=str(investigation.pid),
                labels={"pid": str(investigation.pid)},
            )
        )

    if investigation.mem_available_percent is not None:
        severity = "critical" if investigation.mem_available_percent <= 5 else (
            "warning" if investigation.mem_available_percent <= 10 else "info"
        )
        case.evidence.append(
            _evidence_item(
                item_id="linux.memory.mem_available",
                title="Available memory",
                summary=f"MemAvailable is {investigation.mem_available_percent:.1f}%.",
                severity=severity,
                structured={
                    "mem_total_kb": investigation.mem_total_kb,
                    "mem_available_kb": investigation.mem_available_kb,
                    "mem_available_percent": investigation.mem_available_percent,
                },
                tags=["memory", "memavailable"],
            )
        )

    if investigation.swap_used_percent is not None:
        case.evidence.append(
            _evidence_item(
                item_id="linux.memory.swap",
                title="Swap state",
                summary=(
                    f"Swap used is {investigation.swap_used_percent:.1f}% with "
                    f"si={investigation.swap_in_per_second or 0} "
                    f"so={investigation.swap_out_per_second or 0}."
                ),
                severity=(
                    "warning"
                    if (investigation.swap_in_per_second or investigation.swap_out_per_second)
                    else "info"
                ),
                structured={
                    "swap_total_kb": investigation.swap_total_kb,
                    "swap_free_kb": investigation.swap_free_kb,
                    "swap_used_percent": investigation.swap_used_percent,
                    "swap_in_per_second": investigation.swap_in_per_second,
                    "swap_out_per_second": investigation.swap_out_per_second,
                },
                tags=["memory", "swap"],
            )
        )

    if investigation.oom_events:
        case.evidence.append(
            _evidence_item(
                item_id="linux.memory.kernel_oom",
                title="Kernel OOM evidence",
                summary=f"Found {len(investigation.oom_events)} recent OOM event(s).",
                severity="critical",
                raw="\n".join(investigation.oom_events[:10]),
                structured={"event_count": len(investigation.oom_events)},
                tags=["memory", "oom", "kernel"],
            )
        )

    if investigation.cgroup_memory:
        case.evidence.append(
            _evidence_item(
                item_id="linux.memory.cgroup",
                title="Cgroup memory state",
                summary="Cgroup memory evidence was collected for the target workload.",
                severity="warning" if any(
                    _positive_counter(investigation.cgroup_memory.get(key))
                    for key in ("event_oom", "event_oom_kill", "event_high")
                ) else "info",
                structured=dict(investigation.cgroup_memory),
                tags=["memory", "cgroup"],
            )
        )

    for index, finding in enumerate(investigation.findings, start=1):
        evidence_id = f"linux.memory.finding.{index}.{finding.code}"
        case.evidence.append(
            _evidence_item(
                item_id=evidence_id,
                title=finding.code,
                summary=finding.summary,
                severity=finding.severity,
                raw="\n".join(finding.evidence) if finding.evidence else None,
                structured={
                    "source_confidence": finding.confidence,
                    "next": finding.next,
                    "next_explanation": finding.next_explanation,
                },
                tags=["memory", "finding", finding.code],
            )
        )

    for index, gap in enumerate(investigation.evidence_gaps, start=1):
        case.evidence_gaps.append(
            EvidenceGap(
                id=f"linux.memory.gap.{index}",
                description=gap,
                priority="high",
                reason="The source Linux memory investigator reported missing or unavailable evidence.",
                recommended_checks=[
                    "Re-run the Linux memory investigation with required privileges/tools available."
                ],
                blocks_rca=investigation.primary_diagnosis == "insufficient_evidence",
            )
        )

    supporting_ids = [
        item.id
        for item in case.evidence
        if item.id.startswith("linux.memory.finding.")
    ]

    primary = Hypothesis(
        id=f"linux.memory.{investigation.primary_diagnosis}",
        statement=investigation.summary,
        supporting_evidence_ids=supporting_ids,
        required_evidence_ids=supporting_ids.copy(),
        missing_evidence_ids=[gap.id for gap in case.evidence_gaps if gap.blocks_rca],
        why=[finding.summary for finding in investigation.findings],
        notes=[f"Source deterministic confidence: {investigation.confidence}%"],
    )
    case.hypotheses.append(primary)

    evaluate_case_confidence(case)

    # The domain investigator is already deterministic. Preserve its mature
    # confidence when no RCA-blocking gap exists, but never override a blocking gap.
    blocking_gaps = [gap for gap in case.evidence_gaps if gap.blocks_rca]
    if case.decision and not blocking_gaps and investigation.confidence >= 80:
        primary.confidence = max(primary.confidence, investigation.confidence / 100.0)
        primary.status = "supported"
        case.decision.confidence = primary.confidence
        case.decision.leading_hypothesis_id = primary.id
        case.decision.state = "rca_candidate"
        case.decision.rationale.append(
            "The deterministic Linux memory investigator crossed its 80% confidence threshold."
        )

    if case.decision and case.decision.state == "rca_candidate":
        case.root_cause = investigation.primary_diagnosis

    case.recommendations = list(
        dict.fromkeys(finding.next for finding in investigation.findings if finding.next)
    )
    return case
