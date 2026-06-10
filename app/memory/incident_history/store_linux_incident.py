from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.memory.vectorstore.client import SemanticMemoryClient
from app.schemas.linux import LinuxDiskInvestigation
from app.schemas.memory import LinuxIncidentMemory

logger = get_logger(__name__)


def _build_memory(
    investigation: LinuxDiskInvestigation,
) -> LinuxIncidentMemory:
    return LinuxIncidentMemory(
        incident_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        environment=settings.ENVIRONMENT,
        domain="linux.disk",
        hostname=investigation.hostname,
        target=investigation.path,
        incident_type=investigation.primary_diagnosis,
        severity=investigation.severity,
        confidence=investigation.confidence,
        summary=investigation.summary,
        findings=[
            finding.model_dump(mode="json")
            for finding in investigation.findings
        ],
        evidence_gaps=investigation.evidence_gaps,
        source_workflow_version=settings.WORKFLOW_VERSION,
    )


def _semantic_document(memory: LinuxIncidentMemory) -> str:
    findings = "\n".join(
        f"- {item['code']}: {item['summary']}"
        for item in memory.findings
    )
    return f"""
Domain: {memory.domain}
Host: {memory.hostname}
Target: {memory.target}
Incident Type: {memory.incident_type}
Severity: {memory.severity}
Confidence: {memory.confidence}
Summary: {memory.summary}
Findings:
{findings or "- none"}
""".strip()


def store_linux_disk_incident(
    investigation: LinuxDiskInvestigation,
) -> str:
    """
    Persist Linux disk investigation memory with semantic fallback.
    """

    memory = _build_memory(investigation)
    storage_dir = Path(settings.INCIDENT_HISTORY_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    path = storage_dir / f"linux_disk_memory_{timestamp}.json"
    path.write_text(
        json.dumps(memory.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )

    try:
        semantic_client = SemanticMemoryClient()
        semantic_client.index_document(
            incident_id=memory.incident_id,
            document=_semantic_document(memory),
            metadata={
                "domain": memory.domain,
                "incident_type": memory.incident_type,
                "hostname": memory.hostname,
                "target": memory.target,
                "severity": memory.severity,
            },
        )
    except Exception as exc:
        logger.warning(
            "Linux semantic memory unavailable; structured persistence "
            "will continue error=%s",
            exc,
        )

    logger.info("Linux incident memory persisted path=%s", path)
    return str(path)
