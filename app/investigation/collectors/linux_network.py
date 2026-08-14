from __future__ import annotations

from collections.abc import Callable

from app.investigation.evidence_planner import EvidenceRequest
from app.investigation.models import InvestigationCase
from app.orchestration.linux_network_workflow import run_linux_network_workflow
from app.schemas.linux import LinuxNetworkInvestigation

from .linux_common import normalize_linux_investigation


NetworkWorkflow = Callable[..., tuple[LinuxNetworkInvestigation, str | None]]


def build_linux_network_collector(
    workflow: NetworkWorkflow = run_linux_network_workflow,
):
    """Return a registered read-only collector backed by AOP's network workflow."""

    def collect(request: EvidenceRequest, case: InvestigationCase):
        iface = request.metadata.get("iface") or None
        investigation, _ = workflow(iface=iface, persist=False)
        return normalize_linux_investigation(
            request=request,
            case=case,
            domain="network",
            hostname=investigation.hostname,
            primary_diagnosis=investigation.primary_diagnosis,
            confidence=investigation.confidence,
            summary=investigation.summary,
            findings=investigation.findings,
            evidence_gaps=investigation.evidence_gaps,
            structured={
                "iface": investigation.iface,
                "interfaces": investigation.interfaces,
                "routes": investigation.routes,
                "resolvers": investigation.resolvers,
                "nic_signals": investigation.nic_signals,
            },
        )

    return collect
