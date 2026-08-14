from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.memory.fingerprints.signature import build_incident_fingerprint
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.schemas.memory import (
    IncidentMemory,
    IncidentPatternGuidance,
    IncidentPatternOccurrence,
    IncidentPatternReport,
    IncidentPatternSummary,
    LinuxIncidentMemory,
)

logger = get_logger(__name__)


def _memory_storage_dir() -> Path:
    return Path(settings.INCIDENT_HISTORY_DIR)


def _normalize(value: str | None) -> str:
    if not value:
        return "unknown"

    return (
        value.strip()
        .lower()
        .replace(" ", "-")
        .replace("/", "_")
        .replace(":", "_")
    )


def build_kubernetes_pattern_fingerprint(memory: IncidentMemory) -> str:
    """
    Build stable Kubernetes pattern fingerprint from normalized memory.
    """

    reason = memory.fingerprint.failure_reason or "unknown"
    return ":".join(
        [
            "kubernetes",
            _normalize(memory.namespace),
            _normalize(memory.fingerprint.workload_name),
            _normalize(memory.incident_type),
            _normalize(reason),
        ]
    )


def build_kubernetes_fingerprint_from_current(
    incident: IncidentContext,
    classification: IncidentClassification,
) -> str:
    """
    Build the same Kubernetes pattern fingerprint for an active incident.
    """

    fingerprint = build_incident_fingerprint(
        incident=incident,
        classification=classification,
    )
    reason = fingerprint.failure_reason or "unknown"
    return ":".join(
        [
            "kubernetes",
            _normalize(fingerprint.namespace),
            _normalize(fingerprint.workload_name),
            _normalize(classification.incident_type),
            _normalize(reason),
        ]
    )


def build_linux_pattern_fingerprint(memory: LinuxIncidentMemory) -> str:
    """
    Build stable Linux pattern fingerprint from normalized memory.
    """

    primary_finding = "none"
    if memory.findings:
        primary_finding = str(memory.findings[0].get("code") or "unknown")

    return ":".join(
        [
            "linux",
            _normalize(memory.domain),
            _normalize(memory.hostname),
            _normalize(memory.target),
            _normalize(memory.incident_type),
            _normalize(primary_finding),
        ]
    )


def _load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _load_kubernetes_occurrences(storage_dir: Path) -> list[tuple[str, IncidentPatternOccurrence]]:
    occurrences: list[tuple[str, IncidentPatternOccurrence]] = []

    for path in sorted(storage_dir.glob("incident_memory_*.json")):
        try:
            payload = _load_json_file(path)
            if not isinstance(payload, list):
                continue

            for item in payload:
                memory = IncidentMemory.model_validate(item)
                fingerprint = build_kubernetes_pattern_fingerprint(memory)
                resource = f"{memory.namespace}/{memory.pod_name}"
                occurrences.append(
                    (
                        fingerprint,
                        IncidentPatternOccurrence(
                            incident_id=memory.incident_id,
                            timestamp=memory.timestamp,
                            domain="kubernetes",
                            resource=resource,
                            incident_type=memory.incident_type,
                            severity=memory.severity,
                            summary=memory.rca_summary,
                            source_file=str(path),
                        ),
                    )
                )
        except Exception:
            logger.exception("Failed loading Kubernetes pattern memory file=%s", path)

    return occurrences


def _load_linux_occurrences(storage_dir: Path) -> list[tuple[str, IncidentPatternOccurrence]]:
    occurrences: list[tuple[str, IncidentPatternOccurrence]] = []

    for path in sorted(storage_dir.glob("linux_*_*.json")):
        try:
            payload = _load_json_file(path)
            if not isinstance(payload, dict):
                continue

            memory = LinuxIncidentMemory.model_validate(payload)
            fingerprint = build_linux_pattern_fingerprint(memory)
            resource = f"{memory.hostname}/{memory.target}"
            occurrences.append(
                (
                    fingerprint,
                    IncidentPatternOccurrence(
                        incident_id=memory.incident_id,
                        timestamp=memory.timestamp,
                        domain=memory.domain,
                        resource=resource,
                        incident_type=memory.incident_type,
                        severity=memory.severity,
                        summary=memory.summary,
                        source_file=str(path),
                    ),
                )
            )
        except Exception:
            logger.exception("Failed loading Linux pattern memory file=%s", path)

    return occurrences


