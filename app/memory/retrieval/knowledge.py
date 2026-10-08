from __future__ import annotations

from app.llm.token_budget import estimate_tokens
from app.memory.incident_patterns.patterns import find_incident_patterns
from app.memory.retrieval.search import search_incident_memory
from app.memory.retrieval.semantic_search import search_similar_incidents
from app.memory.runbooks.retrieval import search_runbooks
from app.schemas.memory import (
    KnowledgeMatch,
    KnowledgePromptDiagnostics,
    KnowledgePromptSelection,
    KnowledgeQuery,
    KnowledgeRetrievalResult,
    MemoryQuery,
    RunbookQuery,
)


SOURCE_PRIORITY = {
    "internal_runbook": 4,
    "reviewed_external": 3,
    "incident_memory_exact": 2,
    "incident_pattern": 2,
    "incident_memory_semantic": 1,
}

SOURCE_CLASS = {
    "internal_runbook": "trusted_guidance",
    "reviewed_external": "trusted_guidance",
    "incident_memory_exact": "historical_context",
    "incident_pattern": "historical_context",
    "incident_memory_semantic": "semantic_similarity",
}

DEFAULT_CLASS_BUDGETS = {
    "trusted_guidance": 2,
    "historical_context": 1,
    "semantic_similarity": 1,
}

PROMPT_CLASS_ORDER = (
    "trusted_guidance",
    "historical_context",
    "semantic_similarity",
    "unclassified",
)


def _memory_query(query: KnowledgeQuery) -> MemoryQuery:
    return MemoryQuery(
        incident_type=query.incident_type,
        namespace=query.namespace,
        workload_name=query.workload_name,
        failure_reason=query.failure_reason,
        severity=query.severity,
        limit=max(query.limit, 0),
    )


def _semantic_query(query: KnowledgeQuery) -> str:
    return " ".join(
        value
        for value in (
            query.text,
            query.domain,
            query.incident_type,
            query.failure_reason,
            query.severity,
        )
        if value
    )


def _runbook_matches(query: KnowledgeQuery) -> list[KnowledgeMatch]:
    result = search_runbooks(
        RunbookQuery(
            domain=query.domain,
            incident_type=query.incident_type,
            text=query.text,
            limit=max(query.limit * 2, 0),
        )
    )
    matches = []
    for match in result.matches:
        chunk = match.chunk
        reviewed = chunk.runbook_id.startswith("review-")
        matches.append(
            KnowledgeMatch(
                knowledge_id=f"{chunk.runbook_id}/{chunk.chunk_id}",
                title=chunk.title,
                source_type=("reviewed_external" if reviewed else "internal_runbook"),
                trust_level=("source_reviewed" if reviewed else "curated"),
                domain=chunk.domain,
                incident_type=(chunk.incident_types[0] if chunk.incident_types else None),
                summary=chunk.summary,
                guidance=chunk.guidance,
                commands=chunk.commands,
                source=chunk.source,
                score=match.score,
                matched_terms=match.matched_terms,
                safety_boundary=chunk.safety_boundary,
            )
        )
    return matches


def _exact_memory_matches(query: KnowledgeQuery) -> list[KnowledgeMatch]:
    if not any(
        (
            query.incident_type,
            query.namespace,
            query.workload_name,
            query.failure_reason,
            query.severity,
        )
    ):
        return []

    result = search_incident_memory(_memory_query(query))
    return [
        KnowledgeMatch(
            knowledge_id=memory.incident_id,
            title=f"Historical incident: {memory.namespace}/{memory.pod_name}",
            source_type="incident_memory_exact",
            trust_level="historical_evidence",
            domain="kubernetes",
            incident_type=memory.incident_type,
            summary=memory.rca_summary,
            guidance=[memory.remediation_summary],
            source=f"incident-memory:{memory.incident_id}",
            score=8,
            matched_terms=[
                value
                for value in (query.incident_type, query.namespace, query.workload_name)
                if value
            ],
            safety_boundary=(
                "Historical similarity is a clue, not proof. Revalidate the "
                "root cause and remediation against current evidence."
            ),
        )
        for memory in result.matches
    ]


