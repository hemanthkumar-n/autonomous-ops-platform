from __future__ import annotations

import click

from app.schemas.memory import MemoryQuery


@click.group()
def memory() -> None:
    """
    Search the platform's operational incident memory.
    """


@memory.command("search")
@click.option("--incident-type")
@click.option("--namespace", "-n")
@click.option("--workload")
@click.option("--failure-reason")
@click.option("--severity")
@click.option("--limit", type=click.IntRange(1, 100), default=5)
def search(
    incident_type: str | None,
    namespace: str | None,
    workload: str | None,
    failure_reason: str | None,
    severity: str | None,
    limit: int,
) -> None:
    """
    Search deterministic structured incident history.
    """

    from app.memory.retrieval.search import (
        search_incident_memory,
    )

    query = MemoryQuery(
        incident_type=incident_type,
        namespace=namespace,
        workload_name=workload,
        failure_reason=failure_reason,
        severity=severity,
        limit=limit,
    )
    results = search_incident_memory(query)
    click.echo(results.model_dump_json(indent=2))


@memory.command("patterns")
@click.option("--domain")
@click.option("--incident-type")
@click.option("--min-count", type=click.IntRange(1, 100), default=2)
@click.option("--limit", type=click.IntRange(1, 100), default=10)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["summary", "json"]),
    default="summary",
    show_default=True,
)
def patterns(
    domain: str | None,
    incident_type: str | None,
    min_count: int,
    limit: int,
    output_format: str,
) -> None:
    """
    Show recurring incident patterns from structured memory.
    """

    from app.memory.incident_patterns.patterns import find_incident_patterns

    report = find_incident_patterns(
        min_count=min_count,
        limit=limit,
        domain=domain,
        incident_type=incident_type,
    )

    if output_format == "json":
        click.echo(report.model_dump_json(indent=2))
        return

    click.echo("AOP incident patterns")
    click.echo(f"min_count: {report.min_count}")
    click.echo(f"total_occurrences: {report.total_occurrences}")
    click.echo(f"total_patterns: {report.total_patterns}")

    if not report.patterns:
        click.echo("No recurring patterns found.")
        return

    for pattern in report.patterns:
        click.echo("")
        click.echo(f"fingerprint: {pattern.fingerprint}")
        click.echo(f"domain: {pattern.domain}")
        click.echo(f"incident_type: {pattern.incident_type}")
        click.echo(f"occurrences: {pattern.occurrence_count}")
        click.echo(f"latest: {pattern.latest_timestamp.isoformat()}")
        click.echo(f"resources: {', '.join(pattern.resources)}")
        click.echo(f"severities: {', '.join(pattern.severities)}")

        latest = pattern.occurrences[0]
        click.echo(f"latest_summary: {latest.summary}")
