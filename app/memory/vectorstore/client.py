from __future__ import annotations

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.llm.embeddings.client import EmbeddingClient
from app.memory.vectorstore.providers.chroma_provider import ChromaProvider
from app.schemas.memory import IncidentMemory

logger = get_logger(__name__)


class SemanticMemoryClient:
    """
    Vector store abstraction layer.

    Routes semantic memory operations through configured provider.
    """

    def __init__(
        self,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        provider = settings.VECTORSTORE_PROVIDER.lower()

        if provider == "chroma":
            self.provider = ChromaProvider()
        else:
            raise ValueError(
                f"Unsupported vectorstore provider: {provider}"
            )

        self.embedding_client = (
            embedding_client
            or EmbeddingClient()
        )

        logger.info(
            "Semantic memory client initialized provider=%s",
            provider,
        )

    @staticmethod
    def _build_document(
        memory: IncidentMemory,
    ) -> str:
        return f"""
Incident Type: {memory.incident_type}
Namespace: {memory.namespace}
Pod: {memory.pod_name}
Severity: {memory.severity}
Failure Reason: {memory.fingerprint.failure_reason or "unknown"}
RCA: {memory.rca_summary}
Remediation: {memory.remediation_summary}
""".strip()

    def index_incident(
        self,
        memory: IncidentMemory,
    ) -> None:
        document = self._build_document(memory)
        embedding = self.embedding_client.embed(document)

        self.upsert(
            incident_id=memory.incident_id,
            document=document,
            embedding=embedding,
            metadata={
                "incident_type": memory.incident_type,
                "namespace": memory.namespace,
                "severity": memory.severity,
                "failure_reason": (
                    memory.fingerprint.failure_reason
                    or "unknown"
                ),
            },
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
