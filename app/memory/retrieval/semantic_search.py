from __future__ import annotations

import json

from app.config.logging_config import get_logger
from app.memory.vectorstore.client import (
    SemanticMemoryClient,
)

logger = get_logger(__name__)


def search_similar_incidents(
    query_text: str,
    limit: int = 3,
) -> dict:
    """
    Semantic incident similarity search.
    """

    client = SemanticMemoryClient()

    results = client.search_similar(
        query_text=query_text,
        limit=limit,
    )

    logger.info(
        "Semantic incident retrieval completed"
    )

    return results


def main() -> None:
    """
    Manual semantic retrieval test.
    """

    results = search_similar_incidents(
        query_text="OOMKilled memory exhaustion Kubernetes pod",
        limit=3,
    )

    print(
        json.dumps(
            results,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()