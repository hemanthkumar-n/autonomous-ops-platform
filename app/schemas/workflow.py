from pydantic import BaseModel

from app.schemas.ai import RCAResponse, RemediationResponse
from app.schemas.classification import IncidentClassification
from app.schemas.correlation import KubernetesLinuxCorrelation
from app.schemas.incident import IncidentContext
from app.schemas.kubernetes_knowledge import KubernetesIssueKnowledge


class IncidentKnowledgeGuidance(BaseModel):
    pod_name: str
    namespace: str
    container: str
    symptom: str
    incident_type: str
    kubernetes_knowledge: KubernetesIssueKnowledge | None = None
    linux_correlation: KubernetesLinuxCorrelation | None = None
    evidence_gaps: list[str] = []


class WorkflowExecutionResponse(BaseModel):
    incident_context: list[IncidentContext]
    classified_incidents: list[IncidentClassification]
    rca_results: list[RCAResponse]
    remediation_results: list[RemediationResponse]
    correlation_guidance: list[IncidentKnowledgeGuidance] = []
