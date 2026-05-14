from pydantic import BaseModel


class IncidentClassification(BaseModel):
    pod_name: str
    namespace: str
    node: str | None = None
    container: str
    container_state: str
    restart_count: int
    incident_type: str
    severity: str
    confidence: int
    recommended_team: str