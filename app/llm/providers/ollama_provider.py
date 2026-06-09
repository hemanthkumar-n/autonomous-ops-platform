from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.llm.providers.base import LLMProvider
from app.llm.response_validator import validate_llm_response

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    """
    Production-grade Ollama provider.

    Features:
    - connection pooling
    - keepalive reuse
    - retries
    - timeout controls
    """

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")

        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(
                connect=5.0,
                read=float(settings.AI_REQUEST_TIMEOUT),
                write=30.0,
                pool=5.0,
            ),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
            ),
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def generate(
        self,
        prompt: str,
        timeout: int | None = None,
    ) -> str:
        payload = {
            "model": settings.LLM_MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
        }

        logger.info(
            "Submitting request to Ollama model=%s",
            settings.LLM_MODEL_NAME,
        )

        response = self.client.post(
            "/api/generate",
            json=payload,
            timeout=timeout or settings.AI_REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data: dict[str, Any] = response.json()

        return validate_llm_response(
            data.get("response")
        )

    def healthcheck(self) -> bool:
        try:
            response = self.client.get(
                "/api/tags",
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False

    def close(self) -> None:
        self.client.close()
