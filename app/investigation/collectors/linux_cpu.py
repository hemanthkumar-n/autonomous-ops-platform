from __future__ import annotations

from collections.abc import Callable

from app.investigation.adapters.linux_cpu import linux_cpu_evidence
from app.investigation.autonomous_loop import EvidenceCollectionResult
from app.investigation.evidence_planner import EvidenceRequest
from app.investigation.models import InvestigationCase
from app.orchestration.linux_cpu_workflow import run_linux_cpu_workflow
from app.schemas.linux import LinuxCpuInvestigation


CpuWorkflow = Callable[..., tuple[LinuxCpuInvestigation, str | None]]


def build_linux_cpu_collector(workflow: CpuWorkflow = run_linux_cpu_workflow):
    """Register the existing read-only Linux CPU workflow for evidence collection."""

    def collect(
        request: EvidenceRequest,
        case: InvestigationCase,
    ) -> EvidenceCollectionResult:
        investigation, _ = workflow(persist=False)
        expected_host = request.metadata.get("host") or request.metadata.get("node")
        if expected_host and investigation.hostname != expected_host:
            raise ValueError("CPU evidence came from a different host")

        evidence = linux_cpu_evidence(investigation)
        diagnosis = investigation.primary_diagnosis
        sufficient = (
            investigation.status == "diagnosed"
            and diagnosis not in {"insufficient_evidence", "unsupported_platform"}
            and investigation.confidence >= 80
            and bool(evidence)
        )
        primary_id = f"linux.cpu.finding.{diagnosis}"
        observed_ids = {item.id for item in evidence}
        supporting: dict[str, list[str]] = {}
        reasons: dict[str, list[str]] = {}
        if sufficient and primary_id in observed_ids:
            for hypothesis in case.hypotheses:
                if primary_id in hypothesis.required_evidence_ids:
                    supporting[hypothesis.id] = [primary_id]
                    reasons[hypothesis.id] = [investigation.summary]

        return EvidenceCollectionResult(
            request_id=request.id,
            evidence=evidence,
            supporting_evidence=supporting,
            supporting_reasons=reasons,
            resolved_gap_ids=[request.gap_id] if sufficient and request.gap_id else [],
            notes=[
                f"linux_cpu_primary_diagnosis={diagnosis}",
                f"linux_cpu_source_confidence={investigation.confidence}",
                *investigation.evidence_gaps,
            ],
        )

    return collect
