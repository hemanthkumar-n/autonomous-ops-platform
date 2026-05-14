import json

from app.agents.sre.incident_rules import INCIDENT_RULES
from app.config.logging_config import get_logger
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext

logger = get_logger(__name__)


def classify_container_state(container_state) -> dict:
    """
    Classify a single container operational state.
    """

    state = container_state.state

    if state in INCIDENT_RULES:
        return INCIDENT_RULES[state]

    logger.warning("Unknown incident state encountered state=%s", state)

    return {
        "incident_type": "UnknownIncident",
        "severity": "Medium",
        "confidence": 50,
        "recommended_team": "Manual Investigation",
    }


def classify_incident(
    incident_data: list[IncidentContext],
) -> list[IncidentClassification]:
    """
    Convert typed incident context into typed incident intelligence.
    """

    classifications = []

    for pod in incident_data:
        for container in pod.container_states:

            classification = classify_container_state(container)

            incident_record = IncidentClassification(
                pod_name=pod.pod_name,
                namespace=pod.namespace,
                node=pod.node,
                container=container.container,
                container_state=container.state,
                restart_count=container.restart_count,
                incident_type=classification["incident_type"],
                severity=classification["severity"],
                confidence=classification["confidence"],
                recommended_team=classification["recommended_team"],
            )

            classifications.append(incident_record)

    logger.info(
        "Incident classification completed classified=%s",
        len(classifications),
    )

    return classifications


if __name__ == "__main__":
    from app.tools.kubernetes.incident_context import collect_incident_context

    incident_context = collect_incident_context()

    classified_incidents = classify_incident(incident_context)

    print(
        json.dumps(
            [incident.model_dump() for incident in classified_incidents],
            indent=2,
        )
    )