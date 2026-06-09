from __future__ import annotations

import click

from app.cli.health import collect_health


@click.command()
def precheck() -> None:
    """
    Validate required services before running an investigation.
    """

    checks = collect_health()
    required = {
        name: healthy
        for name, healthy, _ in checks
        if name in {"Kubernetes", "Ollama"}
    }

    for name, healthy, detail in checks:
        status = "OK" if healthy else "UNAVAILABLE"
        click.echo(f"{status:11} {name:14} {detail}")

    if not all(required.values()):
        raise click.ClickException(
            "Kubernetes and Ollama must be available for AI investigation."
        )
