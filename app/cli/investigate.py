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
        guidance = _guidance_for_classification(
            workflow,
            classification,
        )
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
        sections.extend(_markdown_guidance(guidance))

    return "\n".join(sections)


def _guidance_for_classification(workflow, classification):
    for guidance in getattr(workflow, "correlation_guidance", []):
        if (
            guidance.namespace == classification.namespace
            and guidance.pod_name == classification.pod_name
            and guidance.container == classification.container
        ):
            return guidance
    return None


def _markdown_guidance(guidance) -> list[str]:
    if guidance is None:
        return []

    sections = [
        "### Kubernetes Knowledge",
        "",
        f"- Symptom: `{guidance.symptom}`",
    ]
    if guidance.kubernetes_knowledge:
        sections.append(f"- Meaning: {guidance.kubernetes_knowledge.summary}")
        if guidance.kubernetes_knowledge.safe_kubectl_commands:
            sections.extend(["", "Safe Kubernetes checks:", ""])
            sections.extend(
                f"- `{command}`"
                for command in guidance.kubernetes_knowledge.safe_kubectl_commands
            )

    if guidance.linux_correlation:
        sections.extend(["", "Linux evidence needed:", ""])
        for command in guidance.linux_correlation.next_aop_commands:
            sections.append(f"- `{command}`")

        if guidance.linux_correlation.do_not_assume:
            sections.extend(["", "Do not assume:", ""])
            sections.extend(
                f"- {item}"
                for item in guidance.linux_correlation.do_not_assume
            )

    if guidance.evidence_gaps:
        sections.extend(["", "Evidence gaps:", ""])
        sections.extend(f"- {gap}" for gap in guidance.evidence_gaps)

    sections.append("")
    return sections


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
        guidance = _guidance_for_classification(
            workflow,
            classification,
        )
        if guidance:
            click.echo(f"  K8s symptom: {guidance.symptom}")
            if guidance.kubernetes_knowledge:
                click.echo(
                    "  Knowledge: "
                    f"{guidance.kubernetes_knowledge.summary}"
                )
            if guidance.linux_correlation:
                click.echo("  Linux evidence needed:")
                for command in guidance.linux_correlation.next_aop_commands:
                    click.echo(f"  - {command}")
                if guidance.linux_correlation.do_not_assume:
                    click.echo(
                        "  Do not assume: "
                        f"{guidance.linux_correlation.do_not_assume[0]}"
                    )
            if guidance.evidence_gaps:
                click.echo("  Evidence gaps:")
                for gap in guidance.evidence_gaps:
                    click.echo(f"  - {gap}")

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
    if investigation.mount_source or investigation.filesystem_type:
        click.echo(
            "Mount: "
            f"source={investigation.mount_source or 'unknown'} "
            f"type={investigation.filesystem_type or 'unknown'} "
            f"target={investigation.mount_point or 'unknown'}"
        )
    if investigation.io_sample:
        click.echo(
            "I/O sample: "
            + " ".join(
                f"{key}={value}"
                for key, value in investigation.io_sample.items()
            )
        )
    if investigation.lvm_volume_groups:
        click.echo(f"LVM volume groups: {len(investigation.lvm_volume_groups)}")
    if investigation.multipath_devices:
        click.echo(f"Multipath records: {len(investigation.multipath_devices)}")
    if investigation.nfs_mounts:
        click.echo(f"NFS mounts: {len(investigation.nfs_mounts)}")

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


