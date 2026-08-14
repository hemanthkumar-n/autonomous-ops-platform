from __future__ import annotations

from collections.abc import Callable

from app.investigation.adapters.linux_memory import linux_memory_to_case
from app.investigation.autonomous_loop import EvidenceCollectionResult
from app.investigation.evidence_planner import EvidenceRequest
from app.investigation.models import InvestigationCase
from app.orchestration.linux_memory_workflow import run_linux_memory_workflow
from app.schemas.linux import LinuxMemoryInvestigation


MemoryWorkflow = Callable[..., tuple[LinuxMemoryInvestigation, str | None]]


def _leading_hypothesis_id(case: InvestigationCase) -> str | None:
    if case.decision and case.decision.leading_hypothesis_id:
        return case.decision.leading_hypothesis_id
    if case.hypotheses:
        return case.hypotheses[0].id
    return None


def build_linux_memory_collector(
    workflow: MemoryWorkflow = run_linux_memory_workflow,
):
    """Return a registered read-only collector backed by AOP's Linux memory workflow."""

    def collect(
        request: EvidenceRequest,
        case: InvestigationCase,
    ) -> EvidenceCollectionResult:
        pid_value = request.metadata.get("pid")
        pid = int(pid_value) if pid_value and pid_value.isdigit() else None
        investigation, _ = workflow(pid=pid, persist=False)
        normalized = linux_memory_to_case(
            investigation,
            case_id=f"{case.id}-linux-memory",
            environment=case.environment,
        )

        hypothesis_id = request.metadata.get("hypothesis_id") or _leading_hypothesis_id(case)
        evidence_ids = [item.id for item in normalized.evidence]
        supporting: dict[str, list[str]] = {}
        reasons: dict[str, list[str]] = {}

        if hypothesis_id and investigation.primary_diagnosis != "insufficient_evidence":
            supporting[hypothesis_id] = evidence_ids
            reasons[hypothesis_id] = [
                finding.summary for finding in investigation.findings
            ] or [investigation.summary]

        resolved = []
        if request.gap_id and investigation.primary_diagnosis != "insufficient_evidence":
            resolved.append(request.gap_id)

        return EvidenceCollectionResult(
            request_id=request.id,
            evidence=list(normalized.evidence),
            supporting_evidence=supporting,
            supporting_reasons=reasons,
            resolved_gap_ids=resolved,
            notes=[
                f"linux_memory_primary_diagnosis={investigation.primary_diagnosis}",
                f"linux_memory_source_confidence={investigation.confidence}",
            ],
        )

    return collect
