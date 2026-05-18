from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config.logging_config import get_logger
from app.config.settings import settings
from app.llm.response_validator import validate_llm_response
from app.llm.providers.base import LLMProvider

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    """
    Ollama LLM provider implementation.
    """

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL
        self.model_name = settings.LLM_MODEL_NAME
        self.default_timeout = settings.AI_REQUEST_TIMEOUT

        self.session = requests.Session()

        retry_strategy = Retry(
            total=2,
            backoff_factor=2,
            status_forcelist=[
                429,
                500,
                502,
                503,
                504,
            ],
            allowed_methods=["POST"],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10,
        )

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def generate(
        self,
        prompt: str,
        timeout: int | None = None,
    ) -> str:
        """
        Generate response from Ollama.
        """

        endpoint = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }

        effective_timeout = timeout or self.default_timeout

        try:
            logger.info(
                "Submitting request to Ollama model=%s",
                self.model_name,
            )

            response = self.session.post(
                endpoint,
                json=payload,
                timeout=effective_timeout,
            )

            response.raise_for_status()

            result = response.json()

            llm_response = result.get("response")

            validated_response = validate_llm_response(
                llm_response
            )

            logger.info(
                "Ollama response generated successfully"
            )

            return validated_response

        except requests.exceptions.Timeout:
            logger.exception(
                "Ollama request timeout"
            )
            raise

        except requests.exceptions.RequestException:
            logger.exception(
                "Ollama transport failure"
            )
            raise

        except Exception:
            logger.exception(
                "Unexpected Ollama provider failure"
            )
            raise