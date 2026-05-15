from __future__ import annotations

import chromadb

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.llm.embeddings.client import EmbeddingClient
from app.schemas.memory import IncidentMemory

logger = get_logger(__name__)


class ChromaIncidentStore:
    """
    Semantic vector memory store for incidents.
    """

    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(
            path="app/memory/vectorstore/chroma_db"
        )

        self.collection = self.client.get_or_create_collection(
            name="incident_memory"
        )

        self.embedding_client = EmbeddingClient()

    def _build_document(
        self,
        memory: IncidentMemory,
    ) -> str:
        """
        Convert incident memory into searchable semantic text.
        """

        return f"""
Incident Type: {memory.incident_type}
Namespace: {memory.namespace}
Pod: {memory.pod_name}
Severity: {memory.severity}
Failure Reason: {memory.fingerprint.failure_reason}
RCA: {memory.rca_summary}
Remediation: {memory.remediation_summary}
""".strip()

    def index_incident(
        self,
        memory: IncidentMemory,
    ) -> None:
        """
        Index incident into semantic vector store.
        """

        document = self._build_document(
            memory
        )

        embedding = self.embedding_client.embed(
            document
        )

        self.collection.add(
            ids=[memory.incident_id],
            documents=[document],
            embeddings=[embedding],
            metadatas=[
                {
                    "incident_type": memory.incident_type,
                    "namespace": memory.namespace,
                    "severity": memory.severity,
                    "failure_reason": (
                        memory.fingerprint.failure_reason
                        or "unknown"
                    ),
                }
            ],
        )

        logger.info(
            "Incident indexed in semantic memory id=%s",
            memory.incident_id,
        )

    def search_similar(
        self,
        query_text: str,
        limit: int = 3,
    ) -> dict:
        """
        Semantic incident similarity search.
        """

        embedding = self.embedding_client.embed(
            query_text
        )

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=limit,
        )

        logger.info(
            "Semantic incident search completed matches=%s",
            limit,
        )

        return results