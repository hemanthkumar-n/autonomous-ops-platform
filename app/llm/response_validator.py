from __future__ import annotations


def validate_llm_response(
    response: str | None,
) -> str:
    """
    Validate LLM response safely.
    """

    if response is None:
        raise ValueError(
            "LLM returned empty response"
        )

    if not isinstance(response, str):
        raise ValueError(
            "LLM returned invalid response type"
        )

    cleaned = response.strip()

    if not cleaned:
        raise ValueError(
            "LLM returned blank response"
        )

    return cleaned
