from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.schemas.evidence import EvidenceItem

from .evidence_planner import EvidencePlan, EvidencePlanner, EvidenceRequest
from .models import AuditEvent, Hypothesis, InvestigationCase
from .orchestrator import InvestigationOrchestrator


class EvidenceCollectionResult(BaseModel):
    """Normalized output from one explicitly registered read-only collector."""

    request_id: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    supporting_evidence: dict[str, list[str]] = Field(default_factory=dict)
    contradicting_evidence: dict[str, list[str]] = Field(default_factory=dict)
    resolved_gap_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class InvestigationStep(BaseModel):
    number: int
    plan: EvidencePlan
    executed_request_ids: list[str] = Field(default_factory=list)
    skipped_request_ids: list[str] = Field(default_factory=list)
    evidence_added: int = 0
    decision_state: str = "unknown"
    confidence: float = 0.0


class InvestigationLoopResult(BaseModel):
    case: InvestigationCase
    steps: list[InvestigationStep] = Field(default_factory=list)
    stop_reason: str
    total_requests_executed: int = 0
    total_evidence_added: int = 0


@dataclass(frozen=True, slots=True)
class InvestigationLoopPolicy:
    max_steps: int = 5
    max_total_requests: int = 12
    stop_on_collector_error: bool = False


EvidenceCollector = Callable[[EvidenceRequest, InvestigationCase], EvidenceCollectionResult]


def _extend_unique(target: list[str], values: list[str]) -> None:
    seen = set(target)
    for value in values:
        if value not in seen:
            target.append(value)
            seen.add(value)


def _apply_hypothesis_evidence(
    hypothesis: Hypothesis,
    *,
    supporting: list[str],
    contradicting: list[str],
) -> None:
    _extend_unique(hypothesis.supporting_evidence_ids, supporting)
    _extend_unique(hypothesis.contradicting_evidence_ids, contradicting)
    observed = set(hypothesis.supporting_evidence_ids) | set(
        hypothesis.contradicting_evidence_ids
    )
    hypothesis.missing_evidence_ids = [
        evidence_id
        for evidence_id in hypothesis.missing_evidence_ids
        if evidence_id not in observed
    ]


def apply_collection_result(
    case: InvestigationCase,
    result: EvidenceCollectionResult,
) -> int:
    """Merge one collector result into the canonical case without duplicate evidence."""

    existing_ids = set(case.evidence_by_id())
    added = 0
    for item in result.evidence:
        if item.id in existing_ids:
            continue
        case.evidence.append(item)
        existing_ids.add(item.id)
        added += 1

    for hypothesis_id, evidence_ids in result.supporting_evidence.items():
        hypothesis = case.hypothesis_by_id(hypothesis_id)
        if hypothesis is not None:
            _apply_hypothesis_evidence(
                hypothesis,
                supporting=evidence_ids,
                contradicting=[],
            )

    for hypothesis_id, evidence_ids in result.contradicting_evidence.items():
        hypothesis = case.hypothesis_by_id(hypothesis_id)
        if hypothesis is not None:
            _apply_hypothesis_evidence(
                hypothesis,
                supporting=[],
                contradicting=evidence_ids,
            )

    resolved = set(result.resolved_gap_ids)
    if resolved:
        case.evidence_gaps = [gap for gap in case.evidence_gaps if gap.id not in resolved]
        for hypothesis in case.hypotheses:
            hypothesis.missing_evidence_ids = [
                item for item in hypothesis.missing_evidence_ids if item not in resolved
            ]

    case.audit_timeline.append(
        AuditEvent(
            action="evidence_collected",
            summary=(
                f"Collector request={result.request_id} added={added} "
                f"resolved_gaps={len(resolved)}"
            ),
            metadata={"request_id": result.request_id},
        )
    )
    return added


