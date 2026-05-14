import json

from app.agents.sre.incident_classifier import classify_incident
from app.agents.sre.rca_agent import generate_rca
from app.agents.sre.remediation_agent import generate_all_remediations
from app.config.logging_config import get_logger
from app.memory.incident_history.store_incident import store_incident
from app.schemas.workflow import WorkflowExecutionResponse
from app.tools.kubernetes.incident_context import collect_incident_context

logger = get_logger(__name__)


def execute_incident_workflow() -> WorkflowExecutionResponse:
    """
    Execute full typed autonomous incident workflow.
    """

    logger.info("Starting autonomous incident workflow")

    incident_context = collect_incident_context()

    if not incident_context:
        logger.warning("No active incidents detected")

        return WorkflowExecutionResponse(
            incident_context=[],
            classified_incidents=[],
            rca_results=[],
            remediation_results=[],
        )

    logger.info("Classifying incidents")

    classified_incidents = classify_incident(
        incident_context
    )

    logger.info("Generating RCA responses")

    rca_results = generate_rca(
        incident_context=incident_context,
        classified_incidents=classified_incidents,
    )

    logger.info("Generating remediation responses")

    remediation_results = generate_all_remediations(
        classified_incidents=classified_incidents,
        incident_context=incident_context,
    )

    workflow_response = WorkflowExecutionResponse(
        incident_context=incident_context,
        classified_incidents=classified_incidents,
        rca_results=rca_results,
        remediation_results=remediation_results,
    )

    logger.info("Persisting workflow execution")

    store_incident(workflow_response)

    logger.info("Incident workflow completed successfully")

    return workflow_response


def main():
    """
    CLI execution entrypoint.
    """

    workflow_output = execute_incident_workflow()

    print(
        json.dumps(
            workflow_output.model_dump(),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()