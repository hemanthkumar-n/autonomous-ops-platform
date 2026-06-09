from __future__ import annotations

import json
from pathlib import Path

import click


def _echo_json(payload) -> None:
    click.echo(
        json.dumps(
            payload,
            indent=2,
            default=str,
        )
    )


def _echo_table(
    headers: list[str],
    rows: list[list[object]],
) -> None:
    if not rows:
        click.echo("No matching results.")
        return

    widths = [
        max(
            len(str(header)),
            max(len(str(row[index])) for row in rows),
        )
        for index, header in enumerate(headers)
    ]
    click.echo(
        "  ".join(
            str(header).ljust(widths[index])
            for index, header in enumerate(headers)
        )
    )
    click.echo(
        "  ".join("-" * width for width in widths)
    )

    for row in rows:
        click.echo(
            "  ".join(
                str(value).ljust(widths[index])
                for index, value in enumerate(row)
            )
        )


def _command_error(exc: Exception) -> click.ClickException:
    return click.ClickException(str(exc))


def _shorten(value: object, limit: int = 100) -> str:
    text = str(value).replace("\n", " ")
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


@click.group("kb")
def kubernetes() -> None:
    """
    Fast, read-only Kubernetes troubleshooting commands.
    """


@kubernetes.command("health")
@click.option("--namespace", "-n")
@click.option("--json", "as_json", is_flag=True)
def health(namespace: str | None, as_json: bool) -> None:
    """
    Show node readiness and unhealthy workload summary.
    """

    from app.tools.kubernetes.operations import cluster_health

    try:
        result = cluster_health(namespace)
    except Exception as exc:
        raise _command_error(exc) from exc

    if as_json:
        _echo_json(result)
        return

    click.echo(
        f"Kubernetes {result['version']} "
        f"scope={result['namespace']}"
    )
    click.echo(
        f"Nodes: {result['nodes']['ready']}/"
        f"{result['nodes']['total']} ready"
    )
    click.echo(
        f"Pods: {result['pods']['healthy']} healthy, "
        f"{result['pods']['unhealthy']} unhealthy, "
        f"{result['pods']['total']} total"
    )

    if result["pods"]["items"]:
        click.echo()
        click.echo("Unhealthy pods")
        _echo_table(
            ["NAMESPACE", "POD", "READY", "STATUS", "RESTARTS", "NODE"],
            [
                [
                    pod["namespace"],
                    pod["pod"],
                    pod["ready"],
                    pod["status"],
                    pod["restarts"],
                    pod["node"],
                ]
                for pod in result["pods"]["items"]
            ],
        )


@kubernetes.command("nodes")
@click.option("--json", "as_json", is_flag=True)
def nodes(as_json: bool) -> None:
    """
    Show node readiness, pressure, and capacity.
    """

    from app.tools.kubernetes.operations import list_nodes

    try:
        result = list_nodes()
    except Exception as exc:
        raise _command_error(exc) from exc

    if as_json:
        _echo_json(result)
        return

    _echo_table(
        ["NODE", "READY", "PRESSURE", "CPU", "MEMORY", "PODS", "KUBELET", "AGE"],
        [
            [
                node["node"],
                node["ready"],
                node["pressure"],
                node["cpu"],
                node["memory"],
                node["pods"],
                node["kubelet"],
                node["age"],
            ]
            for node in result
        ],
    )


@kubernetes.command("namespaces")
@click.option("--json", "as_json", is_flag=True)
def namespaces(as_json: bool) -> None:
    """
    List Kubernetes namespaces.
    """

    from app.tools.kubernetes.operations import list_namespaces

    try:
        result = list_namespaces()
    except Exception as exc:
        raise _command_error(exc) from exc

    if as_json:
        _echo_json(result)
        return

    _echo_table(
        ["NAMESPACE", "PHASE", "AGE"],
        [
            [
                item["namespace"],
                item["phase"],
                item["age"],
            ]
            for item in result
        ],
    )


@kubernetes.command("deployments")
@click.option("--namespace", "-n")
@click.option(
    "--all",
    "include_healthy",
    is_flag=True,
    help="Include healthy deployments. Default shows unhealthy deployments.",
)
@click.option("--json", "as_json", is_flag=True)
def deployments(
    namespace: str | None,
    include_healthy: bool,
    as_json: bool,
) -> None:
    """
    Show deployment replica health.
    """

    from app.tools.kubernetes.operations import list_deployments

    try:
        result = list_deployments(namespace)
    except Exception as exc:
        raise _command_error(exc) from exc

    if not include_healthy:
        result = [
            deployment
            for deployment in result
            if not deployment["healthy"]
        ]

    if as_json:
        _echo_json(result)
        return

    _echo_table(
        ["NAMESPACE", "DEPLOYMENT", "READY", "AVAILABLE", "UPDATED", "AGE"],
        [
            [
                item["namespace"],
                item["deployment"],
                item["ready"],
                item["available"],
                item["updated"],
                item["age"],
            ]
            for item in result
        ],
    )


@kubernetes.command("services")
@click.option("--namespace", "-n")
@click.option("--json", "as_json", is_flag=True)
def services(
    namespace: str | None,
    as_json: bool,
) -> None:
    """
    Show service types, addresses, and ports.
    """

    from app.tools.kubernetes.operations import list_services

    try:
        result = list_services(namespace)
    except Exception as exc:
        raise _command_error(exc) from exc

    if as_json:
        _echo_json(result)
        return

    _echo_table(
        ["NAMESPACE", "SERVICE", "TYPE", "CLUSTER-IP", "EXTERNAL", "PORTS", "AGE"],
        [
            [
                item["namespace"],
                item["service"],
                item["type"],
                item["cluster_ip"],
                item["external"],
                item["ports"],
                item["age"],
            ]
            for item in result
        ],
    )