class AutonomousInvestigationLoop:
    """
    Bounded evidence-planning loop.

    Only explicitly registered collector functions can run. Requests marked as
    non-read-only are rejected. The loop never executes shell text or performs
    remediation.
    """

    def __init__(
        self,
        *,
        collectors: Mapping[str, EvidenceCollector],
        planner: EvidencePlanner | None = None,
        orchestrator: InvestigationOrchestrator | None = None,
        policy: InvestigationLoopPolicy | None = None,
    ) -> None:
        self.collectors = dict(collectors)
        self.planner = planner or EvidencePlanner()
        self.orchestrator = orchestrator or InvestigationOrchestrator()
        self.policy = policy or InvestigationLoopPolicy()

    def run(self, case: InvestigationCase) -> InvestigationLoopResult:
        completed: set[str] = set()
        steps: list[InvestigationStep] = []
        total_evidence = 0
        total_requests = 0

        initial = self.orchestrator.evaluate(case)
        if initial.state in {"rca_candidate", "resolved"}:
            return InvestigationLoopResult(
                case=case,
                stop_reason=initial.state,
                total_requests_executed=0,
                total_evidence_added=0,
            )

        for step_number in range(1, self.policy.max_steps + 1):
            plan = self.planner.plan(case, completed_request_ids=completed)
            step = InvestigationStep(number=step_number, plan=plan)

            if plan.stop_reason is not None:
                decision = self.orchestrator.evaluate(case)
                step.decision_state = decision.state
                step.confidence = decision.confidence
                steps.append(step)
                return InvestigationLoopResult(
                    case=case,
                    steps=steps,
                    stop_reason=plan.stop_reason,
                    total_requests_executed=total_requests,
                    total_evidence_added=total_evidence,
                )

            for request in plan.requests:
                if total_requests >= self.policy.max_total_requests:
                    step.skipped_request_ids.append(request.id)
                    continue
                if not request.read_only:
                    step.skipped_request_ids.append(request.id)
                    case.audit_timeline.append(
                        AuditEvent(
                            action="collector_blocked",
                            summary=f"Blocked non-read-only request {request.id}.",
                            metadata={"request_id": request.id},
                        )
                    )
                    continue

                collector = self.collectors.get(request.collector)
                if collector is None:
                    step.skipped_request_ids.append(request.id)
                    case.audit_timeline.append(
                        AuditEvent(
                            action="collector_unavailable",
                            summary=(
                                f"No registered collector for {request.collector}; "
                                f"request {request.id} was not executed."
                            ),
                            metadata={"request_id": request.id},
                        )
                    )
                    continue

                try:
                    result = collector(request, case)
                except Exception as exc:
                    step.skipped_request_ids.append(request.id)
                    case.audit_timeline.append(
                        AuditEvent(
                            action="collector_error",
                            summary=f"Collector failed for {request.id}: {type(exc).__name__}",
                            metadata={"request_id": request.id},
                        )
                    )
                    if self.policy.stop_on_collector_error:
                        steps.append(step)
                        return InvestigationLoopResult(
                            case=case,
                            steps=steps,
                            stop_reason="collector_error",
                            total_requests_executed=total_requests,
                            total_evidence_added=total_evidence,
                        )
                    continue

                completed.add(request.id)
                step.executed_request_ids.append(request.id)
                total_requests += 1
                added = apply_collection_result(case, result)
                step.evidence_added += added
                total_evidence += added

            decision = self.orchestrator.evaluate(case)
            step.decision_state = decision.state
            step.confidence = decision.confidence
            steps.append(step)

            if decision.state in {"rca_candidate", "resolved"}:
                return InvestigationLoopResult(
                    case=case,
                    steps=steps,
                    stop_reason=decision.state,
                    total_requests_executed=total_requests,
                    total_evidence_added=total_evidence,
                )

            if total_requests >= self.policy.max_total_requests:
                return InvestigationLoopResult(
                    case=case,
                    steps=steps,
                    stop_reason="request_budget_exhausted",
                    total_requests_executed=total_requests,
                    total_evidence_added=total_evidence,
                )

            if not step.executed_request_ids:
                return InvestigationLoopResult(
                    case=case,
                    steps=steps,
                    stop_reason="no_registered_safe_collector",
                    total_requests_executed=total_requests,
                    total_evidence_added=total_evidence,
                )

        return InvestigationLoopResult(
            case=case,
            steps=steps,
            stop_reason="step_budget_exhausted",
            total_requests_executed=total_requests,
            total_evidence_added=total_evidence,
        )