def _pattern_matches(query: KnowledgeQuery) -> list[KnowledgeMatch]:
    if not query.domain and not query.incident_type:
        return []

    report = find_incident_patterns(
        min_count=2,
        limit=max(query.limit, 0),
        domain=query.domain,
        incident_type=query.incident_type,
    )
    return [
        KnowledgeMatch(
            knowledge_id=pattern.fingerprint,
            title=f"Recurring incident pattern: {pattern.incident_type}",
            source_type="incident_pattern",
            trust_level="historical_recurrence",
            domain=pattern.domain,
            incident_type=pattern.incident_type,
            summary=(
                f"Observed {pattern.occurrence_count} matching incidents; "
                f"latest occurrence was {pattern.latest_timestamp.isoformat()}."
            ),
            guidance=[
                "Compare the active incident with the stored occurrences before declaring recurrence."
            ],
            source=f"pattern-memory:{pattern.fingerprint}",
            score=7 + min(pattern.occurrence_count, 3),
            matched_terms=[
                value for value in (query.domain, query.incident_type) if value
            ],
            safety_boundary=(
                "Recurrence is a correlation clue, not proof of the current "
                "root cause. Validate against current evidence."
            ),
        )
        for pattern in report.patterns
    ]


def _semantic_memory_matches(
    query: KnowledgeQuery,
) -> tuple[list[KnowledgeMatch], list[str]]:
    query_text = _semantic_query(query)
    if not query_text:
        return [], []

    try:
        result = search_similar_incidents(query_text=query_text, limit=query.limit)
    except Exception:
        return [], ["incident_memory_semantic"]

    matches = []
    for incident_id, document, metadata, distance in zip(
        result.get("ids", [[]])[0],
        result.get("documents", [[]])[0],
        result.get("metadatas", [[]])[0],
        result.get("distances", [[]])[0],
        strict=False,
    ):
        metadata = metadata or {}
        score = max(1, 6 - int(float(distance or 0)))
        matches.append(
            KnowledgeMatch(
                knowledge_id=str(incident_id),
                title=f"Semantically similar incident: {incident_id}",
                source_type="incident_memory_semantic",
                trust_level="historical_similarity",
                domain=str(metadata.get("domain", "unknown")),
                incident_type=metadata.get("incident_type"),
                summary=str(document),
                source=f"semantic-memory:{incident_id}",
                score=score,
                safety_boundary=(
                    "Semantic similarity is a weak clue, not proof. Inspect the "
                    "original incident and current evidence before acting."
                ),
            )
        )
    return matches, []


def _prompt_estimate(matches: list[KnowledgeMatch]) -> int:
    text = "\n".join(
        "\n".join(
            [
                match.title,
                match.summary,
                *match.guidance,
                *match.commands,
                match.safety_boundary,
            ]
        )
        for match in matches
    )
    return estimate_tokens(text)


def _select_prompt_matches(
    matches: list[KnowledgeMatch],
    *,
    max_items: int,
    class_budgets: dict[str, int],
) -> KnowledgePromptSelection:
    bounded_max = max(max_items, 0)
    available_counts = {name: 0 for name in PROMPT_CLASS_ORDER}
    for match in matches:
        source_class = SOURCE_CLASS.get(match.source_type, "unclassified")
        available_counts[source_class] = available_counts.get(source_class, 0) + 1

    selected: list[KnowledgeMatch] = []
    selected_keys: set[tuple[str, str]] = set()
    selected_counts = {name: 0 for name in PROMPT_CLASS_ORDER}

    for source_class in PROMPT_CLASS_ORDER:
        budget = max(class_budgets.get(source_class, 0), 0)
        candidates = [
            match
            for match in matches
            if SOURCE_CLASS.get(match.source_type, "unclassified")
            == source_class
        ]
        for match in candidates[:budget]:
            if len(selected) >= bounded_max:
                break
            key = (match.source_type, match.knowledge_id)
            selected.append(match)
            selected_keys.add(key)
            selected_counts[source_class] += 1

    for match in matches:
        if len(selected) >= bounded_max:
            break
        key = (match.source_type, match.knowledge_id)
        if key in selected_keys:
            continue
        source_class = SOURCE_CLASS.get(match.source_type, "unclassified")
        selected.append(match)
        selected_keys.add(key)
        selected_counts[source_class] = selected_counts.get(source_class, 0) + 1

    return KnowledgePromptSelection(
        matches=selected,
        diagnostics=KnowledgePromptDiagnostics(
            max_items=bounded_max,
            class_budgets=class_budgets,
            available_counts=available_counts,
            selected_counts=selected_counts,
            estimated_tokens=_prompt_estimate(selected),
        ),
    )


