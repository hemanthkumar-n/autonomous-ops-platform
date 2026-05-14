from __future__ import annotations

from app.config.logging_config import get_logger
from app.llm.providers.base import LLMProvider
from app.llm.providers.ollama_provider import OllamaProvider

logger = get_logger(__name__)


class LLMClient:
    """
    Central platform LLM access layer.

    Agents interact only with this client.

    Provider implementations remain hidden behind
    the provider abstraction contract.

    Future evolution:
    - provider routing
    - fallback providers
    - retry orchestration
    - model governance
    - policy enforcement
    - cost controls
    - observability
    """

    def __init__(
        self,
        provider: LLMProvider | None = None,
    ) -> None:
        self.provider = provider or OllamaProvider()

    def generate(
        self,
        prompt: str,
        timeout: int | None = None,
    ) -> str:
        """
        Generate LLM response using configured provider.
        """

        logger.info(
            "LLM client request using provider=%s",
            self.provider.__class__.__name__,
        )

        return self.provider.generate(
            prompt=prompt,
            timeout=timeout,
        )
