from pydantic import BaseModel


class RCAResponse(BaseModel):
    pod_name: str
    incident_type: str
    rca: str


class RemediationResponse(BaseModel):
    pod_name: str
    incident_type: str
    remediation: str