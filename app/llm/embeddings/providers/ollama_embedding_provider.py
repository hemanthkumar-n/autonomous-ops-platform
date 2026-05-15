from __future__ import annotations

import ollama

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.llm.embeddings.providers.base import EmbeddingProvider

logger = get_logger(__name__)


class OllamaEmbeddingProvider(
    EmbeddingProvider,
):
    """
    Ollama embedding implementation.
    """

    def embed(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate embedding vector using Ollama.
        """

        logger.info(
            "Generating embedding text_length=%s",
            len(text),
        )

        response = ollama.embeddings(
            model=settings.EMBEDDING_MODEL_NAME,
            prompt=text,
        )

        embedding = response["embedding"]

        logger.info(
            "Embedding generated dimensions=%s",
            len(embedding),
        )

        return embedding