from __future__ import annotations

from app.config.settings import settings
from app.llm.providers.base import LLMProvider
from app.llm.providers.kimi_provider import KimiProvider
from app.llm.providers.ollama_provider import OllamaProvider


class LLMRouter:
    """
    Resolve the configured provider without coupling agents to vendors.
    """

    def __init__(self, provider_name: str | None = None) -> None:
        self.provider_name = (
            provider_name or settings.LLM_PROVIDER
        ).strip().lower()

    def create_provider(self) -> LLMProvider:
        if self.provider_name == "ollama":
            return OllamaProvider()

        if self.provider_name in {"kimi", "moonshot"}:
            return KimiProvider()

        raise ValueError(
            f"Unsupported LLM_PROVIDER={self.provider_name!r}. "
            "Supported providers: ollama, kimi"
        )


def build_llm_provider(provider_name: str | None = None) -> LLMProvider:
    """
    Convenience factory for agents and CLI workflows.
    """

    return LLMRouter(provider_name).create_provider()
