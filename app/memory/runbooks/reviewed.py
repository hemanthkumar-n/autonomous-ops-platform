from __future__ import annotations

import re
from pathlib import Path

from app.memory.runbooks.external import load_external_catalog
from app.schemas.memory import (
    ExternalKnowledgeReview,
    ExternalKnowledgeReviewCatalog,
    RunbookChunk,
)


BUNDLED_K8S_AF_REVIEWS = Path(__file__).parent / "sources" / "k8s_af_reviews.json"
WORD_PATTERN = re.compile(r"[a-z0-9_.:/-]+")


def load_review_catalog(
    path: Path = BUNDLED_K8S_AF_REVIEWS,
) -> ExternalKnowledgeReviewCatalog:
    return ExternalKnowledgeReviewCatalog.model_validate_json(
        path.read_text(encoding="utf-8")
    )


def get_review(
    review_or_story_id: str,
    *,
    path: Path = BUNDLED_K8S_AF_REVIEWS,
) -> ExternalKnowledgeReview:
    catalog = load_review_catalog(path)
    for review in catalog.reviews:
        if review.review_id == review_or_story_id or review.story_id == review_or_story_id:
            return review
    raise KeyError(f"unknown external knowledge review: {review_or_story_id}")


def review_queue() -> list[dict[str, object]]:
    external = load_external_catalog()
    reviewed_story_ids = {
        review.story_id for review in load_review_catalog().reviews
    }
    return [
        {
            "story_id": story.story_id,
            "title": story.title,
            "canonical_url": story.canonical_url,
            "technologies": story.technologies,
            "impact": story.impact,
            "review_state": story.review_state,
        }
        for story in external.stories
        if story.story_id not in reviewed_story_ids
    ]


def search_reviews(
    text: str,
    *,
    review_state: str | None = None,
    limit: int = 10,
) -> list[ExternalKnowledgeReview]:
    query_terms = set(WORD_PATTERN.findall(text.lower()))
    scored: list[tuple[int, ExternalKnowledgeReview]] = []
    for review in load_review_catalog().reviews:
        if review_state and review.review_state != review_state:
            continue
        haystack = " ".join(
            [
                review.source_title,
                review.reported_root_cause,
                *review.domains,
                *review.incident_types,
                *review.keywords,
                *review.reported_symptoms,
                *review.contributing_factors,
                *review.reusable_checks,
            ]
        ).lower()
        overlap = query_terms & set(WORD_PATTERN.findall(haystack))
        if overlap or not query_terms:
            scored.append((len(overlap), review))
    scored.sort(key=lambda item: (item[0], item[1].source_title), reverse=True)
    return [review for _, review in scored[: max(limit, 0)]]


def reviewed_guidance_chunks() -> tuple[RunbookChunk, ...]:
    """
    Convert only guidance-reviewed sources into bounded RAG chunks.
    """

    chunks = []
    for review in load_review_catalog().reviews:
        if review.review_state != "guidance_reviewed":
            continue
        chunks.append(
            RunbookChunk(
                runbook_id=review.review_id,
                chunk_id=f"{review.review_id}-001",
                title=f"Reviewed incident: {review.source_title}",
                domain=review.domains[0],
                incident_types=review.incident_types,
                keywords=review.keywords,
                summary=review.reported_root_cause,
                guidance=review.reusable_checks,
                commands=review.safe_commands,
                source=review.source_url,
                safety_boundary=review.safety_boundary,
            )
        )
    return tuple(chunks)
