from __future__ import annotations

import json
from pathlib import Path

import click

from app.llm.model_policy import ReasoningTask, select_model_for_task


@click.group(
    help="AI planning, token-budget, and model-routing helpers.",
)
def ai() -> None:
    """
    AI governance helpers.
    """


@ai.command(
    "budget",
    help="Estimate evidence tokens and show the selected model tier.",
)
@click.option(
    "--task",
    type=click.Choice(
        [
            "classification",
            "summary",
            "normal_rca",
            "deep_rca",
            "remediation",
        ]
    ),
    default="normal_rca",
    show_default=True,
)
@click.option(
    "--text",
    default="",
    help="Evidence text to estimate.",
)
@click.option(
    "--file",
    "file_path",
    type=click.Path(
        exists=True,
        dir_okay=False,
        path_type=Path,
    ),
    help="Evidence file to estimate.",
)
@click.option(
    "--local-only",
    is_flag=True,
    help="Force the local/default model tier.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["summary", "json"]),
    default="summary",
    show_default=True,
)
def budget(
    task: ReasoningTask,
    text: str,
    file_path: Path | None,
    local_only: bool,
    output_format: str,
) -> None:
    evidence_text = text
    if file_path is not None:
        evidence_text = file_path.read_text(encoding="utf-8")

    selection = select_model_for_task(
        task=task,
        evidence_text=evidence_text,
        allow_external=not local_only,
    )

    payload = {
        "task": selection.task,
        "tier": selection.tier,
        "model": selection.model,
        "provider_hint": selection.provider_hint,
        "estimated_input_tokens": selection.budget.estimated_input_tokens,
        "input_token_budget": selection.budget.input_token_budget,
        "output_token_reserve": selection.budget.output_token_reserve,
        "remaining_input_tokens": selection.budget.remaining_input_tokens,
        "within_budget": selection.budget.within_budget,
        "reason": selection.reason,
    }

    if output_format == "json":
        click.echo(json.dumps(payload, indent=2))
        return

    click.echo("AOP AI token budget plan")
    click.echo(f"task: {payload['task']}")
    click.echo(f"tier: {payload['tier']}")
    click.echo(f"model: {payload['model']}")
    click.echo(f"provider_hint: {payload['provider_hint']}")
    click.echo(f"estimated_input_tokens: {payload['estimated_input_tokens']}")
    click.echo(f"input_token_budget: {payload['input_token_budget']}")
    click.echo(f"output_token_reserve: {payload['output_token_reserve']}")
    click.echo(f"within_budget: {payload['within_budget']}")
    click.echo(f"reason: {payload['reason']}")
