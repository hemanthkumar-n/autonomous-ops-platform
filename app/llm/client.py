from __future__ import annotations

from app.llm.providers.ollama_provider import OllamaProvider


class LLMClient:
    def __init__(self) -> None:
        self.provider = OllamaProvider()

    async def generate(self, prompt: str) -> str:
        return await self.provider.generate(prompt)

    async def close(self) -> None:
        await self.provider.close()