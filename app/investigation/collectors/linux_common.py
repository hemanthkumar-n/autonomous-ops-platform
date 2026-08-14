from __future__ import annotations

from app.investigation.autonomous_loop import EvidenceCollectionResult
from app.investigation.evidence_planner import EvidenceRequest
from app.investigation.models import AffectedResource, InvestigationCase
from app.schemas.evidence import EvidenceItem


def leading_hypothesis_id(case: InvestigationCase, request: EvidenceRequest) -> str | None:
    configured = request.metadata.get("hypothesis_id")
    if configured:
        return configured
    if case.decision and case.decision.leading_hypothesis_id:
        return case.decision.leading_hypothesis_id
    if case.hypotheses:
        return case.hypotheses[0].id
    return None


def normalize_linux_investigation(
    *,
    request: EvidenceRequest,
    case: InvestigationCase,
    domain: str,
    hostname: str,
    primary_diagnosis: str,
    confidence: int,
    summary: str,
    findings: list,
    evidence_gaps: list[str],
    structured: dict[str, object] | None = None,
    resources: list[AffectedResource] | None = None,
) -> EvidenceCollectionResult:
    evidence: list[EvidenceItem] = []
    finding_ids: list[str] = []

    evidence.append(
        EvidenceItem(
            id=f"linux.{domain}.summary",
            domain="linux",
            source=f"aop-linux-{domain}",
            title=f"Linux {domain} investigation",
            summary=summary,
            severity="info",
            structured={
                "hostname": hostname,
                "primary_diagnosis": primary_diagnosis,
                "source_confidence": confidence,
                **(structured or {}),
            },
            tags=["linux", domain, primary_diagnosis],
        )
    )

    for index, finding in enumerate(findings, start=1):
        evidence_id = f"linux.{domain}.finding.{index}.{finding.code}"
        finding_ids.append(evidence_id)
        evidence.append(
            EvidenceItem(
                id=evidence_id,
                domain="linux",
                source=f"aop-linux-{domain}",
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
                tags=["linux", domain, "finding", finding.code],
            )
        )

    hypothesis_id = leading_hypothesis_id(case, request)
    diagnosed = primary_diagnosis != "insufficient_evidence"
    supporting: dict[str, list[str]] = {}
    reasons: dict[str, list[str]] = {}
    if hypothesis_id and diagnosed:
        supporting[hypothesis_id] = finding_ids or [evidence[0].id]
        reasons[hypothesis_id] = [finding.summary for finding in findings] or [summary]

    resolved = [request.gap_id] if request.gap_id and diagnosed else []
    notes = [
        f"linux_{domain}_primary_diagnosis={primary_diagnosis}",
        f"linux_{domain}_source_confidence={confidence}",
    ]
    if evidence_gaps:
        notes.append(f"linux_{domain}_evidence_gaps={len(evidence_gaps)}")

    return EvidenceCollectionResult(
        request_id=request.id,
        evidence=evidence,
        supporting_evidence=supporting,
        supporting_reasons=reasons,
        resolved_gap_ids=resolved,
        affected_resources=resources or [
            AffectedResource(domain="linux", kind="host", name=hostname)
        ],
        notes=notes,
    )
