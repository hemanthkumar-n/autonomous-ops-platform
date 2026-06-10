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


@investigate.group("linux")
def investigate_linux() -> None:
    """
    Diagnose Linux incidents from bounded, read-only evidence.
    """


@investigate_linux.command("disk")
@click.option(
    "--path",
    "scan_path",
    type=click.Path(
        exists=True,
        file_okay=False,
        path_type=str,
    ),
    default="/",
    show_default=True,
    help="Path whose backing filesystem should be investigated.",
)
@click.option(
    "--top",
    type=click.IntRange(1, 100),
    default=10,
    show_default=True,
    help="Maximum directory and recent-file records to retain.",
)
@click.option(
    "--recent-minutes",
    type=click.IntRange(1, 10_080),
    default=60,
    show_default=True,
    help="Recent-change window for large-file and kernel evidence.",
)
@click.option(
    "--large-size-mb",
    type=click.IntRange(1),
    default=1024,
    show_default=True,
    help="Minimum recent-file size in MiB.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["summary", "json"], case_sensitive=False),
    default="summary",
    show_default=True,
)
@click.option(
    "--no-persist",
    is_flag=True,
    help="Do not save structured or semantic Linux incident memory.",
)
def investigate_linux_disk(
    scan_path: str,
    top: int,
    recent_minutes: int,
    large_size_mb: int,
    output_format: str,
    no_persist: bool,
) -> None:
    """
    Diagnose disk capacity, inode, growth, mount, and storage failures.
    """

    from app.orchestration.linux_disk_workflow import (
        run_linux_disk_workflow,
    )

    try:
        investigation, saved_path = run_linux_disk_workflow(
            scan_path=scan_path,
            top=top,
            recent_minutes=recent_minutes,
            large_size_mb=large_size_mb,
            persist=not no_persist,
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        click.echo(investigation.model_dump_json(indent=2))
        return

    click.echo(
        f"Linux disk investigation: {investigation.severity.upper()} "
        f"host={investigation.hostname} path={investigation.path}"
    )
    click.echo(
        f"Primary diagnosis: {investigation.primary_diagnosis} "
        f"({investigation.confidence}%)"
    )
    click.echo(investigation.summary)

    if investigation.filesystem_use_percent is not None:
        click.echo(
            "Filesystem use: "
            f"{investigation.filesystem_use_percent:.0f}%"
        )
    if investigation.inode_use_percent is not None:
        click.echo(
            f"Inode use: {investigation.inode_use_percent:.0f}%"
        )

    if investigation.findings:
        click.echo()
        click.echo("Findings")
        for finding in investigation.findings:
            click.echo(
                f"{finding.severity.upper():8} "
                f"{finding.code:32} "
                f"{finding.confidence}%"
            )
            click.echo(f"         {finding.summary}")
            click.echo(f"         Next: {finding.next}")

    if investigation.evidence_gaps:
        click.echo()
        click.echo("Evidence gaps")
        for gap in investigation.evidence_gaps:
            click.echo(f"- {gap}")

    if saved_path:
        click.echo()
        click.echo(f"Memory record: {saved_path}")


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