def select_knowledge_for_prompt(
    result: KnowledgeRetrievalResult,
    *,
    max_items: int = 4,
    class_budgets: dict[str, int] | None = None,
) -> KnowledgePromptSelection:
    """Select diverse prompt context and expose allocation diagnostics."""

    if (
        class_budgets is None
        and max_items == result.prompt_selection.diagnostics.max_items
    ):
        return result.prompt_selection

    return _select_prompt_matches(
        result.matches,
        max_items=max_items,
        class_budgets=dict(class_budgets or DEFAULT_CLASS_BUDGETS),
    )


def retrieve_knowledge(
    query: KnowledgeQuery,
    *,
    include_semantic: bool = False,
) -> KnowledgeRetrievalResult:
    """Retrieve bounded guidance and history through one offline-first API."""

    matches = [
        *_runbook_matches(query),
        *_exact_memory_matches(query),
        *_pattern_matches(query),
    ]
    unavailable_sources: list[str] = []
    if include_semantic:
        semantic_matches, unavailable_sources = _semantic_memory_matches(query)
        matches.extend(semantic_matches)

    matches.sort(
        key=lambda item: (
            item.score,
            SOURCE_PRIORITY.get(item.source_type, 0),
            item.title,
        ),
        reverse=True,
    )
    source_counts: dict[str, int] = {}
    for match in matches:
        source_counts[match.source_type] = source_counts.get(match.source_type, 0) + 1

    bounded = matches[: max(query.limit, 0)]
    prompt_selection = _select_prompt_matches(
        matches,
        max_items=min(4, max(query.limit, 0)),
        class_budgets=dict(DEFAULT_CLASS_BUDGETS),
    )
    return KnowledgeRetrievalResult(
        query=query,
        matches=bounded,
        total_matches=len(matches),
        source_counts=source_counts,
        unavailable_sources=unavailable_sources,
        semantic_attempted=include_semantic,
        prompt_selection=prompt_selection,
    )


def format_knowledge_context_for_prompt(
    result: KnowledgeRetrievalResult,
    *,
    max_items: int = 4,
    max_guidance_items: int = 3,
    max_commands: int = 2,
) -> str:
    """Render a fixed-budget prompt block without erasing provenance."""

    if not result.matches:
        return "No trusted knowledge matched. Do not invent operational guidance."

    selection = select_knowledge_for_prompt(result, max_items=max_items)
    diagnostics = selection.diagnostics
    lines = [
        "Retrieved knowledge is guidance or historical context, not proof. "
        "Verify every conclusion against live evidence.",
        f"Evidence references: {', '.join(result.query.evidence_references) or 'none supplied'}",
        f"Prompt allocation: {diagnostics.selected_counts}; "
        f"estimated_tokens: {diagnostics.estimated_tokens}",
    ]
    for index, match in enumerate(selection.matches, start=1):
        lines.extend(
            [
                f"{index}. {match.title}",
                f"   id: {match.knowledge_id}",
                f"   provenance: {match.source_type}/{match.trust_level}",
                f"   source: {match.source or 'local source-controlled knowledge'}",
                f"   score: {match.score}",
                f"   summary: {match.summary}",
            ]
        )
        for guidance in match.guidance[:max_guidance_items]:
            lines.append(f"   guidance: {guidance}")
        for command in match.commands[:max_commands]:
            lines.append(f"   safe_command: {command}")
        lines.append(f"   boundary: {match.safety_boundary}")
    if result.unavailable_sources:
        lines.append(
            "Unavailable optional sources: " + ", ".join(result.unavailable_sources)
        )
    return "\n".join(lines)
