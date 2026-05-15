from __future__ import annotations

from app.memory.vectorstore.providers.base import (
    VectorStoreProvider,
)
from app.memory.vectorstore.providers.chroma_provider import (
    ChromaVectorStoreProvider,
)
from app.schemas.memory import IncidentMemory


class SemanticMemoryClient:
    """
    Central semantic memory abstraction.
    """

    def __init__(
        self,
        provider: VectorStoreProvider | None = None,
    ) -> None:
        self.provider = (
            provider
            or ChromaVectorStoreProvider()
        )

    def index_incident(
        self,
        memory: IncidentMemory,
    ) -> None:
        self.provider.index_incident(
            memory
        )

    def search_similar(
        self,
        query_text: str,
        limit: int = 3,
    ) -> dict:
        return self.provider.search_similar(
            query_text=query_text,
            limit=limit,
        )