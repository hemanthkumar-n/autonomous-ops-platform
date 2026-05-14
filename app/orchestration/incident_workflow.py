import json

from app.tools.kubernetes.incident_context import collect_incident_context
from app.agents.sre.incident_classifier import classify_incident
from app.agents.sre.rca_agent import generate_rca
from app.agents.sre.remediation_agent import generate_all_remediations
from app.memory.incident_history.store_incident import store_incident
from app.config.logging_config import get_logger
from app.config.settings import settings

logger = get_logger(__name__)


def map_incident_context(incident_context):
    """
    Map pod_name -> full incident context.
    """

    context_map = {}

    if not incident_context:
        return context_map

    for incident in incident_context:
        pod_name = incident.get("pod_name")

        if pod_name:
            context_map[pod_name] = incident

    return context_map


def generate_incident_rcas(classified_incidents, incident_context):
    """
    Generate RCA per incident.
    """

    context_map = map_incident_context(incident_context)

    rca_results = []

    for incident in classified_incidents:
        try:
            pod_name = incident.get("pod_name")

            relevant_context = context_map.get(pod_name, {})

            logger.info("Generating RCA for pod=%s", pod_name)

            rca_output = generate_rca(
                incident_context=relevant_context,
                classified_incidents=[incident]
            )

            rca_results.append({
                "pod_name": pod_name,
                "incident_type": incident.get("incident_type"),
                "rca": rca_output
            })

        except Exception:
            logger.exception(
                "RCA generation failed for pod=%s",
                incident.get("pod_name")
            )

    return rca_results


def main():
    """
    Autonomous incident workflow.
    """

    logger.info("Autonomous Ops Incident Workflow started")

    try:
        logger.info("Step 1: Collecting unified incident context")

        incident_context = collect_incident_context()

    except Exception:
        logger.exception("Incident context collection failed")
        return

    if not incident_context:
        logger.warning("No active incidents detected")
        print("No active incidents detected.")
        return

    try:
        logger.info("Step 2: Classifying incidents")

        classified_incidents = classify_incident(incident_context)

    except Exception:
        logger.exception("Incident classification failed")
        classified_incidents = []

    try:
        logger.info("Step 3: Generating incident RCA")

        rca_results = generate_incident_rcas(
            classified_incidents=classified_incidents,
            incident_context=incident_context
        )

    except Exception:
        logger.exception("RCA workflow stage failed")
        rca_results = []

    try:
        logger.info("Step 4: Generating remediation guidance")

        remediation_results = generate_all_remediations(
            classified_incidents=classified_incidents,
            incident_context=incident_context
        )

    except Exception:
        logger.exception("Remediation workflow stage failed")
        remediation_results = []

    workflow_output = {
        "metadata": {
            "platform_name": settings.PLATFORM_NAME,
            "environment": settings.ENVIRONMENT,
            "workflow_version": settings.WORKFLOW_VERSION
        },
        "incident_context": incident_context,
        "classified_incidents": classified_incidents,
        "rca_results": rca_results,
        "remediation_results": remediation_results
    }

    try:
        logger.info("Step 5: Persisting workflow results")

        saved_path = store_incident(workflow_output)

        logger.info("Workflow saved path=%s", saved_path)

    except Exception:
        logger.exception("Incident persistence failed")
        saved_path = None

    logger.info("Autonomous Ops Incident Workflow completed")

    print(json.dumps(workflow_output, indent=2))


if __name__ == "__main__":
    main()