from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.memory.fingerprints.signature import build_incident_fingerprint
from app.schemas.ai import RCAResponse, RemediationResponse
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.schemas.memory import IncidentMemory
from app.schemas.workflow import WorkflowExecutionResponse

logger = get_logger(__name__)


def _ensure_storage_directory() -> Path:
    """
    Ensure incident memory directory exists.
    """

    storage_dir = Path(settings.INCIDENT_HISTORY_DIR)

    storage_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return storage_dir


def _build_incident_memory(
    incident: IncidentContext,
    classification: IncidentClassification,
    rca: RCAResponse,
    remediation: RemediationResponse,
) -> IncidentMemory:
    """
    Convert workflow objects into normalized incident memory.
    """

    fingerprint = build_incident_fingerprint(
        incident=incident,
        classification=classification,
    )

    return IncidentMemory(
        incident_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        environment=settings.ENVIRONMENT,
        fingerprint=fingerprint,
        severity=classification.severity,
        confidence=classification.confidence,
        pod_name=incident.pod_name,
        namespace=incident.namespace,
        node=incident.node,
        incident_type=classification.incident_type,
        rca_summary=rca.rca,
        remediation_summary=remediation.remediation,
        source_workflow_version=settings.WORKFLOW_VERSION,
    )


def _generate_filename() -> str:
    """
    Generate normalized incident memory filename.
    """

    timestamp = datetime.utcnow().strftime(
        "%Y%m%d_%H%M%S"
    )

    return f"incident_memory_{timestamp}.json"


def store_incident(
    workflow: WorkflowExecutionResponse,
) -> str:
    """
    Persist structured incident memory.
    """

    storage_dir = _ensure_storage_directory()

    incident_memories = []

    for incident, classification, rca, remediation in zip(
        workflow.incident_context,
        workflow.classified_incidents,
        workflow.rca_results,
        workflow.remediation_results,
        strict=False,
    ):
        incident_memories.append(
            _build_incident_memory(
                incident=incident,
                classification=classification,
                rca=rca,
                remediation=remediation,
            )
        )

    filepath = storage_dir / _generate_filename()

    with filepath.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            [memory.model_dump(mode="json") for memory in incident_memories],
            file,
            indent=2,
        )

    logger.info(
        "Incident memory persisted count=%s path=%s",
        len(incident_memories),
        filepath,
    )

    return str(filepath)