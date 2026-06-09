from __future__ import annotations

import json

from app.config.logging_config import get_logger
from app.memory.retrieval.search import search_incident_memory
from app.memory.retrieval.semantic_search import (
    search_similar_incidents,
)
from app.schemas.memory import MemoryQuery

logger = get_logger(__name__)


def _normalize_semantic_results(
    semantic_results: dict,
) -> list[dict]:
    """
    Normalize semantic provider response.
    """

    matches = []

    ids = semantic_results.get(
        "ids",
        [[]],
    )[0]

    documents = semantic_results.get(
        "documents",
        [[]],
    )[0]

    metadatas = semantic_results.get(
        "metadatas",
        [[]],
    )[0]

    distances = semantic_results.get(
        "distances",
        [[]],
    )[0]

    for incident_id, document, metadata, distance in zip(
        ids,
        documents,
        metadatas,
        distances,
        strict=False,
    ):
        matches.append(
            {
                "incident_id": incident_id,
                "document": document,
                "metadata": metadata,
                "distance": distance,
                "retrieval_type": "semantic",
            }
        )

    return matches


def _build_semantic_query(
    query: MemoryQuery,
) -> str:
    """
    Convert structured query into semantic query text.
    """

    return " ".join(
        filter(
            None,
            [
                query.incident_type,
                query.namespace,
                query.workload_name,
                query.failure_reason,
                query.severity,
            ],
        )
    )


def hybrid_incident_search(
    query: MemoryQuery,
) -> dict:
    """
    Hybrid operational memory retrieval.

    Combines:
    - deterministic exact search
    - semantic similarity search
    """

    logger.info(
        "Starting hybrid retrieval"
    )

    exact_results = search_incident_memory(
        query
    )

    semantic_query = _build_semantic_query(
        query
    )

    semantic_results = {}

    if semantic_query:
        try:
            semantic_results = search_similar_incidents(
                query_text=semantic_query,
                limit=query.limit,
            )
        except Exception as exc:
            logger.warning(
                "Semantic retrieval unavailable; using exact memory only error=%s",
                exc,
            )

    normalized_semantic = _normalize_semantic_results(
        semantic_results
    )

    exact_matches = [
        memory.model_dump(
            mode="json"
        )
        for memory in exact_results.matches
    ]

    response = {
        "query": query.model_dump(
            mode="json"
        ),
        "exact_matches": exact_matches,
        "semantic_matches": normalized_semantic,
        "exact_match_count": len(
            exact_matches
        ),
        "semantic_match_count": len(
            normalized_semantic
        ),
    }

    logger.info(
        "Hybrid retrieval completed exact=%s semantic=%s",
        len(exact_matches),
        len(normalized_semantic),
    )

    return response


def main() -> None:
    """
    Manual hybrid retrieval test.
    """

    query = MemoryQuery(
        incident_type="MemoryExhaustion",
        limit=3,
    )

    results = hybrid_incident_search(
        query
    )

    print(
        json.dumps(
            results,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
