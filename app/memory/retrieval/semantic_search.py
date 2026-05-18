from __future__ import annotations

import json

from app.config.logging_config import get_logger
from app.llm.embeddings.client import EmbeddingClient
from app.memory.vectorstore.client import SemanticMemoryClient

logger = get_logger(__name__)


def search_similar_incidents(
    query_text: str,
    limit: int = 5,
) -> dict:
    """
    Semantic incident similarity search.
    """

    embedding_client = EmbeddingClient()
    semantic_client = SemanticMemoryClient()

    query_embedding = embedding_client.embed(
        query_text
    )

    results = semantic_client.similarity_search(
        embedding=query_embedding,
        limit=limit,
    )

    logger.info(
        "Semantic incident retrieval completed"
    )

    return results


def main() -> None:
    """
    Manual semantic search test.
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