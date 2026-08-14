from __future__ import annotations

import json

import click

from app.memory.runbooks.catalog import list_runbook_chunks
from app.memory.runbooks.retrieval import (
    format_runbook_context_for_prompt,
    search_runbooks,
)
from app.schemas.memory import RunbookQuery


def _echo_json(payload: object) -> None:
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump()
    click.echo(json.dumps(payload, indent=2, default=str))


@click.group("runbooks")
def runbooks() -> None:
    """
    Retrieve trusted runbook snippets for bounded RAG context.
    """


@runbooks.command("list")
@click.option("--domain")
@click.option("--incident-type")
@click.option("--json", "as_json", is_flag=True)
def list_chunks(
    domain: str | None,
    incident_type: str | None,
    as_json: bool,
) -> None:
    """
    List source-controlled runbook chunks.
    """

    chunks = list_runbook_chunks(
        domain=domain,
        incident_type=incident_type,
    )
    if as_json:
        _echo_json([chunk.model_dump() for chunk in chunks])
        return

    for chunk in chunks:
        click.echo(f"{chunk.runbook_id:40} {chunk.domain:16} {chunk.title}")


@runbooks.command("search")
@click.option("--domain")
@click.option("--incident-type")
@click.option("--text", default="")
@click.option("--limit", type=int, default=3, show_default=True)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["summary", "json", "prompt"]),
    default="summary",
    show_default=True,
)
def search(
    domain: str | None,
    incident_type: str | None,
    text: str,
    limit: int,
    output_format: str,
) -> None:
    """
    Search trusted runbook chunks by domain, incident type, and text.
    """

    result = search_runbooks(
        RunbookQuery(
            domain=domain,
            incident_type=incident_type,
            text=text,
            limit=limit,
        )
    )

    if output_format == "json":
        _echo_json(result)
        return

    if output_format == "prompt":
        click.echo(format_runbook_context_for_prompt(result))
        return

    click.echo("AOP runbook retrieval")
    click.echo(f"total_matches: {result.total_matches}")
    click.echo(
        "boundary: Runbook match is guidance, not proof. Verify with live evidence."
    )
    for match in result.matches:
        chunk = match.chunk
        click.echo()
        click.echo(f"- {chunk.title}")
        click.echo(f"  id: {chunk.runbook_id}/{chunk.chunk_id}")
        click.echo(f"  domain: {chunk.domain}")
        click.echo(f"  score: {match.score}")
        click.echo(f"  matched: {', '.join(match.matched_terms) or 'none'}")
        click.echo(f"  summary: {chunk.summary}")
