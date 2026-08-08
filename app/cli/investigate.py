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
            if finding.next_explanation:
                click.echo(f"         Why: {finding.next_explanation}")

    if investigation.evidence_gaps:
        click.echo()
        click.echo("Evidence gaps")
        for gap in investigation.evidence_gaps:
            click.echo(f"- {gap}")

    if saved_path:
        click.echo()
        click.echo(f"Memory record: {saved_path}")


@investigate_linux.command("memory")
@click.option(
    "--pid",
    type=click.IntRange(1),
    default=None,
    help="Optional process ID whose cgroup memory evidence should be included.",
)
@click.option(
    "--top",
    type=click.IntRange(1, 100),
    default=10,
    show_default=True,
    help="Maximum memory process records to retain.",
)
@click.option(
    "--recent-minutes",
    type=click.IntRange(1, 10_080),
    default=60,
    show_default=True,
    help="Recent window for kernel OOM evidence.",
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
def investigate_linux_memory(
    pid: int | None,
    top: int,
    recent_minutes: int,
    output_format: str,
    no_persist: bool,
) -> None:
    """
    Diagnose memory pressure, swap activity, OOM, and cgroup memory events.
    """

    from app.orchestration.linux_memory_workflow import (
        run_linux_memory_workflow,
    )

    try:
        investigation, saved_path = run_linux_memory_workflow(
            pid=pid,
            top=top,
            recent_minutes=recent_minutes,
            persist=not no_persist,
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        click.echo(investigation.model_dump_json(indent=2))
        return

    target = f" pid={investigation.pid}" if investigation.pid else ""
    click.echo(
        f"Linux memory investigation: {investigation.severity.upper()} "
        f"host={investigation.hostname}{target}"
    )
    click.echo(
        f"Primary diagnosis: {investigation.primary_diagnosis} "
        f"({investigation.confidence}%)"
    )
    click.echo(investigation.summary)

    if investigation.mem_available_percent is not None:
        click.echo(
            "MemAvailable: "
            f"{investigation.mem_available_percent:.1f}%"
        )
    if investigation.swap_used_percent is not None:
        click.echo(
            "Swap used: "
            f"{investigation.swap_used_percent:.1f}%"
        )
    if (
        investigation.swap_in_per_second is not None
        or investigation.swap_out_per_second is not None
    ):
        click.echo(
            "Swap activity: "
            f"si={investigation.swap_in_per_second or 0} "
            f"so={investigation.swap_out_per_second or 0}"
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
            if finding.next_explanation:
                click.echo(f"         Why: {finding.next_explanation}")

    if investigation.evidence_gaps:
        click.echo()
        click.echo("Evidence gaps")
        for gap in investigation.evidence_gaps:
            click.echo(f"- {gap}")

    if saved_path:
        click.echo()
        click.echo(f"Memory record: {saved_path}")


@investigate_linux.command("cpu")
@click.option(
    "--top",
    type=click.IntRange(1, 100),
    default=10,
    show_default=True,
    help="Maximum CPU process records to retain.",
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
def investigate_linux_cpu(
    top: int,
    output_format: str,
    no_persist: bool,
) -> None:
    """
    Diagnose CPU saturation, high load, D-state tasks, I/O wait, and steal.
    """

    from app.orchestration.linux_cpu_workflow import (
        run_linux_cpu_workflow,
    )

    try:
        investigation, saved_path = run_linux_cpu_workflow(
            top=top,
            persist=not no_persist,
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        click.echo(investigation.model_dump_json(indent=2))
        return

    click.echo(
        f"Linux CPU investigation: {investigation.severity.upper()} "
        f"host={investigation.hostname}"
    )
    click.echo(
        f"Primary diagnosis: {investigation.primary_diagnosis} "
        f"({investigation.confidence}%)"
    )
    click.echo(investigation.summary)

    if investigation.load_average:
        click.echo(
            "Load: "
            f"{investigation.load_average[0]:.2f} "
            f"CPUs={investigation.cpu_count}"
        )
    if investigation.process_states:
        click.echo(
            "Process states: "
            + ", ".join(
                f"{state}={count}"
                for state, count in investigation.process_states.items()
            )
        )
    if investigation.vmstat_cpu:
        click.echo(
            "CPU sample: "
            + " ".join(
                f"{key}={value}"
                for key, value in investigation.vmstat_cpu.items()
            )
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
            if finding.next_explanation:
                click.echo(f"         Why: {finding.next_explanation}")

    if investigation.evidence_gaps:
        click.echo()
        click.echo("Evidence gaps")
        for gap in investigation.evidence_gaps:
            click.echo(f"- {gap}")

    if saved_path:
        click.echo()
        click.echo(f"Memory record: {saved_path}")


@investigate_linux.command("network")
@click.option(
    "--iface",
    help="Optional interface name such as eth0, ens5, bond0, or enp1s0.",
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
def investigate_linux_network(
    iface: str | None,
    output_format: str,
    no_persist: bool,
) -> None:
    """
    Diagnose NIC, route, resolver, and lower-layer network failures.
    """

    from app.orchestration.linux_network_workflow import (
        run_linux_network_workflow,
    )

    try:
        investigation, saved_path = run_linux_network_workflow(
            iface=iface,
            persist=not no_persist,
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        click.echo(investigation.model_dump_json(indent=2))
        return

    target = f" iface={investigation.iface}" if investigation.iface else ""
    click.echo(
        f"Linux network investigation: {investigation.severity.upper()} "
        f"host={investigation.hostname}{target}"
    )
    click.echo(
        f"Primary diagnosis: {investigation.primary_diagnosis} "
        f"({investigation.confidence}%)"
    )
    click.echo(investigation.summary)

    if investigation.nic_signals:
        click.echo(
            "NIC signals: "
            + " ".join(
                f"{key}={value or 'missing'}"
                for key, value in investigation.nic_signals.items()
            )
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
            if finding.next_explanation:
                click.echo(f"         Why: {finding.next_explanation}")

    if investigation.evidence_gaps:
        click.echo()
        click.echo("Evidence gaps")
        for gap in investigation.evidence_gaps:
            click.echo(f"- {gap}")

    if saved_path:
        click.echo()
        click.echo(f"Memory record: {saved_path}")


@investigate_linux.command("service")
@click.option(
    "--service",
    "service_name",
    required=True,
    help="systemd service or unit name, such as nginx or nginx.service.",
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
def investigate_linux_service(
    service_name: str,
    output_format: str,
    no_persist: bool,
) -> None:
    """
    Diagnose systemd failed services and restart-loop evidence.
    """

    from app.orchestration.linux_service_workflow import (
        run_linux_service_workflow,
    )

    try:
        investigation, saved_path = run_linux_service_workflow(
            service=service_name,
            persist=not no_persist,
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        click.echo(investigation.model_dump_json(indent=2))
        return

    click.echo(
        f"Linux service investigation: {investigation.severity.upper()} "
        f"host={investigation.hostname} service={investigation.service}"
    )
    click.echo(
        f"Primary diagnosis: {investigation.primary_diagnosis} "
        f"({investigation.confidence}%)"
    )
    click.echo(investigation.summary)

    if investigation.unit_properties:
        keys = ("ActiveState", "Result", "ExecMainStatus", "NRestarts", "Restart")
        click.echo(
            "Unit: "
            + " ".join(
                f"{key}={investigation.unit_properties.get(key, '')}"
                for key in keys
            )
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
            if finding.next_explanation:
                click.echo(f"         Why: {finding.next_explanation}")

    if investigation.evidence_gaps:
        click.echo()
        click.echo("Evidence gaps")
        for gap in investigation.evidence_gaps:
            click.echo(f"- {gap}")

    if saved_path:
        click.echo()
        click.echo(f"Memory record: {saved_path}")


@investigate.command("k8s-linux")
@click.option(
    "--incident",
    help="Kubernetes symptom or incident type, such as OOMKilled or DiskPressure.",
)
@click.option(
    "--list",
    "list_incidents",
    is_flag=True,
    help="List supported Kubernetes symptoms.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["summary", "json"], case_sensitive=False),
    default="summary",
    show_default=True,
)
def investigate_k8s_linux(
    incident: str | None,
    list_incidents: bool,
    output_format: str,
) -> None:
    """
    Plan Linux evidence for Kubernetes incident symptoms.
    """

    from app.agents.sre.k8s_linux_correlation_agent import (
        correlate_k8s_linux,
        list_k8s_linux_incidents,
    )

    if list_incidents:
        for item in list_k8s_linux_incidents():
            click.echo(item)
        return

    if not incident:
        raise click.UsageError(
            "Provide --incident or use --list to see supported symptoms."
        )

    try:
        plan = correlate_k8s_linux(incident)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        click.echo(plan.model_dump_json(indent=2))
        return

    click.echo(f"Kubernetes to Linux correlation: {plan.incident}")
    click.echo(plan.kubernetes_meaning)

    if plan.linux_evidence:
        click.echo()
        click.echo("Linux evidence to collect")
        for item in plan.linux_evidence:
            click.echo(f"- {item.domain}: {item.reason}")
            for command in item.commands:
                click.echo(f"  command: {command}")

    if plan.next_aop_commands:
        click.echo()
        click.echo("Next AOP commands")
        for command in plan.next_aop_commands:
            click.echo(f"- {command}")

    if plan.kubernetes_checks:
        click.echo()
        click.echo("Kubernetes checks")
        for check in plan.kubernetes_checks:
            click.echo(f"- {check}")

    if plan.cloud_checks:
        click.echo()
        click.echo("Cloud/AWS checks")
        for check in plan.cloud_checks:
            click.echo(f"- {check}")

    if plan.do_not_assume:
        click.echo()
        click.echo("Do not assume")
        for item in plan.do_not_assume:
            click.echo(f"- {item}")

    click.echo()
    click.echo(f"Memory note: {plan.memory_note}")


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
