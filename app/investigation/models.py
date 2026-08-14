from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.evidence import EvidenceItem


HypothesisStatus = Literal["unknown", "supported", "contradicted", "insufficient"]
DecisionState = Literal[
    "collect_more_evidence",
    "rca_candidate",
    "escalate",
    "resolved",
]
GapPriority = Literal["low", "medium", "high", "critical"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AffectedResource(BaseModel):
    domain: str
    kind: str
    name: str
    namespace: str | None = None
    cluster: str | None = None
    node: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)


class EvidenceGap(BaseModel):
    id: str
    description: str
    priority: GapPriority = "medium"
    reason: str = ""
    recommended_checks: list[str] = Field(default_factory=list)
    blocks_rca: bool = False


class Hypothesis(BaseModel):
    id: str
    statement: str
    status: HypothesisStatus = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    required_evidence_ids: list[str] = Field(default_factory=list)
    missing_evidence_ids: list[str] = Field(default_factory=list)
    why: list[str] = Field(default_factory=list)
    why_not: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class KnowledgeMatch(BaseModel):
    source: str
    reference: str
    title: str
    relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    summary: str = ""
    provenance: str = ""


class HistoricalMatch(BaseModel):
    incident_id: str
    similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    incident_type: str = ""
    root_cause: str | None = None
    resolution: str | None = None
    outcome: str | None = None


class ResolutionRecord(BaseModel):
    summary: str
    actions: list[str] = Field(default_factory=list)
    validation_steps: list[str] = Field(default_factory=list)
    outcome: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None


class AuditEvent(BaseModel):
    timestamp: datetime = Field(default_factory=utc_now)
    actor: str = "aop"
    action: str
    summary: str
    metadata: dict[str, str] = Field(default_factory=dict)


class InvestigationDecision(BaseModel):
    state: DecisionState
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    leading_hypothesis_id: str | None = None
    rationale: list[str] = Field(default_factory=list)
    next_checks: list[str] = Field(default_factory=list)
    blocked_by_gaps: list[str] = Field(default_factory=list)


class RootCauseCandidate(BaseModel):
    """Evidence-backed RCA candidate; distinct from a confirmed root cause."""

    hypothesis_id: str
    statement: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    why: list[str] = Field(default_factory=list)
    why_not: list[str] = Field(default_factory=list)
    validation_state: Literal["candidate", "validated", "rejected"] = "candidate"
    created_at: datetime = Field(default_factory=utc_now)


class InvestigationCase(BaseModel):
    """Canonical incident state shared by collectors, memory, AI, reports and UI."""

    id: str
    title: str
    source: str
    environment: str = "unknown"
    severity: str = "unknown"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    symptoms: list[str] = Field(default_factory=list)
    affected_resources: list[AffectedResource] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    evidence_gaps: list[EvidenceGap] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    knowledge_matches: list[KnowledgeMatch] = Field(default_factory=list)
    historical_matches: list[HistoricalMatch] = Field(default_factory=list)
    correlations: list[str] = Field(default_factory=list)
    decision: InvestigationDecision | None = None
    rca_candidate: RootCauseCandidate | None = None
    root_cause: str | None = None
    recommendations: list[str] = Field(default_factory=list)
    resolution: ResolutionRecord | None = None
    audit_timeline: list[AuditEvent] = Field(default_factory=list)

    def evidence_by_id(self) -> dict[str, EvidenceItem]:
        return {item.id: item for item in self.evidence}

    def hypothesis_by_id(self, hypothesis_id: str) -> Hypothesis | None:
        return next((item for item in self.hypotheses if item.id == hypothesis_id), None)
