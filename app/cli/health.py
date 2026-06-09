from __future__ import annotations

from pathlib import Path

import click
import requests
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException


def collect_health() -> list[tuple[str, bool, str]]:
    """
    Check the external services required by the showcase workflow.
    """

    checks = []

    from app.config.settings import settings

    try:
        try:
            config.load_kube_config()
        except ConfigException:
            config.load_incluster_config()

        version = client.VersionApi().get_code()
        checks.append(
            (
                "Kubernetes",
                True,
                f"{version.git_version}",
            )
        )
    except Exception as exc:
        checks.append(("Kubernetes", False, str(exc)))

    try:
        response = requests.get(
            f"{settings.PROMETHEUS_URL}/-/ready",
            timeout=settings.PROMETHEUS_TIMEOUT,
        )
        checks.append(
            (
                "Prometheus",
                response.ok,
                f"HTTP {response.status_code}",
            )
        )
    except Exception as exc:
        checks.append(("Prometheus", False, str(exc)))

    try:
        response = requests.get(
            f"{settings.OLLAMA_BASE_URL}/api/tags",
            timeout=5,
        )
        checks.append(
            (
                "Ollama",
                response.ok,
                f"HTTP {response.status_code}",
            )
        )
    except Exception as exc:
        checks.append(("Ollama", False, str(exc)))

    vector_path = Path(settings.VECTORSTORE_PATH)
    checks.append(
        (
            "Vector memory",
            True,
            (
                f"{vector_path} (ready)"
                if vector_path.exists()
                else f"{vector_path} (created on first use)"
            ),
        )
    )

    return checks


@click.command()
@click.option(
    "--strict",
    is_flag=True,
    help="Exit non-zero when any dependency is unavailable.",
)
def health(strict: bool) -> None:
    """
    Check Kubernetes, Prometheus, Ollama, and local memory.
    """

    checks = collect_health()

    click.echo("Autonomous Ops Platform health")
    click.echo()

    for name, healthy, detail in checks:
        status = "OK" if healthy else "UNAVAILABLE"
        click.echo(f"{status:11} {name:14} {detail}")

    if strict and not all(item[1] for item in checks):
        raise click.exceptions.Exit(1)
