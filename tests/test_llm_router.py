from __future__ import annotations

import unittest
from unittest.mock import patch

from app.llm.providers.kimi_provider import KimiProvider
from app.llm.providers.ollama_provider import OllamaProvider
from app.llm.router import LLMRouter, build_llm_provider


class LLMRouterTests(unittest.TestCase):
    def test_default_provider_is_ollama(self) -> None:
        provider = build_llm_provider("ollama")

        self.assertIsInstance(provider, OllamaProvider)
        provider.close()

    def test_unknown_provider_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported LLM_PROVIDER"):
            LLMRouter("unknown").create_provider()

    def test_kimi_requires_api_key(self) -> None:
        with patch("app.llm.providers.kimi_provider.settings.MOONSHOT_API_KEY", None):
            with self.assertRaisesRegex(ValueError, "MOONSHOT_API_KEY"):
                LLMRouter("kimi").create_provider()

    def test_kimi_provider_can_be_selected_when_configured(self) -> None:
        with patch(
            "app.llm.providers.kimi_provider.settings.MOONSHOT_API_KEY",
            "test-token",
        ):
            provider = LLMRouter("moonshot").create_provider()

        self.assertIsInstance(provider, KimiProvider)
        provider.close()


if __name__ == "__main__":
    unittest.main()
