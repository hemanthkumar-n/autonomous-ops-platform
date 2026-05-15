from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """
    Abstract embedding provider contract.
    """

    @abstractmethod
    def embed(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate embedding vector.
        """
        raise NotImplementedError