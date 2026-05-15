from __future__ import annotations

import json
from pathlib import Path

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.schemas.memory import (
    IncidentMemory,
    MemoryQuery,
    MemorySearchResult,
)

logger = get_logger(__name__)


def _memory_storage_dir() -> Path:
    """
    Return configured incident memory directory.
    """

    return Path(settings.INCIDENT_HISTORY_DIR)


def load_incident_memories() -> list[IncidentMemory]:
    """
    Load all persisted incident memories.
    """

    storage_dir = _memory_storage_dir()

    if not storage_dir.exists():
        logger.warning(
            "Incident memory directory not found path=%s",
            storage_dir,
        )
        return []

    memories = []

    for file_path in storage_dir.glob("incident_memory_*.json"):
        try:
            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                payload = json.load(file)

            for item in payload:
                memories.append(
                    IncidentMemory.model_validate(item)
                )

        except Exception:
            logger.exception(
                "Failed loading incident memory file=%s",
                file_path,
            )

    logger.info(
        "Incident memories loaded count=%s",
        len(memories),
    )

    return memories


def _matches_query(
    memory: IncidentMemory,
    query: MemoryQuery,
    ) -> bool:
    """
    Apply normalized deterministic query filters.
    """

    if query.incident_type:
        if memory.incident_type.lower() != query.incident_type.lower():
            return False

    if query.namespace:
        if memory.namespace.lower() != query.namespace.lower():
            return False

    if query.workload_name:
        if (
            memory.fingerprint.workload_name.lower()
            != query.workload_name.lower()
        ):
            return False

    if query.failure_reason:
        memory_reason = memory.fingerprint.failure_reason

        if not memory_reason:
            return False

        if memory_reason.lower() != query.failure_reason.lower():
            return False

    if query.severity:
        if memory.severity.lower() != query.severity.lower():
            return False

    return True


def search_incident_memory(
    query: MemoryQuery,
) -> MemorySearchResult:
    """
    Search structured incident memory.
    """

    memories = load_incident_memories()

    matches = [
        memory
        for memory in memories
        if _matches_query(memory, query)
    ]

    limited_matches = matches[: query.limit]

    logger.info(
        "Incident memory search completed matches=%s",
        len(limited_matches),
    )

    return MemorySearchResult(
        query=query,
        matches=limited_matches,
        total_matches=len(matches),
    )


if __name__ == "__main__":
    sample_query = MemoryQuery(
        incident_type="MemoryExhaustion",
        limit=5,
    )

    results = search_incident_memory(
        sample_query
    )

    print(
        results.model_dump_json(
            indent=2
        )
    )
