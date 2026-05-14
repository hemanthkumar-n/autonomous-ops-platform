from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.schemas.metrics import PodMetrics


class PodCondition(BaseModel):
    type: str
    status: str


class ContainerState(BaseModel):
    container: str
    state: str
    restart_count: int
    last_termination: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    logs: Optional[str] = None


class IncidentContext(BaseModel):
    pod_name: str
    namespace: str
    phase: str
    node: Optional[str] = None
    conditions: List[PodCondition] = []
    container_states: List[ContainerState] = []
    events: List[Any] = []
    metrics: PodMetrics