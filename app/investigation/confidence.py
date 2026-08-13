from __future__ import annotations

from dataclasses import dataclass

from .models import Hypothesis, InvestigationCase, InvestigationDecision


@dataclass(frozen=True, slots=True)
class ConfidencePolicy:
    support_weight: float = 0.55
    contradiction_weight: float = 0.65
    coverage_weight: float = 0.30
    gap_penalty: float = 0.10
    rca_threshold: float = 0.80
    collect_more_threshold: float = 0.45


def _coverage(hypothesis: Hypothesis) -> float:
    required = set(hypothesis.required_evidence_ids)
    if not required:
        return 1.0
    observed = set(hypothesis.supporting_evidence_ids) | set(
        hypothesis.contradicting_evidence_ids
    )
    return len(required & observed) / len(required)


def score_hypothesis(
    hypothesis: Hypothesis,
    *,
    blocking_gap_count: int = 0,
    policy: ConfidencePolicy | None = None,
) -> float:
    policy = policy or ConfidencePolicy()
    supporting = len(set(hypothesis.supporting_evidence_ids))
    contradicting = len(set(hypothesis.contradicting_evidence_ids))
    total_observed = supporting + contradicting

    support_ratio = supporting / total_observed if total_observed else 0.0
    contradiction_ratio = contradicting / total_observed if total_observed else 0.0
    coverage = _coverage(hypothesis)

    score = (
        support_ratio * policy.support_weight
        + coverage * policy.coverage_weight
        - contradiction_ratio * policy.contradiction_weight
        - blocking_gap_count * policy.gap_penalty
    )
    return max(0.0, min(1.0, round(score, 4)))


def evaluate_case_confidence(
    case: InvestigationCase,
    *,
    policy: ConfidencePolicy | None = None,
) -> InvestigationDecision:
    policy = policy or ConfidencePolicy()
    blocking_gaps = [gap for gap in case.evidence_gaps if gap.blocks_rca]

    if not case.hypotheses:
        return InvestigationDecision(
            state="collect_more_evidence",
            confidence=0.0,
            rationale=["No hypotheses are available for evaluation."],
            next_checks=[
                check
                for gap in case.evidence_gaps
                for check in gap.recommended_checks
            ],
            blocked_by_gaps=[gap.id for gap in blocking_gaps],
        )

    scored: list[tuple[float, Hypothesis]] = []
    for hypothesis in case.hypotheses:
        score = score_hypothesis(
            hypothesis,
            blocking_gap_count=len(blocking_gaps),
            policy=policy,
        )
        hypothesis.confidence = score
        if hypothesis.contradicting_evidence_ids and not hypothesis.supporting_evidence_ids:
            hypothesis.status = "contradicted"
        elif hypothesis.supporting_evidence_ids and score >= policy.collect_more_threshold:
            hypothesis.status = "supported"
        elif hypothesis.missing_evidence_ids:
            hypothesis.status = "insufficient"
        else:
            hypothesis.status = "unknown"
        scored.append((score, hypothesis))

    scored.sort(key=lambda item: (-item[0], item[1].id))
    best_score, best = scored[0]

    next_checks = [
        check
        for gap in case.evidence_gaps
        for check in gap.recommended_checks
    ]

    if blocking_gaps:
        state = "collect_more_evidence"
        rationale = [
            f"Leading hypothesis {best.id} is blocked by required evidence gaps."
        ]
    elif best_score >= policy.rca_threshold:
        state = "rca_candidate"
        rationale = [
            f"Leading hypothesis {best.id} crossed the deterministic RCA threshold."
        ]
    elif best_score >= policy.collect_more_threshold:
        state = "collect_more_evidence"
        rationale = [
            f"Leading hypothesis {best.id} has partial support but insufficient confidence."
        ]
    else:
        state = "escalate"
        rationale = [
            "Available evidence does not strongly support any current hypothesis."
        ]

    decision = InvestigationDecision(
        state=state,
        confidence=best_score,
        leading_hypothesis_id=best.id,
        rationale=rationale,
        next_checks=list(dict.fromkeys(next_checks)),
        blocked_by_gaps=[gap.id for gap in blocking_gaps],
    )
    case.decision = decision
    return decision
