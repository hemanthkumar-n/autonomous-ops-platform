import os
from datetime import datetime
from pathlib import Path

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.schemas.workflow import WorkflowExecutionResponse

logger = get_logger(__name__)


def ensure_incident_directory() -> Path:
    """
    Ensure incident persistence directory exists.
    """

    incident_dir = Path(settings.INCIDENT_HISTORY_DIR)

    incident_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger.info(
        "Incident persistence directory ready path=%s",
        incident_dir,
    )

    return incident_dir


def generate_incident_filename() -> str:
    """
    Generate timestamp-based incident filename.
    """

    timestamp = datetime.utcnow().strftime(
        "%Y%m%d_%H%M%S"
    )

    return f"incident_{timestamp}.json"


def store_incident(
    workflow_report: WorkflowExecutionResponse,
) -> str:
    """
    Persist typed workflow execution report.
    """

    incident_dir = ensure_incident_directory()

    filename = generate_incident_filename()

    filepath = incident_dir / filename

    try:
        filepath.write_text(
            workflow_report.model_dump_json(
                indent=2
            ),
            encoding="utf-8",
        )

        logger.info(
            "Incident workflow persisted path=%s",
            filepath,
        )

        return str(filepath)

    except Exception:
        logger.exception(
            "Incident persistence failed"
        )
        raise


def main():
    """
    Persistence smoke test.
    """

    from app.orchestration.incident_workflow import (
        execute_incident_workflow,
    )

    logger.info("Executing workflow persistence test")

    workflow_output = execute_incident_workflow()

    saved_path = store_incident(
        workflow_output
    )

    print(saved_path)


if __name__ == "__main__":
    main()