from __future__ import annotations

import math
import re
from dataclasses import dataclass


_TOKENISH_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


@dataclass(frozen=True)
class TokenBudgetResult:
    """
    Approximate token budget result for prompt planning.

    This is intentionally provider-neutral and deterministic. It is not a
    tokenizer replacement; it is a guardrail that helps AOP avoid sending huge
    raw evidence blobs to an LLM.
    """

    estimated_input_tokens: int
    input_token_budget: int
    output_token_reserve: int
    within_budget: bool
    remaining_input_tokens: int


def estimate_tokens(text: str) -> int:
    """
    Estimate token count without a provider-specific tokenizer.

    The max of token-like splits and character/4 gives a conservative result
    for mixed English text, command output, paths, IPs, IDs, and log lines.
    """

    if not text:
        return 0

    tokenish_count = len(_TOKENISH_PATTERN.findall(text))
    char_estimate = math.ceil(len(text) / 4)
    return max(tokenish_count, char_estimate)


def evaluate_token_budget(
    text: str,
    *,
    input_token_budget: int,
    output_token_reserve: int,
) -> TokenBudgetResult:
    estimated = estimate_tokens(text)
    remaining = max(input_token_budget - estimated, 0)

    return TokenBudgetResult(
        estimated_input_tokens=estimated,
        input_token_budget=input_token_budget,
        output_token_reserve=output_token_reserve,
        within_budget=estimated <= input_token_budget,
        remaining_input_tokens=remaining,
    )


def trim_to_token_budget(
    text: str,
    *,
    input_token_budget: int,
) -> str:
    """
    Return a bounded text block with a visible truncation marker.
    """

    if estimate_tokens(text) <= input_token_budget:
        return text

    character_budget = max(input_token_budget * 4, 0)
    if character_budget <= 0:
        return "[AOP truncated evidence: token budget is zero]"

    trimmed = text[:character_budget].rstrip()
    return (
        f"{trimmed}\n"
        "[AOP truncated evidence: input token budget reached]"
    )
