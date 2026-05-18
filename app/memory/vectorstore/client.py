from __future__ import annotations

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.memory.vectorstore.providers.chroma_provider import ChromaProvider

logger = get_logger(__name__)


class SemanticMemoryClient:
    """
    Vector store abstraction layer.

    Routes semantic memory operations through configured provider.
    """

    def __init__(self) -> None:
        provider = settings.VECTORSTORE_PROVIDER.lower()

        if provider == "chroma":
            self.provider = ChromaProvider()
        else:
            raise ValueError(
                f"Unsupported vectorstore provider: {provider}"
            )

        logger.info(
            "Semantic memory client initialized provider=%s",
            provider,
        )

    def upsert(
        self,
        incident_id: str,
        document: str,
        embedding: list[float],
        metadata: dict,
    ) -> None:
        self.provider.upsert(
            incident_id=incident_id,
            document=document,
            embedding=embedding,
            metadata=metadata,
        )

    def similarity_search(
        self,
        embedding: list[float],
        limit: int = 5,
    ) -> dict:
        return self.provider.similarity_search(
            embedding=embedding,
            limit=limit,
        )

    def delete_all(self) -> None:
        self.provider.delete_all()