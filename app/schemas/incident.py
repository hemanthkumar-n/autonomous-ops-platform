from dataclasses import dataclass
from typing import Optional


@dataclass
class ClassifiedIncident:
    pod_name: str
    namespace: str
    node: str
    container: str
    container_state: str
    restart_count: int
    incident_type: str
    severity: str
    confidence: int
    recommended_team: str


@dataclass
class RCAResult:
    pod_name: str
    incident_type: str
    rca: str


@dataclass
class RemediationResult:
    pod_name: str
    incident_type: str
    remediation: str