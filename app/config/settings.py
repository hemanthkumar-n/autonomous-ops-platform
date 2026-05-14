import os
from dotenv import load_dotenv

load_dotenv()


def _get_bool(value: str, default: bool = False) -> bool:
    """
    Safe boolean parser for environment variables.
    """

    if value is None:
        return default

    return value.lower() in ("true", "1", "yes", "on")


class Settings:
    """
    Central runtime configuration for Autonomous Ops Platform.
    Production-safe environment driven settings.
    """

    # =========================
    # Platform identity
    # =========================
    PLATFORM_NAME = os.getenv(
        "PLATFORM_NAME",
        "autonomous-ops-platform"
    )

    ENVIRONMENT = os.getenv(
        "ENVIRONMENT",
        "development"
    )

    WORKFLOW_VERSION = os.getenv(
        "WORKFLOW_VERSION",
        "v1"
    )

    # =========================
    # Prometheus
    # =========================
    PROMETHEUS_URL = os.getenv(
        "PROMETHEUS_URL",
        "http://localhost:9090"
    )

    PROMETHEUS_TIMEOUT = int(
        os.getenv("PROMETHEUS_TIMEOUT", "10")
    )

    PROMETHEUS_RETRIES = int(
        os.getenv("PROMETHEUS_RETRIES", "3")
    )

    ENABLE_METRICS_ENRICHMENT = _get_bool(
        os.getenv("ENABLE_METRICS_ENRICHMENT"),
        True
    )

    # =========================
    # Kubernetes collection
    # =========================
    MAX_LOG_LINES = int(
        os.getenv("MAX_LOG_LINES", "50")
    )

    ENABLE_POD_LOG_COLLECTION = _get_bool(
        os.getenv("ENABLE_POD_LOG_COLLECTION"),
        True
    )

    ENABLE_EVENT_COLLECTION = _get_bool(
        os.getenv("ENABLE_EVENT_COLLECTION"),
        True
    )

    # =========================
    # Incident persistence
    # =========================
    INCIDENT_HISTORY_DIR = os.getenv(
        "INCIDENT_HISTORY_DIR",
        "app/memory/incident_history/incidents"
    )

    PERSIST_INCIDENTS = _get_bool(
        os.getenv("PERSIST_INCIDENTS"),
        True
    )

    # =========================
    # AI runtime
    # =========================
    DEFAULT_LLM_MODEL = os.getenv(
        "DEFAULT_LLM_MODEL",
        "gpt-4o-mini"
    )

    AI_REQUEST_TIMEOUT = int(
        os.getenv("AI_REQUEST_TIMEOUT", "60")
    )

    # =========================
    # Safety controls
    # =========================
    ENABLE_DESTRUCTIVE_REMEDIATION = _get_bool(
        os.getenv("ENABLE_DESTRUCTIVE_REMEDIATION"),
        False
    )

    SAFE_MODE = _get_bool(
        os.getenv("SAFE_MODE"),
        True
    )


settings = Settings()

