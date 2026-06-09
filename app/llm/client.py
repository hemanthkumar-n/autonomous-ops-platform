from __future__ import annotations

from app.llm.providers.base import LLMProvider
from app.llm.providers.ollama_provider import OllamaProvider


class LLMClient:
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
        return self.provider.generate(
            prompt=prompt,
            timeout=timeout,
        )

    def close(self) -> None:
        close = getattr(self.provider, "close", None)
        if close:
            close()
