from pydantic import BaseModel

from app.schemas.ai import RCAResponse, RemediationResponse
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext


class WorkflowExecutionResponse(BaseModel):
    incident_context: list[IncidentContext]
    classified_incidents: list[IncidentClassification]
    rca_results: list[RCAResponse]
    remediation_results: list[RemediationResponse]