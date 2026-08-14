from __future__ import annotations

from collections.abc import Callable

from app.investigation.evidence_planner import EvidenceRequest
from app.investigation.models import InvestigationCase
from app.orchestration.linux_cpu_workflow import run_linux_cpu_workflow
from app.schemas.linux import LinuxCpuInvestigation

from .linux_common import normalize_linux_investigation


CpuWorkflow = Callable[..., tuple[LinuxCpuInvestigation, str | None]]


def build_linux_cpu_collector(workflow: CpuWorkflow = run_linux_cpu_workflow):
    """Return a registered read-only collector backed by AOP's CPU workflow."""

    def collect(request: EvidenceRequest, case: InvestigationCase):
        investigation, _ = workflow(persist=False)
        return normalize_linux_investigation(
            request=request,
            case=case,
            domain="cpu",
            hostname=investigation.hostname,
            primary_diagnosis=investigation.primary_diagnosis,
            confidence=investigation.confidence,
            summary=investigation.summary,
            findings=investigation.findings,
            evidence_gaps=investigation.evidence_gaps,
            structured={
                "load_average": investigation.load_average,
                "cpu_count": investigation.cpu_count,
                "running_tasks": investigation.running_tasks,
                "total_tasks": investigation.total_tasks,
                "process_states": investigation.process_states,
                "vmstat_cpu": investigation.vmstat_cpu,
            },
        )

    return collect
