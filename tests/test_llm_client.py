from __future__ import annotations

import unittest

from app.llm.client import LLMClient
from app.llm.providers.base import LLMProvider


class FakeProvider(LLMProvider):
    def __init__(self) -> None:
        self.closed = False

    def generate(
        self,
        prompt: str,
        timeout: int | None = None,
    ) -> str:
        return f"{prompt}:{timeout}"

    def close(self) -> None:
        self.closed = True


class LLMClientTests(unittest.TestCase):
    def test_uses_synchronous_provider_contract(self) -> None:
        provider = FakeProvider()
        client = LLMClient(provider)

        self.assertEqual(
            client.generate("diagnose", timeout=10),
            "diagnose:10",
        )

        client.close()
        self.assertTrue(provider.closed)


if __name__ == "__main__":
    unittest.main()
