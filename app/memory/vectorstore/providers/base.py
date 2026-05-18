from __future__ import annotations

from abc import ABC, abstractmethod


class VectorStoreProvider(ABC):
    """
    Abstract vector store provider contract.
    """

    @abstractmethod
    def upsert(
        self,
        incident_id: str,
        document: str,
        embedding: list[float],
        metadata: dict,
    ) -> None:
        """
        Insert or update semantic memory document.
        """

    @abstractmethod
    def similarity_search(
        self,
        embedding: list[float],
        limit: int = 5,
    ) -> dict:
        """
        Semantic similarity retrieval.
        """

    @abstractmethod
    def delete_all(self) -> None:
        """
        Clear semantic memory.
        """