@kubernetes.command("pods")
@click.option("--namespace", "-n")
@click.option(
    "--all",
    "include_healthy",
    is_flag=True,
    help="Include healthy pods. Default shows unhealthy pods only.",
)
@click.option(
    "--system",
    is_flag=True,
    help="Include Kubernetes system namespaces.",
)
@click.option("--json", "as_json", is_flag=True)
def pods(
    namespace: str | None,
    include_healthy: bool,
    system: bool,
    as_json: bool,
) -> None:
    """
    List unhealthy pods, or all pods with --all.
    """

    from app.tools.kubernetes.operations import list_pods

    try:
        result = list_pods(
            namespace=namespace,
            unhealthy_only=not include_healthy,
            include_system=system,
        )
    except Exception as exc:
        raise _command_error(exc) from exc

    if as_json:
        _echo_json(result)
        return

    _echo_table(
        ["NAMESPACE", "POD", "READY", "STATUS", "RESTARTS", "NODE", "AGE"],
        [
            [
                pod["namespace"],
                pod["pod"],
                pod["ready"],
                pod["status"],
                pod["restarts"],
                pod["node"],
                pod["age"],
            ]
            for pod in result
        ],
    )


@kubernetes.command("events")
@click.option("--namespace", "-n")
@click.option(
    "--all",
    "include_normal",
    is_flag=True,
    help="Include Normal events. Default shows warnings only.",
)
@click.option("--limit", type=click.IntRange(1, 200), default=20)
@click.option("--json", "as_json", is_flag=True)
def events(
    namespace: str | None,
    include_normal: bool,
    limit: int,
    as_json: bool,
) -> None:
    """
    Show recent warning events.
    """

    from app.tools.kubernetes.operations import list_events

    try:
        result = list_events(
            namespace=namespace,
            warnings_only=not include_normal,
            limit=limit,
        )
    except Exception as exc:
        raise _command_error(exc) from exc

    if as_json:
        _echo_json(result)
        return

    _echo_table(
        ["NAMESPACE", "TYPE", "REASON", "OBJECT", "MESSAGE"],
        [
            [
                event["namespace"],
                event["type"],
                event["reason"],
                event["object"],
                _shorten(event["message"]),
            ]
            for event in result
        ],
    )


@kubernetes.command("logs")
@click.argument("pod")
@click.option("--namespace", "-n", default="default", show_default=True)
@click.option("--container", "-c")
@click.option("--tail", type=click.IntRange(1, 10000), default=100)
@click.option(
    "--previous",
    is_flag=True,
    help="Read logs from the previous container instance.",
)
def logs(
    pod: str,
    namespace: str,
    container: str | None,
    tail: int,
    previous: bool,
) -> None:
    """
    Show bounded pod logs.
    """

    from app.tools.kubernetes.operations import get_logs

    try:
        result = get_logs(
            pod_name=pod,
            namespace=namespace,
            container=container,
            tail_lines=tail,
            previous=previous,
        )
    except Exception as exc:
        raise _command_error(exc) from exc

    click.echo(result)


@kubernetes.command("describe")
@click.argument("pod")
@click.option("--namespace", "-n", default="default", show_default=True)
@click.option("--json", "as_json", is_flag=True)
def describe(
    pod: str,
    namespace: str,
    as_json: bool,
) -> None:
    """
    Show normalized pod state, resources, and events.
    """

    from app.tools.kubernetes.operations import describe_pod

    try:
        result = describe_pod(
            pod_name=pod,
            namespace=namespace,
        )
    except Exception as exc:
        raise _command_error(exc) from exc

    if as_json:
        _echo_json(result)
        return

    click.echo(
        f"Pod: {result['namespace']}/{result['pod']}"
    )
    click.echo(
        f"Phase: {result['phase']}  "
        f"Node: {result['node'] or '-'}  "
        f"Pod IP: {result['pod_ip'] or '-'}"
    )
    click.echo()
    click.echo("Containers")
    _echo_table(
        ["NAME", "READY", "STATE", "RESTARTS", "IMAGE"],
        [
            [
                container["name"],
                container["ready"],
                container["state"],
                container["restarts"],
                container["image"] or "-",
            ]
            for container in result["containers"]
        ],
    )

    if result["events"]:
        click.echo()
        click.echo("Events")
        _echo_table(
            ["TYPE", "REASON", "MESSAGE"],
            [
                [
                    event["type"],
                    event["reason"],
                    _shorten(event["message"]),
                ]
                for event in result["events"]
            ],
        )


@kubernetes.command("investigate")
@click.option("--namespace", "-n")
@click.option("--pod")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["summary", "json", "markdown"]),
    default="summary",
)
@click.option(
    "--output",
    type=click.Path(
        dir_okay=False,
        path_type=Path,
    ),
)
@click.option("--no-persist", is_flag=True)
@click.pass_context
def investigate(
    context: click.Context,
    namespace: str | None,
    pod: str | None,
    output_format: str,
    output: Path | None,
    no_persist: bool,
) -> None:
    """
    Run the full AI and memory-aware Kubernetes investigation.
    """

    from app.cli.investigate import investigate_k8s

    context.invoke(
        investigate_k8s,
        namespace=namespace,
        pod=pod,
        output_format=output_format,
        output=output,
        no_persist=no_persist,
    )


kubernetes.add_command(nodes, name="no")
kubernetes.add_command(namespaces, name="ns")
kubernetes.add_command(deployments, name="deploy")
kubernetes.add_command(services, name="svc")
kubernetes.add_command(pods, name="po")
kubernetes.add_command(events, name="ev")
kubernetes.add_command(logs, name="log")
kubernetes.add_command(describe, name="desc")
kubernetes.add_command(investigate, name="inv")
