from __future__ import annotations

from app.llm.embeddings.providers.base import EmbeddingProvider
from app.llm.embeddings.providers.ollama_embedding_provider import (
    OllamaEmbeddingProvider,
)


class EmbeddingClient:
    """
    Central embedding abstraction.
    """

    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
    ) -> None:
        self.provider = (
            provider
            or OllamaEmbeddingProvider()
        )

    def embed(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate embeddings.
        """

        return self.provider.embed(text)