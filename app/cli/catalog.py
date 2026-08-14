from __future__ import annotations

import json

import click

from app.tools.troubleshooting.catalog import (
    get_command,
    list_categories,
    list_commands,
    search_commands,
)
from app.tools.troubleshooting.executor import SafeTroubleshootingExecutor


def _echo_json(payload: object) -> None:
    click.echo(json.dumps(payload, indent=2, default=str))


@click.group("catalog")
def catalog() -> None:
    """
    Inspect and safely run known troubleshooting catalog commands.
    """


@catalog.command("list")
@click.option("--domain", type=click.Choice(["linux", "kubernetes"]))
@click.option("--category")
@click.option("--json", "as_json", is_flag=True)
def list_catalog(
    domain: str | None,
    category: str | None,
    as_json: bool,
) -> None:
    """
    List known Linux and Kubernetes troubleshooting commands.
    """

    commands = list_commands(domain=domain, category=category)
    if as_json:
        _echo_json(commands)
        return

    for command in commands:
        root_note = " [root]" if command["requires_root"] else ""
        click.echo(
            f"{command['key']:36} "
            f"{command['domain']:10} "
            f"{command['category']:14} "
            f"{command['risk']:8} "
            f"{command['command']}{root_note}"
        )


@catalog.command("categories")
@click.option("--domain", type=click.Choice(["linux", "kubernetes"]))
@click.option("--json", "as_json", is_flag=True)
def categories(domain: str | None, as_json: bool) -> None:
    """
    List known troubleshooting categories.
    """

    values = list_categories(domain=domain)
    if as_json:
        _echo_json(values)
        return

    for value in values:
        click.echo(value)


@catalog.command("search")
@click.argument("query")
@click.option("--json", "as_json", is_flag=True)
def search(query: str, as_json: bool) -> None:
    """
    Search command keys, descriptions, and guidance.
    """

    results = search_commands(query)
    if as_json:
        _echo_json(results)
        return

    for command in results:
        click.echo(f"{command['key']:36} {command['description']}")


@catalog.command("run")
@click.argument("key")
@click.option("--allow-elevated-read", is_flag=True)
@click.option("--allow-careful-read", is_flag=True)
@click.option("--timeout", type=int, default=10, show_default=True)
@click.option("--json", "as_json", is_flag=True)
def run(
    key: str,
    allow_elevated_read: bool,
    allow_careful_read: bool,
    timeout: int,
    as_json: bool,
) -> None:
    """
    Run one known read-only catalog command by key.
    """

    command = get_command(key)
    result = SafeTroubleshootingExecutor(
        allow_elevated_reads=allow_elevated_read,
        allow_careful_reads=allow_careful_read,
        timeout_seconds=timeout,
    ).execute(command)

    if as_json:
        _echo_json(result.to_dict())
        return

    click.echo(f"{result.status.upper():8} {result.key}")
    click.echo(f"$ {result.command}")
    if result.reason:
        click.echo(f"Reason: {result.reason}")
    if result.output:
        click.echo(result.output)
    if result.error:
        click.echo(result.error, err=True)
