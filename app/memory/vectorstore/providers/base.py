from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.memory import IncidentMemory


class VectorStoreProvider(ABC):
    """
    Abstract semantic vector store contract.
    """

    @abstractmethod
    def index_incident(
        self,
        memory: IncidentMemory,
    ) -> None:
        """
        Persist semantic memory.
        """
        raise NotImplementedError

    @abstractmethod
    def search_similar(
        self,
        query_text: str,
        limit: int = 3,
    ) -> dict:
        """
        Semantic similarity search.
        """
        raise NotImplementedError