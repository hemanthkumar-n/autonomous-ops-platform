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
