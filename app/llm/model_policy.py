from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.config.settings import settings
from app.llm.token_budget import TokenBudgetResult, evaluate_token_budget

ReasoningTask = Literal[
    "classification",
    "summary",
    "normal_rca",
    "deep_rca",
    "remediation",
]


@dataclass(frozen=True)
class ModelTier:
    name: str
    provider_hint: str
    input_token_budget: int
    output_token_reserve: int
    purpose: str


@dataclass(frozen=True)
class ModelSelection:
    task: ReasoningTask
    tier: str
    model: str
    provider_hint: str
    budget: TokenBudgetResult
    reason: str


def configured_model_tiers() -> dict[str, ModelTier]:
    return {
        "local": ModelTier(
            name=settings.LLM_MODEL_NAME,
            provider_hint=settings.LLM_PROVIDER,
            input_token_budget=settings.AI_STANDARD_INPUT_TOKEN_BUDGET,
            output_token_reserve=1500,
            purpose="safe local/default reasoning",
        ),
        "light": ModelTier(
            name=settings.AI_LIGHT_MODEL_NAME,
            provider_hint="external-light",
            input_token_budget=settings.AI_LIGHT_INPUT_TOKEN_BUDGET,
            output_token_reserve=1000,
            purpose="classification, summarization, and routing",
        ),
        "standard": ModelTier(
            name=settings.AI_STANDARD_MODEL_NAME,
            provider_hint="external-standard",
            input_token_budget=settings.AI_STANDARD_INPUT_TOKEN_BUDGET,
            output_token_reserve=2000,
            purpose="normal incident RCA and recommendations",
        ),
        "deep": ModelTier(
            name=settings.AI_DEEP_MODEL_NAME,
            provider_hint="external-deep",
            input_token_budget=settings.AI_DEEP_INPUT_TOKEN_BUDGET,
            output_token_reserve=4000,
            purpose="complex multi-signal enterprise investigation",
        ),
    }


def select_model_for_task(
    *,
    task: ReasoningTask,
    evidence_text: str,
    allow_external: bool = True,
) -> ModelSelection:
    """
    Select a model tier from task intent and estimated evidence size.

    This does not call any provider. It is governance metadata for future
    routing, prompt compression, cost control, and audit logging.
    """

    tiers = configured_model_tiers()

    if not allow_external or task == "remediation":
        return _selection(
            task=task,
            tier_name="local",
            tier=tiers["local"],
            evidence_text=evidence_text,
            reason="local/default model selected for safety or offline mode",
        )

    estimated_tokens = evaluate_token_budget(
        evidence_text,
        input_token_budget=tiers["deep"].input_token_budget,
        output_token_reserve=tiers["deep"].output_token_reserve,
    ).estimated_input_tokens

    if task in {"classification", "summary"}:
        tier_name = (
            "light"
            if estimated_tokens <= tiers["light"].input_token_budget
            else "standard"
        )
        return _selection(
            task=task,
            tier_name=tier_name,
            tier=tiers[tier_name],
            evidence_text=evidence_text,
            reason="lightweight task selected from classification/summary intent",
        )

    if task == "normal_rca" and estimated_tokens <= tiers["standard"].input_token_budget:
        return _selection(
            task=task,
            tier_name="standard",
            tier=tiers["standard"],
            evidence_text=evidence_text,
            reason="standard model selected for normal RCA within budget",
        )

    return _selection(
        task=task,
        tier_name="deep",
        tier=tiers["deep"],
        evidence_text=evidence_text,
        reason="deep model selected for complex task or large evidence",
    )


def _selection(
    *,
    task: ReasoningTask,
    tier_name: str,
    tier: ModelTier,
    evidence_text: str,
    reason: str,
) -> ModelSelection:
    return ModelSelection(
        task=task,
        tier=tier_name,
        model=tier.name,
        provider_hint=tier.provider_hint,
        budget=evaluate_token_budget(
            evidence_text,
            input_token_budget=tier.input_token_budget,
            output_token_reserve=tier.output_token_reserve,
        ),
        reason=reason,
    )
