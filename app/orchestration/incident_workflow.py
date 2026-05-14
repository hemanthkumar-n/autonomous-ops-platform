from __future__ import annotations

import json

from app.agents.sre.incident_classifier import classify_incident
from app.agents.sre.rca_agent import generate_rca
from app.agents.sre.remediation_agent import generate_all_remediations
from app.config.logging_config import get_logger
from app.memory.incident_history.store_incident import store_incident
from app.schemas.workflow import WorkflowExecutionResponse
from app.tools.kubernetes.incident_context import collect_incident_context

logger = get_logger(__name__)


def main() -> None:
    """
    Autonomous incident workflow orchestration.
    """

    logger.info("Starting autonomous incident workflow")

    incidents = collect_incident_context()

    if not incidents:
        logger.warning("No active incidents detected")
        print("No active incidents detected.")
        return

    logger.info(
        "Incident context collected count=%s",
        len(incidents),
    )

    classifications = classify_incident(incidents)

    logger.info(
        "Incident classification completed count=%s",
        len(classifications),
    )

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
            )
        )

    logger.info(
        "RCA generation completed count=%s",
        len(rca_results),
    )

    remediation_results = generate_all_remediations(
        incidents=incidents,
        classifications=classifications,
    )

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

    saved_path = store_incident(workflow_execution)

    logger.info(
        "Workflow persisted path=%s",
        saved_path,
    )

    print(
        json.dumps(
            workflow_execution.model_dump(),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
