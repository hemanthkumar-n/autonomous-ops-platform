import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config.logging_config import get_logger
from app.config.settings import settings

logger = get_logger(__name__)


def ensure_incident_directory() -> Path:
    """
    Ensure incident storage directory exists.
    """

    incident_dir = Path(settings.INCIDENT_HISTORY_DIR)

    incident_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return incident_dir


def generate_incident_filename() -> str:
    """
    Generate timestamp-based incident filename.
    """

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")

    return f"incident_{timestamp}.json"


def store_incident(incident_report: Any) -> str | None:
    """
    Persist incident report to disk.
    """

    if not settings.PERSIST_INCIDENTS:
        logger.warning("Incident persistence disabled via configuration")
        return None

    if incident_report is None:
        logger.warning("No incident report provided for persistence")
        return None

    try:
        incident_dir = ensure_incident_directory()

        filename = generate_incident_filename()

        filepath = incident_dir / filename

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                incident_report,
                file,
                indent=2,
                ensure_ascii=False
            )

        logger.info("Incident persisted successfully path=%s", filepath)

        return str(filepath)

    except Exception:
        logger.exception("Incident persistence failed")
        return None


if __name__ == "__main__":
    sample_incident = {
        "test": "incident"
    }

    saved_path = store_incident(sample_incident)

    print(saved_path)