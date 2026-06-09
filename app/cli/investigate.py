from __future__ import annotations

import json
from pathlib import Path

import click


def _markdown_report(workflow) -> str:
    sections = [
        "# Autonomous Ops Platform Incident Report",
        "",
        f"Incidents analyzed: {len(workflow.classified_incidents)}",
        "",
    ]

    for incident, classification, rca, remediation in zip(
        workflow.incident_context,
        workflow.classified_incidents,
        workflow.rca_results,
        workflow.remediation_results,
        strict=False,
    ):
        sections.extend(
            [
                f"## {incident.namespace}/{incident.pod_name}",
                "",
                f"- Incident: `{classification.incident_type}`",
                f"- Severity: `{classification.severity}`",
                f"- Confidence: `{classification.confidence}%`",
                f"- Owner: `{classification.recommended_team}`",
                "",
                "### Analysis",
                "",
                rca.rca,
                "",
                "### Remediation",
                "",
                remediation.remediation,
                "",
            ]
        )

    return "\n".join(sections)


def _print_summary(workflow, saved_path: str | None) -> None:
    click.echo()
    click.echo("Incident investigation completed")
    click.echo()

    for classification in workflow.classified_incidents:
        click.echo(
            f"{classification.severity:8} "
            f"{classification.namespace}/{classification.pod_name} "
            f"{classification.incident_type} "
            f"({classification.confidence}%)"
        )

    if saved_path:
        click.echo()
        click.echo(f"Memory record: {saved_path}")


@click.group()
def investigate() -> None:
    """
    Collect evidence and investigate operational incidents.
    """


@investigate.command("k8s")
@click.option(
    "--namespace",
    "-n",
    help="Limit collection to one Kubernetes namespace.",
)
@click.option(
    "--pod",
    help="Limit collection to one pod name.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(
        ["summary", "json", "markdown"],
        case_sensitive=False,
    ),
    default="summary",
    show_default=True,
)
@click.option(
    "--output",
    type=click.Path(
        dir_okay=False,
        path_type=Path,
    ),
    help="Write JSON or Markdown output to a file.",
)
@click.option(
    "--no-persist",
    is_flag=True,
    help="Do not save structured or semantic incident memory.",
)
def investigate_k8s(
    namespace: str | None,
    pod: str | None,
    output_format: str,
    output: Path | None,
    no_persist: bool,
) -> None:
    """
    Investigate unhealthy Kubernetes workloads.
    """

    from app.orchestration.incident_workflow import (
        run_incident_workflow,
    )

    try:
        workflow, saved_path = run_incident_workflow(
            namespace=namespace,
            pod_name=pod,
            persist=not no_persist,
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    if workflow is None:
        click.echo("No active incidents detected.")
        return

    if output_format == "json":
        rendered = json.dumps(
            workflow.model_dump(mode="json"),
            indent=2,
        )
    elif output_format == "markdown":
        rendered = _markdown_report(workflow)
    else:
        rendered = ""

    if output:
        if output_format == "summary":
            raise click.UsageError(
                "--output requires --format json or --format markdown"
            )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        output.write_text(
            rendered,
            encoding="utf-8",
        )
        _print_summary(workflow, saved_path)
        click.echo(f"Report: {output}")
    elif rendered:
        click.echo(rendered)
    else:
        _print_summary(workflow, saved_path)
