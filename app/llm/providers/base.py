from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Abstract contract for all LLM providers.

    Every provider implementation must expose
    the same deterministic generation interface.

    This prevents agent coupling to provider-specific
    transport logic, endpoints, or authentication details.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        timeout: int | None = None,
    ) -> str:
        """
        Generate LLM response.

        Args:
            prompt:
                Fully constructed prompt.

            timeout:
                Optional request timeout override.

        Returns:
            Generated model response text.

        Raises:
            Provider-specific exceptions should be handled
            internally and surfaced as platform-safe failures.
        """
        raise NotImplementedError
