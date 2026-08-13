from __future__ import annotations

from .models import Hypothesis, InvestigationCase


def _evidence_summary(case: InvestigationCase, evidence_id: str) -> str:
    item = case.evidence_by_id().get(evidence_id)
    if item is None:
        return f"missing evidence reference: {evidence_id}"
    return item.summary


def _leading_hypothesis(case: InvestigationCase) -> Hypothesis | None:
    if case.decision and case.decision.leading_hypothesis_id:
        selected = case.hypothesis_by_id(case.decision.leading_hypothesis_id)
        if selected is not None:
            return selected
    if not case.hypotheses:
        return None
    return max(case.hypotheses, key=lambda item: item.confidence)


def build_reasoning_summary(
    case: InvestigationCase,
    hypothesis: Hypothesis | None = None,
) -> dict[str, object]:
    """Build machine-readable why / why-not reasoning from verified evidence.

    Callers may pass a specific hypothesis. If omitted, the current leading
    hypothesis is selected from the case decision, falling back to the highest
    confidence hypothesis. This keeps CLI/report consumers simple while still
    allowing hypothesis-specific reasoning in tests and orchestration.
    """

    hypothesis = hypothesis or _leading_hypothesis(case)
    if hypothesis is None:
        return {
            "hypothesis_id": None,
            "statement": "",
            "status": "unknown",
            "confidence": 0.0,
            "why": [],
            "why_not": [],
            "missing_evidence": [gap.id for gap in case.evidence_gaps],
            "evidence_complete": not case.evidence_gaps,
        }

    supporting = [
        _evidence_summary(case, evidence_id)
        for evidence_id in hypothesis.supporting_evidence_ids
    ]
    contradicting = [
        _evidence_summary(case, evidence_id)
        for evidence_id in hypothesis.contradicting_evidence_ids
    ]

    missing = list(
        dict.fromkeys(
            hypothesis.missing_evidence_ids
            + [gap.id for gap in case.evidence_gaps if gap.blocks_rca]
        )
    )

    return {
        "hypothesis_id": hypothesis.id,
        "statement": hypothesis.statement,
        "status": hypothesis.status,
        "confidence": hypothesis.confidence,
        "why": list(dict.fromkeys(hypothesis.why + supporting)),
        "why_not": list(dict.fromkeys(hypothesis.why_not + contradicting)),
        "missing_evidence": missing,
        "evidence_complete": not missing,
    }
