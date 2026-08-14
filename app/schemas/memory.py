from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class IncidentFingerprint(BaseModel):
    """
    Deterministic incident signature for correlation.
    """

    incident_type: str
    namespace: str
    workload_name: str
    failure_reason: Optional[str] = None


class IncidentMemory(BaseModel):
    """
    Persistent normalized incident memory contract.
    """

    incident_id: str
    timestamp: datetime
    environment: str

    fingerprint: IncidentFingerprint

    severity: str
    confidence: int

    pod_name: str
    namespace: str
    node: Optional[str] = None

    incident_type: str

    rca_summary: str
    remediation_summary: str

    source_workflow_version: str


class LinuxIncidentMemory(BaseModel):
    """
    Persistent Linux investigation memory without Kubernetes-specific fields.
    """

    incident_id: str
    timestamp: datetime
    environment: str
    domain: str
    hostname: str
    target: str
    incident_type: str
    severity: str
    confidence: int
    summary: str
    findings: list[dict[str, Any]]
    evidence_gaps: list[str]
    source_workflow_version: str


class MemoryQuery(BaseModel):
    """
    Memory retrieval query contract.
    """

    incident_type: Optional[str] = None
    namespace: Optional[str] = None
    workload_name: Optional[str] = None
    failure_reason: Optional[str] = None
    severity: Optional[str] = None
    limit: int = 5


class MemorySearchResult(BaseModel):
    """
    Memory retrieval response contract.
    """

    query: MemoryQuery
    matches: list[IncidentMemory]
    total_matches: int


class IncidentPatternOccurrence(BaseModel):
    """
    One historical incident occurrence that belongs to a pattern.
    """

    incident_id: str
    timestamp: datetime
    domain: str
    resource: str
    incident_type: str
    severity: str
    summary: str
    source_file: str


class IncidentPatternSummary(BaseModel):
    """
    Grouped incident recurrence summary.
    """

    fingerprint: str
    domain: str
    incident_type: str
    occurrence_count: int
    latest_timestamp: datetime
    severities: list[str]
    resources: list[str]
    occurrences: list[IncidentPatternOccurrence]


class IncidentPatternReport(BaseModel):
    """
    Pattern intelligence response contract.
    """

    patterns: list[IncidentPatternSummary]
    total_patterns: int
    total_occurrences: int
    min_count: int


class IncidentPatternGuidance(BaseModel):
    """
    Pattern guidance attached to an active investigation.
    """

    pod_name: str
    namespace: str
    container: str
    incident_type: str
    fingerprint: str
    patterns: list[IncidentPatternSummary] = []
    evidence_note: str = (
        "Historical recurrence is a clue, not proof of root cause."
    )


class RunbookMemory(BaseModel):
    """
    Future runbook knowledge contract.
    """

    runbook_id: str
    title: str
    incident_type: str
    remediation_steps: list[str]
    source: Optional[str] = None


class KnowledgeArtifact(BaseModel):
    """
    Future architecture / operational knowledge object.
    """

    artifact_id: str
    category: str
    title: str
    content: str
    created_at: datetime
