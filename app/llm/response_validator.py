def validate_llm_response(response: str) -> str:
    """
    Validate LLM response.
    """

    if not response:
        raise ValueError("LLM returned empty response")

    if len(response.strip()) < 50:
        raise ValueError("LLM response too short")

    return response