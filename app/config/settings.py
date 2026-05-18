import os
from urllib.parse import urlparse

from dotenv import load_dotenv

from app.config.logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)


def _get_bool(value: str, default: bool = False) -> bool:
    """
    Safe boolean parser for environment variables.
    """

    if value is None:
        return default

    return value.lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def _get_int(value: str, default: int) -> int:
    """
    Safe integer parser for environment variables.
    """

    try:
        return int(value)

    except (TypeError, ValueError):
        logger.warning(
            "Invalid integer config detected, using default=%s",
            default,
        )
        return default


def _validate_url(url: str, setting_name: str) -> str:
    """
    Basic URL validation.
    """

    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        raise ValueError(
            f"Invalid URL configuration: {setting_name}"
        )

    return url.rstrip("/")


class Settings:
    """
    Central runtime configuration.
    """

    def __init__(self):
        # =========================
        # Platform identity
        # =========================
        self.PLATFORM_NAME = os.getenv(
            "PLATFORM_NAME",
            "autonomous-ops-platform",
        )

        self.ENVIRONMENT = os.getenv(
            "ENVIRONMENT",
            "development",
        )

        self.WORKFLOW_VERSION = os.getenv(
            "WORKFLOW_VERSION",
            "v1",
        )

        # =========================
        # Prometheus
        # =========================
        self.PROMETHEUS_URL = _validate_url(
            os.getenv(
                "PROMETHEUS_URL",
                "http://localhost:9090",
            ),
            "PROMETHEUS_URL",
        )

        self.PROMETHEUS_TIMEOUT = _get_int(
            os.getenv("PROMETHEUS_TIMEOUT"),
            10,
        )

        self.PROMETHEUS_RETRIES = _get_int(
            os.getenv("PROMETHEUS_RETRIES"),
            3,
        )

        self.ENABLE_METRICS_ENRICHMENT = _get_bool(
            os.getenv("ENABLE_METRICS_ENRICHMENT"),
            True,
        )

        # =========================
        # Kubernetes collection
        # =========================
        self.MAX_LOG_LINES = _get_int(
            os.getenv("MAX_LOG_LINES"),
            50,
        )

        self.ENABLE_POD_LOG_COLLECTION = _get_bool(
            os.getenv("ENABLE_POD_LOG_COLLECTION"),
            True,
        )

        self.ENABLE_EVENT_COLLECTION = _get_bool(
            os.getenv("ENABLE_EVENT_COLLECTION"),
            True,
        )

        # =========================
        # Incident persistence
        # =========================
        self.INCIDENT_HISTORY_DIR = os.getenv(
            "INCIDENT_HISTORY_DIR",
            "data/incidents",
        )

        self.PERSIST_INCIDENTS = _get_bool(
            os.getenv("PERSIST_INCIDENTS"),
            True,
        )

        # =========================
        # AI runtime
        # =========================
        self.OLLAMA_BASE_URL = _validate_url(
            os.getenv(
                "OLLAMA_BASE_URL",
                "http://localhost:11434",
            ),
            "OLLAMA_BASE_URL",
        )

        self.LLM_MODEL_NAME = os.getenv(
            "LLM_MODEL_NAME",
            "qwen2.5-coder:latest",
        )

        self.EMBEDDING_MODEL_NAME = os.getenv(
            "EMBEDDING_MODEL_NAME",
            "nomic-embed-text",
        )

        self.AI_REQUEST_TIMEOUT = _get_int(
            os.getenv("AI_REQUEST_TIMEOUT"),
            180,
        )

        # =========================
        # Vector memory
        # =========================
        self.VECTORSTORE_PROVIDER = os.getenv(
            "VECTORSTORE_PROVIDER",
            "chroma",
        )

        self.VECTORSTORE_PATH = os.getenv(
            "VECTORSTORE_PATH",
            "data/vectorstore/chroma",
        )

        self.VECTORSTORE_COLLECTION_NAME = os.getenv(
            "VECTORSTORE_COLLECTION_NAME",
            "incident_memory",
        )

        # =========================
        # Safety controls
        # =========================
        self.ENABLE_DESTRUCTIVE_REMEDIATION = _get_bool(
            os.getenv("ENABLE_DESTRUCTIVE_REMEDIATION"),
            False,
        )

        self.SAFE_MODE = _get_bool(
            os.getenv("SAFE_MODE"),
            True,
        )

        self.validate()

    def validate(self):
        """
        Runtime config sanity checks.
        """

        if self.PROMETHEUS_TIMEOUT <= 0:
            raise ValueError(
                "PROMETHEUS_TIMEOUT must be > 0"
            )

        if self.AI_REQUEST_TIMEOUT <= 0:
            raise ValueError(
                "AI_REQUEST_TIMEOUT must be > 0"
            )

        if self.MAX_LOG_LINES <= 0:
            raise ValueError(
                "MAX_LOG_LINES must be > 0"
            )

        if not self.VECTORSTORE_PROVIDER:
            raise ValueError(
                "VECTORSTORE_PROVIDER must be configured"
            )

        logger.info(
            "Settings initialized env=%s workflow=%s llm=%s embedding=%s vectorstore=%s",
            self.ENVIRONMENT,
            self.WORKFLOW_VERSION,
            self.LLM_MODEL_NAME,
            self.EMBEDDING_MODEL_NAME,
            self.VECTORSTORE_PROVIDER,
        )


settings = Settings()