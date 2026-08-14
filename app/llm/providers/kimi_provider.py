from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.llm.providers.base import LLMProvider
from app.llm.response_validator import validate_llm_response

logger = get_logger(__name__)


class KimiProvider(LLMProvider):
    """
    OpenAI-compatible Moonshot/Kimi provider.

    Secrets are read from configuration and never logged. Ollama remains the
    default provider; this provider is used only when explicitly selected.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.MOONSHOT_API_KEY
        if not self.api_key:
            raise ValueError(
                "MOONSHOT_API_KEY is required when LLM_PROVIDER=kimi"
            )

        self.model = model or settings.KIMI_MODEL_NAME
        self.base_url = (base_url or settings.KIMI_BASE_URL).rstrip("/")

        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(
                connect=10.0,
                read=float(settings.AI_REQUEST_TIMEOUT),
                write=30.0,
                pool=10.0,
            ),
            limits=httpx.Limits(
                max_connections=50,
                max_keepalive_connections=10,
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
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert Site Reliability Engineer. "
                        "Analyze only supplied operational evidence, state "
                        "uncertainty, and never invent commands or facts."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
        }

        logger.info("Submitting request to Kimi model=%s", self.model)
        response = self.client.post(
            "/chat/completions",
            json=payload,
            timeout=timeout or settings.AI_REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        data: dict[str, Any] = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("Invalid Kimi response structure") from exc

        return validate_llm_response(content)

    def healthcheck(self) -> bool:
        try:
            response = self.client.get("/models", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    def close(self) -> None:
        self.client.close()
