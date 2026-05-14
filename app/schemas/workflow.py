from pydantic import BaseModel
from typing import List

from app.schemas.incident import IncidentContext
from app.schemas.classification import IncidentClassification
from app.schemas.ai import RCAResponse, RemediationResponse


class WorkflowExecution(BaseModel):
    incident_context: List[IncidentContext]
    classified_incidents: List[IncidentClassification]
    rca_results: List[RCAResponse]
    remediation_results: List[RemediationResponse]