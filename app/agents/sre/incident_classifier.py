import json

from app.tools.kubernetes.incident_context import collect_incident_context
from app.config.logging_config import get_logger

logger = get_logger(__name__)


INCIDENT_RULES = {
    "OOMKilled": {
        "incident_type": "MemoryExhaustion",
        "severity": "Critical",
        "confidence": 99,
        "recommended_team": "Application / Platform Engineering"
    },
    "CrashLoopBackOff": {
        "incident_type": "ApplicationCrashLoop",
        "severity": "High",
        "confidence": 95,
        "recommended_team": "Application Team"
    },
    "ImagePullBackOff": {
        "incident_type": "ImagePullFailure",
        "severity": "High",
        "confidence": 98,
        "recommended_team": "Platform Engineering"
    },
    "ErrImagePull": {
        "incident_type": "ImagePullFailure",
        "severity": "High",
        "confidence": 96,
        "recommended_team": "Platform Engineering"
    },
    "CreateContainerConfigError": {
        "incident_type": "ContainerConfigurationFailure",
        "severity": "High",
        "confidence": 95,
        "recommended_team": "Platform Engineering"
    },
    "CreateContainerError": {
        "incident_type": "ContainerStartupFailure",
        "severity": "High",
        "confidence": 94,
        "recommended_team": "Platform Engineering"
    },
    "FailedScheduling": {
        "incident_type": "SchedulingFailure",
        "severity": "Critical",
        "confidence": 93,
        "recommended_team": "Cluster Operations"
    }
}


DEFAULT_CLASSIFICATION = {
    "incident_type": "UnknownIncident",
    "severity": "Medium",
    "confidence": 50,
    "recommended_team": "Manual Investigation"
}


def classify_container_state(container_state):
    """
    Classify a single container operational state.
    """

    if not isinstance(container_state, dict):
        logger.warning("Invalid container state payload received")
        return DEFAULT_CLASSIFICATION

    state = container_state.get("state")

    if state in INCIDENT_RULES:
        logger.info("Matched incident rule for state=%s", state)
        return INCIDENT_RULES[state]

    logger.warning("Unknown container state detected: %s", state)

    return DEFAULT_CLASSIFICATION


def classify_incident(incident_data):
    """
    Convert raw incident context into normalized incident intelligence.
    """

    if not incident_data:
        logger.warning("No incident data received for classification")
        return []

    if not isinstance(incident_data, list):
        logger.error("Invalid incident_data type: %s", type(incident_data))
        return []

    classifications = []

    for pod in incident_data:
        try:
            for container in pod.get("container_states", []):

                classification = classify_container_state(container)

                incident_record = {
                    "pod_name": pod.get("pod_name"),
                    "namespace": pod.get("namespace"),
                    "node": pod.get("node"),
                    "container": container.get("container"),
                    "container_state": container.get("state"),
                    "restart_count": container.get("restart_count"),
                    "incident_type": classification["incident_type"],
                    "severity": classification["severity"],
                    "confidence": classification["confidence"],
                    "recommended_team": classification["recommended_team"]
                }

                classifications.append(incident_record)

        except Exception:
            logger.exception(
                "Incident classification failed for pod=%s",
                pod.get("pod_name")
            )

    logger.info(
        "Incident classification completed total=%s",
        len(classifications)
    )

    return classifications


if __name__ == "__main__":
    logger.info("Collecting incident context")

    incident_context = collect_incident_context()

    classified_incidents = classify_incident(incident_context)

    print(json.dumps(classified_incidents, indent=2))