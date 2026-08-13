from __future__ import annotations

from .confidence import ConfidencePolicy, evaluate_case_confidence
from .models import AuditEvent, InvestigationCase, InvestigationDecision
from .reasoning import build_reasoning_summary


class InvestigationOrchestrator:
    """Evaluate an investigation without collecting new evidence or mutating systems."""

    def __init__(self, policy: ConfidencePolicy | None = None) -> None:
        self.policy = policy or ConfidencePolicy()

    def evaluate(self, case: InvestigationCase) -> InvestigationDecision:
        decision = evaluate_case_confidence(case, policy=self.policy)
        case.audit_timeline.append(
            AuditEvent(
                action="confidence_evaluated",
                summary=(
                    f"Investigation decision={decision.state} "
                    f"confidence={decision.confidence:.2f}"
                ),
                metadata={
                    "leading_hypothesis_id": decision.leading_hypothesis_id or "",
                    "state": decision.state,
                },
            )
        )
        return decision

    def reasoning(self, case: InvestigationCase) -> dict[str, object]:
        if case.decision is None:
            self.evaluate(case)
        assert case.decision is not None

        hypothesis_id = case.decision.leading_hypothesis_id
        if hypothesis_id is None:
            return {
                "decision": case.decision.model_dump(mode="json"),
                "hypothesis": None,
            }

        hypothesis = case.hypothesis_by_id(hypothesis_id)
        if hypothesis is None:
            return {
                "decision": case.decision.model_dump(mode="json"),
                "hypothesis": None,
            }

        return {
            "decision": case.decision.model_dump(mode="json"),
            "hypothesis": build_reasoning_summary(case, hypothesis),
        }