@investigate_linux.command("boot")
@click.option(
    "--recent-minutes",
    type=click.IntRange(1, 10_080),
    default=240,
    show_default=True,
    help="Recent window for current-boot kernel evidence.",
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
def investigate_linux_boot(
    recent_minutes: int,
    output_format: str,
    no_persist: bool,
) -> None:
    """
    Diagnose boot, kernel, panic, kdump, and grubby evidence.
    """

    from app.orchestration.linux_boot_kernel_workflow import (
        run_linux_boot_kernel_workflow,
    )

    try:
        investigation, saved_path = run_linux_boot_kernel_workflow(
            recent_minutes=recent_minutes,
            persist=not no_persist,
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        click.echo(investigation.model_dump_json(indent=2))
        return

    click.echo(
        f"Linux boot/kernel investigation: {investigation.severity.upper()} "
        f"host={investigation.hostname}"
    )
    click.echo(
        f"Primary diagnosis: {investigation.primary_diagnosis} "
        f"({investigation.confidence}%)"
    )
    click.echo(investigation.summary)

    if investigation.running_kernel or investigation.default_kernel:
        click.echo(
            "Kernel: "
            f"running={investigation.running_kernel or 'unknown'} "
            f"default={investigation.default_kernel or 'unknown'}"
        )
    if investigation.boot_args:
        click.echo(f"Boot args: {investigation.boot_args}")
    if investigation.kdump_status:
        click.echo(f"kdump: {investigation.kdump_status}")

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


@investigate_linux.command("host")
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
    help="Filesystem path used for disk/storage correlation.",
)
@click.option(
    "--iface",
    help="Optional interface name for network/NIC correlation.",
)
@click.option(
    "--pid",
    type=click.IntRange(1),
    default=None,
    help="Optional PID for cgroup-aware memory correlation.",
)
@click.option(
    "--service",
    "service_name",
    help="Optional systemd service for service-state correlation.",
)
@click.option(
    "--top",
    type=click.IntRange(1, 100),
    default=10,
    show_default=True,
    help="Maximum process/file records retained by child investigations.",
)
@click.option(
    "--recent-minutes",
    type=click.IntRange(1, 10_080),
    default=60,
    show_default=True,
    help="Recent evidence window for child investigations.",
)
@click.option(
    "--large-size-mb",
    type=click.IntRange(1),
    default=1024,
    show_default=True,
    help="Minimum recent-file size in MiB for disk correlation.",
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
    help="Do not save structured or semantic Linux host memory.",
)
def investigate_linux_host(
    scan_path: str,
    iface: str | None,
    pid: int | None,
    service_name: str | None,
    top: int,
    recent_minutes: int,
    large_size_mb: int,
    output_format: str,
    no_persist: bool,
) -> None:
    """
    Correlate disk, memory, CPU, network, boot, and service evidence.
    """

    from app.orchestration.linux_host_workflow import (
        run_linux_host_workflow,
    )

    try:
        investigation, saved_path = run_linux_host_workflow(
            scan_path=scan_path,
            iface=iface,
            pid=pid,
            service=service_name,
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
        f"Linux host investigation: {investigation.severity.upper()} "
        f"host={investigation.hostname} path={investigation.path}"
    )
    click.echo(
        f"Primary diagnosis: {investigation.primary_diagnosis} "
        f"({investigation.confidence}%)"
    )
    click.echo(investigation.summary)

    click.echo()
    click.echo("Domain summary")
    for domain in investigation.domains:
        click.echo(
            f"{domain.severity.upper():8} "
            f"{domain.domain:8} "
            f"{domain.primary_diagnosis:36} "
            f"{domain.confidence}%"
        )
        click.echo(f"         {domain.summary}")

    if investigation.findings:
        click.echo()
        click.echo("Correlated findings")
        for finding in investigation.findings:
            click.echo(
                f"{finding.severity.upper():8} "
                f"{finding.code:40} "
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


@investigate.command("k8s-node")
@click.option(
    "--node",
    required=True,
    help="Kubernetes node name, such as worker-01.",
)
@click.option(
    "--condition",
    "conditions",
    multiple=True,
    help=(
        "Node condition or symptom. Repeat for multiple values, for example "
        "--condition DiskPressure --condition ReadyFalse."
    ),
)
@click.option(
    "--list-conditions",
    is_flag=True,
    help="List supported Kubernetes node conditions.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["summary", "json"], case_sensitive=False),
    default="summary",
    show_default=True,
)
def investigate_k8s_node(
    node: str,
    conditions: tuple[str, ...],
    list_conditions: bool,
    output_format: str,
) -> None:
    """
    Plan Linux host evidence for Kubernetes node conditions.
    """

    from app.agents.sre.k8s_node_linux_agent import (
        list_k8s_node_conditions,
        plan_k8s_node_linux,
    )

    if list_conditions:
        for item in list_k8s_node_conditions():
            click.echo(item)
        return

    try:
        plan = plan_k8s_node_linux(
            node=node,
            conditions=list(conditions) if conditions else None,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        click.echo(plan.model_dump_json(indent=2))
        return

    click.echo(
        f"Kubernetes node Linux plan: {plan.severity.upper()} "
        f"node={plan.node}"
    )
    click.echo(
        f"Primary diagnosis: {plan.primary_diagnosis} "
        f"({plan.confidence}%)"
    )
    click.echo(plan.summary)

    if plan.kubernetes_signals:
        click.echo()
        click.echo("Kubernetes signals")
        for signal in plan.kubernetes_signals:
            click.echo(
                f"- {signal.condition}={signal.status}: {signal.summary}"
            )

    if plan.linux_evidence:
        click.echo()
        click.echo("Linux evidence required")
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


@investigate.command("k8s-knowledge")
@click.option(
    "--symptom",
    help="Kubernetes symptom such as CrashLoopBackOff, OOMKilled, or NodeNotReady.",
)
@click.option(
    "--list",
    "list_symptoms",
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
def investigate_k8s_knowledge(
    symptom: str | None,
    list_symptoms: bool,
    output_format: str,
) -> None:
    """
    Read curated Kubernetes troubleshooting knowledge.
    """

    from app.agents.sre.kubernetes_issue_training_agent import (
        get_kubernetes_issue_knowledge,
        list_kubernetes_issue_symptoms,
    )

    if list_symptoms:
        for item in list_kubernetes_issue_symptoms():
            click.echo(item)
        return

    if not symptom:
        raise click.UsageError(
            "Provide --symptom or use --list to see supported symptoms."
        )

    try:
        knowledge = get_kubernetes_issue_knowledge(symptom)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        click.echo(knowledge.model_dump_json(indent=2))
        return

    click.echo(f"Kubernetes issue knowledge: {knowledge.symptom}")
    click.echo(knowledge.summary)

    sections = [
        ("Common causes", knowledge.common_causes),
        ("Kubernetes evidence", knowledge.kubernetes_evidence),
        ("Linux evidence", knowledge.linux_evidence),
        ("Safe kubectl commands", knowledge.safe_kubectl_commands),
        ("Safe AOP commands", knowledge.safe_aop_commands),
        ("Do not assume", knowledge.do_not_assume),
        ("Escalation signals", knowledge.escalation_signals),
    ]
    for title, values in sections:
        if not values:
            continue
        click.echo()
        click.echo(title)
        for value in values:
            click.echo(f"- {value}")

    if knowledge.sources:
        click.echo()
        click.echo("Sources")
        for source in knowledge.sources:
            click.echo(f"- {source.title}: {source.url}")


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
