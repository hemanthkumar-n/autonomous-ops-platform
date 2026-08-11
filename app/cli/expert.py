from __future__ import annotations

import json

import click


KX_SHORTCUTS = {
    "oom": "OOMKilled",
    "crash": "CrashLoopBackOff",
    "image": "ImagePullBackOff",
    "pull": "ImagePullBackOff",
    "config": "CreateContainerConfigError",
    "runtime": "CreateContainerError",
    "schedule": "FailedScheduling",
    "pending": "FailedScheduling",
    "disk": "DiskPressure",
    "memory": "MemoryPressure",
    "pid": "PIDPressure",
    "node": "NodeNotReady",
    "notready": "NodeNotReady",
    "network": "NetworkUnavailable",
}


def _dump_json(payload) -> None:
    click.echo(
        json.dumps(
            payload,
            indent=2,
            default=str,
        )
    )


@click.group("kx")
def kx() -> None:
    """
    Short Kubernetes expert troubleshooting shortcuts.
    """


@kx.command("list")
def list_shortcuts() -> None:
    """
    List Kubernetes expert shortcuts.
    """

    for shortcut, symptom in sorted(KX_SHORTCUTS.items()):
        click.echo(f"{shortcut:10} -> {symptom}")


@kx.command("explain")
@click.argument("shortcut")
@click.option("--json", "as_json", is_flag=True)
def explain(shortcut: str, as_json: bool) -> None:
    """
    Explain one Kubernetes shortcut.
    """

    from app.agents.sre.k8s_linux_correlation_agent import (
        correlate_k8s_linux,
    )
    from app.agents.sre.kubernetes_issue_training_agent import (
        get_kubernetes_issue_knowledge,
    )

    normalized = shortcut.strip().lower()
    symptom = KX_SHORTCUTS.get(normalized, shortcut)

    try:
        knowledge = get_kubernetes_issue_knowledge(symptom)
    except ValueError as exc:
        supported = ", ".join(sorted(KX_SHORTCUTS))
        raise click.ClickException(
            f"{exc} Shortcuts: {supported}"
        ) from exc

    try:
        correlation = correlate_k8s_linux(symptom)
    except ValueError:
        correlation = None

    if as_json:
        _dump_json(
            {
                "shortcut": normalized,
                "symptom": knowledge.symptom,
                "knowledge": knowledge.model_dump(mode="json"),
                "linux_correlation": (
                    correlation.model_dump(mode="json")
                    if correlation
                    else None
                ),
            }
        )
        return

    click.echo(f"aop kx {normalized} -> {knowledge.symptom}")
    click.echo(knowledge.summary)

    if knowledge.common_causes:
        click.echo()
        click.echo("Top causes")
        for cause in knowledge.common_causes[:5]:
            click.echo(f"- {cause}")

    if knowledge.safe_kubectl_commands:
        click.echo()
        click.echo("Kubernetes checks")
        for command in knowledge.safe_kubectl_commands[:4]:
            click.echo(f"- {command}")

    if correlation and correlation.next_aop_commands:
        click.echo()
        click.echo("Next AOP commands")
        for command in correlation.next_aop_commands:
            click.echo(f"- {command}")
    elif knowledge.safe_aop_commands:
        click.echo()
        click.echo("Next AOP commands")
        for command in knowledge.safe_aop_commands[:4]:
            click.echo(f"- {command}")

    do_not_assume = []
    do_not_assume.extend(knowledge.do_not_assume)
    if correlation:
        do_not_assume.extend(correlation.do_not_assume)
    if do_not_assume:
        click.echo()
        click.echo(f"Do not assume: {do_not_assume[0]}")


def _shortcut_command(shortcut_name: str):
    @click.command(shortcut_name)
    @click.option("--json", "as_json", is_flag=True)
    def shortcut(as_json: bool) -> None:
        explain.callback(shortcut_name, as_json)

    return shortcut


for _shortcut in KX_SHORTCUTS:
    kx.add_command(_shortcut_command(_shortcut))
