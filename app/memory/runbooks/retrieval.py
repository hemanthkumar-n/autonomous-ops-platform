from __future__ import annotations

import re

from app.memory.runbooks.catalog import RUNBOOK_CHUNKS
from app.memory.runbooks.reviewed import reviewed_guidance_chunks
from app.schemas.memory import (
    RunbookMatch,
    RunbookQuery,
    RunbookSearchResult,
)


WORD_PATTERN = re.compile(r"[a-z0-9_.-]+")


def _terms(*values: str | None) -> set[str]:
    terms: set[str] = set()
    for value in values:
        if not value:
            continue
        terms.update(WORD_PATTERN.findall(value.lower()))
    return terms


def search_runbooks(query: RunbookQuery) -> RunbookSearchResult:
    """
    Deterministically retrieve bounded trusted runbook chunks.

    This is the first RAG foundation: no vector database is required yet, and
    no full document is injected into prompts. Matches are scored by domain,
    incident type, and keyword overlap.
    """

    query_terms = _terms(query.text, query.incident_type, query.domain)
    matches: list[RunbookMatch] = []

    searchable_chunks = (*RUNBOOK_CHUNKS, *reviewed_guidance_chunks())
    for chunk in searchable_chunks:
        score = 0
        matched_terms: set[str] = set()

        if query.domain and (
            chunk.domain == query.domain
            or chunk.domain.startswith(f"{query.domain}.")
            or query.domain.startswith(f"{chunk.domain}.")
        ):
            score += 5
            matched_terms.add(query.domain)

        if query.incident_type:
            incident = query.incident_type.lower()
            chunk_incidents = {value.lower() for value in chunk.incident_types}
            if incident in chunk_incidents:
                score += 6
                matched_terms.add(query.incident_type)

        chunk_terms = _terms(
            chunk.title,
            chunk.summary,
            " ".join(chunk.keywords),
            " ".join(chunk.guidance),
            " ".join(chunk.commands),
        )
        overlap = query_terms & chunk_terms
        if overlap:
            score += len(overlap)
            matched_terms.update(overlap)

        if score > 0:
            matches.append(
                RunbookMatch(
                    chunk=chunk,
                    score=score,
                    matched_terms=sorted(matched_terms),
                )
            )

    matches.sort(
        key=lambda item: (
            item.score,
            item.chunk.domain,
            item.chunk.title,
        ),
        reverse=True,
    )
    bounded = matches[: max(query.limit, 0)]
    return RunbookSearchResult(
        query=query,
        matches=bounded,
        total_matches=len(matches),
    )


def format_runbook_context_for_prompt(
    result: RunbookSearchResult,
    *,
    max_chunks: int = 2,
    max_guidance_items: int = 3,
    max_commands: int = 3,
) -> str:
    """
    Render a bounded RAG context block for prompts.
    """

    if not result.matches:
        return (
            "No trusted runbook chunks matched. Do not invent runbook guidance."
        )

    lines = [
        "Trusted runbook matches are guidance, not proof. Verify each item "
        "against live evidence."
    ]

    for index, match in enumerate(result.matches[:max_chunks], start=1):
        chunk = match.chunk
        lines.extend(
            [
                f"{index}. {chunk.title}",
                f"   id: {chunk.runbook_id}/{chunk.chunk_id}",
                f"   domain: {chunk.domain}",
                f"   score: {match.score}",
                f"   matched_terms: {', '.join(match.matched_terms) or 'none'}",
                f"   summary: {chunk.summary}",
                "   guidance:",
            ]
        )
        for guidance in chunk.guidance[:max_guidance_items]:
            lines.append(f"   - {guidance}")
        if chunk.commands:
            lines.append("   useful_commands:")
            for command in chunk.commands[:max_commands]:
                lines.append(f"   - {command}")
        lines.append(f"   boundary: {chunk.safety_boundary}")

    return "\n".join(lines)