def find_incident_patterns(
    *,
    min_count: int = 2,
    limit: int = 10,
    domain: str | None = None,
    incident_type: str | None = None,
) -> IncidentPatternReport:
    """
    Find recurring incident patterns from structured local memory.
    """

    storage_dir = _memory_storage_dir()
    if not storage_dir.exists():
        return IncidentPatternReport(
            patterns=[],
            total_patterns=0,
            total_occurrences=0,
            min_count=min_count,
        )

    loaded = [
        *_load_kubernetes_occurrences(storage_dir),
        *_load_linux_occurrences(storage_dir),
    ]

    filtered = [
        (fingerprint, occurrence)
        for fingerprint, occurrence in loaded
        if _matches_filters(
            occurrence,
            domain=domain,
            incident_type=incident_type,
        )
    ]

    grouped: dict[str, list[IncidentPatternOccurrence]] = defaultdict(list)
    for fingerprint, occurrence in filtered:
        grouped[fingerprint].append(occurrence)

    patterns = [
        _summarize_pattern(fingerprint, occurrences)
        for fingerprint, occurrences in grouped.items()
        if len(occurrences) >= min_count
    ]

    patterns.sort(
        key=lambda pattern: (
            pattern.occurrence_count,
            pattern.latest_timestamp,
        ),
        reverse=True,
    )

    limited = patterns[:limit]

    logger.info(
        "Incident pattern search completed patterns=%s occurrences=%s",
        len(limited),
        len(filtered),
    )

    return IncidentPatternReport(
        patterns=limited,
        total_patterns=len(patterns),
        total_occurrences=len(filtered),
        min_count=min_count,
    )


def find_kubernetes_pattern_guidance(
    incidents: list[IncidentContext],
    classifications: list[IncidentClassification],
    *,
    min_count: int = 1,
    max_patterns: int = 1,
) -> list[IncidentPatternGuidance]:
    """
    Find exact historical recurrence hints for active Kubernetes incidents.
    """

    all_patterns = find_incident_patterns(
        min_count=min_count,
        limit=100,
        domain="kubernetes",
    )
    by_fingerprint = {
        pattern.fingerprint: pattern
        for pattern in all_patterns.patterns
    }

    guidance: list[IncidentPatternGuidance] = []

    for incident, classification in zip(
        incidents,
        classifications,
        strict=False,
    ):
        fingerprint = build_kubernetes_fingerprint_from_current(
            incident=incident,
            classification=classification,
        )
        pattern = by_fingerprint.get(fingerprint)
        patterns = [pattern] if pattern else []

        guidance.append(
            IncidentPatternGuidance(
                pod_name=classification.pod_name,
                namespace=classification.namespace,
                container=classification.container,
                incident_type=classification.incident_type,
                fingerprint=fingerprint,
                patterns=patterns[:max_patterns],
            )
        )

    return guidance


def _matches_filters(
    occurrence: IncidentPatternOccurrence,
    *,
    domain: str | None,
    incident_type: str | None,
) -> bool:
    if domain and occurrence.domain.lower() != domain.lower():
        return False

    if incident_type and occurrence.incident_type.lower() != incident_type.lower():
        return False

    return True


def _summarize_pattern(
    fingerprint: str,
    occurrences: list[IncidentPatternOccurrence],
) -> IncidentPatternSummary:
    ordered = sorted(
        occurrences,
        key=lambda occurrence: occurrence.timestamp,
        reverse=True,
    )
    latest = ordered[0]

    severities = sorted(
        {occurrence.severity for occurrence in ordered},
        key=str.lower,
    )
    resources = sorted(
        {occurrence.resource for occurrence in ordered},
        key=str.lower,
    )

    return IncidentPatternSummary(
        fingerprint=fingerprint,
        domain=latest.domain,
        incident_type=latest.incident_type,
        occurrence_count=len(ordered),
        latest_timestamp=latest.timestamp,
        severities=severities,
        resources=resources,
        occurrences=ordered,
    )
