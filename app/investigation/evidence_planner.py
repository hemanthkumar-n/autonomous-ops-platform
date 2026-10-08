from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from .confidence import ConfidencePolicy, evaluate_case_confidence
from .models import EvidenceGap, InvestigationCase


CollectorKind = Literal[
    "linux_memory",
    "linux_cpu",
    "linux_disk",
    "linux_network",
    "kubernetes_read",
    "prometheus_query",
    "manual_review",
]


class EvidenceRequest(BaseModel):
    """One bounded, read-only evidence request selected by the planner."""

    id: str
    gap_id: str | None = None
    domain: str = "unknown"
    collector: CollectorKind
    instruction: str
    purpose: str
    priority: str = "medium"
    read_only: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)


class EvidencePlan(BaseModel):
    requests: list[EvidenceRequest] = Field(default_factory=list)
    stop_reason: str | None = None
    rationale: list[str] = Field(default_factory=list)


@dataclass(frozen=True, slots=True)
class EvidencePlannerPolicy:
    max_requests_per_step: int = 4
    allow_manual_review: bool = True


def _collector_for_check(check: str) -> CollectorKind:
    normalized = check.strip().lower()
    if "linux memory" in normalized:
        return "linux_memory"
    if "linux cpu" in normalized:
        return "linux_cpu"
    if "linux disk" in normalized or "linux space" in normalized:
        return "linux_disk"
    if "linux network" in normalized or "linux nic" in normalized:
        return "linux_network"
    if normalized.startswith("kubectl") or "kubernetes" in normalized:
        return "kubernetes_read"
    if "prometheus" in normalized or "promql" in normalized:
        return "prometheus_query"
    return "manual_review"


def _domain_for_collector(collector: CollectorKind) -> str:
    if collector.startswith("linux_"):
        return "linux"
    if collector == "kubernetes_read":
        return "kubernetes"
    if collector == "prometheus_query":
        return "observability"
    return "unknown"


def _resource_metadata(case: InvestigationCase) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for resource in case.affected_resources:
        if resource.cluster and "cluster" not in metadata:
            metadata["cluster"] = resource.cluster
        if resource.namespace and "namespace" not in metadata:
            metadata["namespace"] = resource.namespace
        if resource.node and "node" not in metadata:
            metadata["node"] = resource.node
        kind = resource.kind.lower()
        if kind == "pod" and "pod" not in metadata:
            metadata["pod"] = resource.name
        elif kind == "container" and "container" not in metadata:
            metadata["container"] = resource.name
        elif kind == "host" and "host" not in metadata:
            metadata["host"] = resource.name
        elif kind == "process" and "pid" not in metadata:
            metadata["pid"] = resource.labels.get("pid", resource.name)
    return metadata


def _gap_requests(gap: EvidenceGap, case: InvestigationCase) -> list[EvidenceRequest]:
    checks = gap.recommended_checks or [gap.description]
    context = _resource_metadata(case)
    requests: list[EvidenceRequest] = []
    for index, check in enumerate(checks, start=1):
        collector = _collector_for_check(check)
        requests.append(
            EvidenceRequest(
                id=f"{gap.id}.request.{index}",
                gap_id=gap.id,
                domain=_domain_for_collector(collector),
                collector=collector,
                instruction=check,
                purpose=gap.reason or gap.description,
                priority=gap.priority,
                read_only=True,
                metadata=context,
            )
        )
    return requests


class EvidencePlanner:
    """Plan the next bounded evidence step from current case state."""

    def __init__(
        self,
        *,
        confidence_policy: ConfidencePolicy | None = None,
        planner_policy: EvidencePlannerPolicy | None = None,
    ) -> None:
        self.confidence_policy = confidence_policy or ConfidencePolicy()
        self.planner_policy = planner_policy or EvidencePlannerPolicy()

    def plan(
        self,
        case: InvestigationCase,
        *,
        completed_request_ids: set[str] | None = None,
    ) -> EvidencePlan:
        completed_request_ids = completed_request_ids or set()
        decision = evaluate_case_confidence(case, policy=self.confidence_policy)

        if decision.state in {"rca_candidate", "resolved"}:
            return EvidencePlan(
                stop_reason=decision.state,
                rationale=["Current evidence already satisfies the investigation stop condition."],
            )

        blocking = [gap for gap in case.evidence_gaps if gap.blocks_rca]
        non_blocking = [gap for gap in case.evidence_gaps if not gap.blocks_rca]
        ordered_gaps = [*blocking, *non_blocking]

        requests: list[EvidenceRequest] = []
        for gap in ordered_gaps:
            for request in _gap_requests(gap, case):
                if request.id in completed_request_ids:
                    continue
                if request.collector == "manual_review" and not self.planner_policy.allow_manual_review:
                    continue
                requests.append(request)
                if len(requests) >= self.planner_policy.max_requests_per_step:
                    break
            if len(requests) >= self.planner_policy.max_requests_per_step:
                break

        if requests:
            return EvidencePlan(
                requests=requests,
                rationale=[
                    f"Selected {len(requests)} bounded request(s) from unresolved evidence gaps.",
                    "Blocking RCA gaps are prioritized before non-blocking context gaps.",
                ],
            )

        if decision.state == "escalate":
            return EvidencePlan(
                stop_reason="escalate_no_safe_plan",
                rationale=["Evidence is weak and no additional bounded collector request is available."],
            )

        return EvidencePlan(
            stop_reason="no_additional_evidence_plan",
            rationale=["The case needs more evidence, but current gaps do not expose another bounded check."],
        )
