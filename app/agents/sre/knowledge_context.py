from __future__ import annotations

from app.memory.fingerprints.signature import extract_failure_reason
from app.memory.retrieval.knowledge import (
    format_knowledge_context_for_prompt,
    retrieve_knowledge,
)
from app.schemas.classification import IncidentClassification
from app.schemas.incident import IncidentContext
from app.schemas.memory import KnowledgeQuery, KnowledgeRetrievalResult


def retrieve_incident_knowledge_context(
    incident: IncidentContext,
    classification: IncidentClassification,
    *,
    include_semantic: bool = False,
    retrieval_limit: int = 8,
    prompt_items: int = 4,
) -> tuple[str, bool, KnowledgeRetrievalResult]:
    """Build one bounded, source-diverse context for SRE reasoning agents."""

    failure_reason = extract_failure_reason(incident)
    result = retrieve_knowledge(
        KnowledgeQuery(
            domain="kubernetes",
            incident_type=classification.incident_type,
            text=(
                f"{incident.phase} {classification.container_state} "
                f"{classification.incident_type} "
                f"{failure_reason or ''}"
            ),
            namespace=incident.namespace,
            workload_name=incident.pod_name,
            failure_reason=failure_reason,
            severity=classification.severity,
            evidence_references=[
                f"kubernetes://{incident.namespace}/pod/{incident.pod_name}"
            ],
            limit=retrieval_limit,
        ),
        include_semantic=include_semantic,
    )
    has_history = any(
        (
            source.startswith("incident_memory")
            or source == "incident_pattern"
        )
        and count > 0
        for source, count in result.source_counts.items()
    )
    return (
        format_knowledge_context_for_prompt(result, max_items=prompt_items),
        has_history,
        result,
    )
