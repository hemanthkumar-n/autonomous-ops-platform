from __future__ import annotations

import click

from app.memory.retrieval.knowledge import (
    format_knowledge_context_for_prompt,
    retrieve_knowledge,
)
from app.schemas.memory import KnowledgeQuery


@click.group("knowledge")
def knowledge() -> None:
    """Search AOP guidance and incident memory through one interface."""


@knowledge.command("search")
@click.option("--domain")
@click.option("--incident-type")
@click.option("--text", default="")
@click.option("--namespace")
@click.option("--workload")
@click.option("--failure-reason")
@click.option("--severity")
@click.option("--evidence-ref", multiple=True)
@click.option("--limit", type=click.IntRange(min=0), default=5, show_default=True)
@click.option(
    "--semantic",
    is_flag=True,
    help="Also query optional embedding/vector memory; deterministic fallback remains active.",
)
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
    namespace: str | None,
    workload: str | None,
    failure_reason: str | None,
    severity: str | None,
    evidence_ref: tuple[str, ...],
    limit: int,
    semantic: bool,
    output_format: str,
) -> None:
    """Retrieve bounded, provenance-bearing operational knowledge."""

    result = retrieve_knowledge(
        KnowledgeQuery(
            domain=domain,
            incident_type=incident_type,
            text=text,
            namespace=namespace,
            workload_name=workload,
            failure_reason=failure_reason,
            severity=severity,
            evidence_references=list(evidence_ref),
            limit=limit,
        ),
        include_semantic=semantic,
    )
    if output_format == "json":
        click.echo(result.model_dump_json(indent=2))
        return
    if output_format == "prompt":
        click.echo(format_knowledge_context_for_prompt(result))
        return

    click.echo("AOP unified knowledge retrieval")
    click.echo(f"total_matches: {result.total_matches}")
    click.echo(f"returned_matches: {len(result.matches)}")
    click.echo(f"source_counts: {result.source_counts}")
    click.echo(f"semantic_attempted: {result.semantic_attempted}")
    if result.unavailable_sources:
        click.echo(f"unavailable_sources: {', '.join(result.unavailable_sources)}")
    click.echo("boundary: Retrieved knowledge is not proof; verify live evidence.")
    for match in result.matches:
        click.echo()
        click.echo(f"- {match.title}")
        click.echo(f"  id: {match.knowledge_id}")
        click.echo(f"  provenance: {match.source_type}/{match.trust_level}")
        click.echo(f"  source: {match.source or 'local source-controlled knowledge'}")
        click.echo(f"  score: {match.score}")
        click.echo(f"  summary: {match.summary}")
