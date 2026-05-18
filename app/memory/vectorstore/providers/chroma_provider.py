from __future__ import annotations

import chromadb

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.memory.vectorstore.providers.base import VectorStoreProvider

logger = get_logger(__name__)


class ChromaProvider(VectorStoreProvider):
    """
    Chroma vector store provider.

    Implementation is configuration-driven so the platform
    can migrate later to pgvector / Qdrant / Weaviate
    without architectural redesign.
    """

    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(
            path=settings.VECTORSTORE_PATH,
        )

        self.collection = self.client.get_or_create_collection(
            name=settings.VECTORSTORE_COLLECTION_NAME,
        )

        logger.info(
            "Chroma provider initialized path=%s collection=%s",
            settings.VECTORSTORE_PATH,
            settings.VECTORSTORE_COLLECTION_NAME,
        )

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

        self.collection.upsert(
            ids=[incident_id],
            documents=[document],
            embeddings=[embedding],
            metadatas=[metadata],
        )

        logger.info(
            "Semantic memory upsert completed incident_id=%s",
            incident_id,
        )

    def similarity_search(
        self,
        embedding: list[float],
        limit: int = 5,
    ) -> dict:
        """
        Execute semantic similarity retrieval.
        """

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=limit,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        logger.info(
            "Semantic similarity search completed limit=%s",
            limit,
        )

        return results

    def delete_all(self) -> None:
        """
        Clear collection contents.
        Useful for rebuild workflows.
        """

        self.client.delete_collection(
            settings.VECTORSTORE_COLLECTION_NAME,
        )

        self.collection = self.client.get_or_create_collection(
            name=settings.VECTORSTORE_COLLECTION_NAME,
        )

        logger.warning(
            "Semantic memory cleared collection=%s",
            settings.VECTORSTORE_COLLECTION_NAME,
        )