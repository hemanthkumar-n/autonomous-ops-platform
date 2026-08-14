from __future__ import annotations

from app.llm.providers.base import LLMProvider
from app.llm.router import LLMRouter


class LLMClient:
    def __init__(
        self,
        provider: LLMProvider | None = None,
        provider_name: str | None = None,
    ) -> None:
        self.provider = provider or LLMRouter(provider_name).create_provider()

    def generate(
        self,
        prompt: str,
        timeout: int | None = None,
    ) -> str:
        return self.provider.generate(
            prompt=prompt,
            timeout=timeout,
        )

    def healthcheck(self) -> bool:
        healthcheck = getattr(self.provider, "healthcheck", None)
        return bool(healthcheck and healthcheck())

    def close(self) -> None:
        close = getattr(self.provider, "close", None)
        if close:
            close()
