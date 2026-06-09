from __future__ import annotations

import json

from app.agents.sre.incident_classifier import classify_incident
from app.agents.sre.rca_agent import generate_rca
from app.agents.sre.remediation_agent import generate_all_remediations
from app.config.logging_config import get_logger
from app.config.settings import settings
from app.llm.client import LLMClient
from app.memory.incident_history.store_incident import store_incident
from app.schemas.workflow import WorkflowExecutionResponse
from app.tools.kubernetes.incident_context import collect_incident_context

logger = get_logger(__name__)


def run_incident_workflow(
    namespace: str | None = None,
    pod_name: str | None = None,
    persist: bool | None = None,
) -> tuple[WorkflowExecutionResponse | None, str | None]:
    """
    Run the incident intelligence workflow.
    """

    logger.info("Starting autonomous incident workflow")

    incidents = collect_incident_context(
        namespace=namespace,
        pod_name=pod_name,
    )

    if not incidents:
        logger.warning("No active incidents detected")
        return None, None

    logger.info(
        "Incident context collected count=%s",
        len(incidents),
    )

    classifications = classify_incident(incidents)

    logger.info(
        "Incident classification completed count=%s",
        len(classifications),
    )

    llm_client = LLMClient()

    try:
        rca_results = []

        for incident, classification in zip(
            incidents,
            classifications,
            strict=False,
        ):
            rca_results.append(
                generate_rca(
                    incident=incident,
                    classification=classification,
                    llm_client=llm_client,
                )
            )

        logger.info(
            "RCA generation completed count=%s",
            len(rca_results),
        )

        remediation_results = generate_all_remediations(
            incidents=incidents,
            classifications=classifications,
            rca_results=rca_results,
            llm_client=llm_client,
        )
    finally:
        llm_client.close()

    logger.info(
        "Remediation generation completed count=%s",
        len(remediation_results),
    )

    workflow_execution = WorkflowExecutionResponse(
        incident_context=incidents,
        classified_incidents=classifications,
        rca_results=rca_results,
        remediation_results=remediation_results,
    )

    should_persist = (
        settings.PERSIST_INCIDENTS
        if persist is None
        else persist
    )
    saved_path = None

    if should_persist:
        saved_path = store_incident(workflow_execution)

        logger.info(
            "Workflow persisted path=%s",
            saved_path,
        )

    return workflow_execution, saved_path


def main() -> None:
    """
    Manual incident workflow entrypoint.
    """

    workflow_execution, _ = run_incident_workflow()

    if workflow_execution is None:
        print("No active incidents detected.")
        return

    print(
        json.dumps(
            workflow_execution.model_dump(
                mode="json"
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
