from __future__ import annotations

from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.schemas.memory import IncidentFingerprint


def extract_failure_reason(
    incident: IncidentContext,
) -> str | None:
    """
    Extract deterministic failure reason from hybrid schema payloads.
    """

    if not incident.container_states:
        return None

    first_container = incident.container_states[0]

    if isinstance(first_container, dict):
        last_termination = first_container.get("last_termination")

        if isinstance(last_termination, dict):
            return last_termination.get("reason")

        return first_container.get("state")

    if first_container.last_termination:
        if isinstance(first_container.last_termination, dict):
            return first_container.last_termination.get("reason")

    return first_container.state


def build_incident_fingerprint(
    incident: IncidentContext,
    classification: IncidentClassification,
) -> IncidentFingerprint:
    """
    Build deterministic incident fingerprint.
    """

    failure_reason = extract_failure_reason(
        incident
    )

    return IncidentFingerprint(
        incident_type=classification.incident_type,
        namespace=incident.namespace,
        workload_name=incident.pod_name,
        failure_reason=failure_reason,
    )