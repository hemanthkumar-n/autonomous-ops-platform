from __future__ import annotations

import json

import click


def _echo_json(payload: object) -> None:
    click.echo(json.dumps(payload, indent=2, default=str))


def _echo_result(result: dict) -> None:
    status = result["status"].upper()
    root_note = " [root may be required]" if result["requires_root"] else ""
    click.echo(f"{status:11} {result['label']}{root_note}")
    click.echo(f"  $ {result['command']}")

    if result["output"]:
        click.echo(result["output"])
    if result["error"]:
        click.echo(f"  {result['error']}", err=True)
    click.echo()


def _render_domain(payload: dict) -> None:
    if payload.get("status") == "unsupported":
        click.echo(
            f"Linux {payload['domain']} diagnostics: UNSUPPORTED"
        )
        click.echo(payload["message"])
        return

    click.echo(
        f"Linux {payload['domain']} diagnostics "
        f"host={payload['host']}"
    )
    click.echo()
    for result in payload["results"]:
        _echo_result(result)


@click.group("linux")
def linux() -> None:
    """
    Read-only Linux troubleshooting based on experienced admin workflows.
    """


@linux.command("health")
@click.option("--json", "as_json", is_flag=True)
@click.option(
    "--strict",
    is_flag=True,
    help="Exit non-zero when warning or critical findings exist.",
)
def health(as_json: bool, strict: bool) -> None:
    """
    Show prioritized host, resource, filesystem, and service health.
    """

    from app.tools.linux.operations import collect_health

    payload = collect_health()
    if as_json:
        _echo_json(payload)
    else:
        host = payload["host"]
        click.echo(
            f"Linux health: {payload['status'].upper()} "
            f"host={host['hostname']}"
        )
        click.echo(
            f"Kernel: {host['kernel']}  "
            f"Architecture: {host['architecture']}  "
            f"CPUs: {host['cpu_count']}"
        )
        if host["load_average"]:
            load = host["load_average"]
            click.echo(
                "Load average: "
                f"{load[0]:.2f} {load[1]:.2f} {load[2]:.2f}"
            )

        memory = payload["memory"]
        if memory:
            click.echo(
                "Available memory: "
                f"{memory['available_percent']}%"
            )

        click.echo()
        if payload["findings"]:
            click.echo("Prioritized findings")
            for finding in payload["findings"]:
                click.echo(
                    f"{finding['severity'].upper():8} "
                    f"{finding['area']:10} {finding['summary']}"
                )
                click.echo(f"         Next: {finding['next']}")
        else:
            click.echo("No deterministic warning or critical findings.")

        if payload["services"]["status"] not in {"ok", "unavailable"}:
            click.echo()
            click.echo(
                "Service check: "
                f"{payload['services']['status']} "
                f"{payload['services']['error']}"
            )

    if strict and payload["status"] != "healthy":
        raise click.exceptions.Exit(1)


def _domain_command(name: str, help_text: str):
    def command(
        as_json: bool,
        top: int = 10,
        scan_path: str = "/",
    ) -> None:
        from app.tools.linux.operations import collect_domain

        payload = collect_domain(
            name,
            scan_path=scan_path,
            top=top,
        )
        if as_json:
            _echo_json(payload)
        else:
            _render_domain(payload)

    decorated = click.option(
        "--json",
        "as_json",
        is_flag=True,
    )(command)

    if name in {"cpu", "memory", "processes"}:
        decorated = click.option(
            "--top",
            type=click.IntRange(1, 100),
            default=10,
            show_default=True,
            help="Number of process records to display.",
        )(decorated)

    if name == "disk":
        decorated = click.option(
            "--path",
            "scan_path",
            type=click.Path(
                exists=True,
                file_okay=False,
                path_type=str,
            ),
            default="/",
            show_default=True,
            help="Filesystem path used for bounded directory usage.",
        )(decorated)

    return linux.command(
        name,
        help=help_text,
    )(decorated)


for _name, _help in (
    ("cpu", "Inspect load, CPU topology, run queue, and top consumers."),
    ("memory", "Inspect available memory, swap activity, and top consumers."),
    ("disk", "Inspect capacity, inodes, mounts, growth, and deleted files."),
    ("network", "Inspect link, address, route, DNS, ports, and connections."),
    ("processes", "Inspect process states, hierarchy, age, and resource use."),
    ("services", "Inspect failed and running systemd services."),
    ("logs", "Inspect bounded system, kernel, and authentication logs."),
    ("kernel", "Inspect kernel identity, warnings, and errors."),
    ("boot", "Inspect current and previous boot health."),
    ("security", "Inspect identity and Linux security control status."),
):
    _domain_command(_name, _help)


@linux.command("all")
@click.option("--json", "as_json", is_flag=True)
@click.option("--top", type=click.IntRange(1, 100), default=10)
@click.option(
    "--path",
    "scan_path",
    type=click.Path(exists=True, file_okay=False, path_type=str),
    default="/",
)
def all_diagnostics(as_json: bool, top: int, scan_path: str) -> None:
    """
    Run the baseline Linux health and troubleshooting domains.
    """

    from app.tools.linux.operations import collect_all

    payload = collect_all(scan_path=scan_path, top=top)
    if as_json:
        _echo_json(payload)
        return

    click.echo(
        f"Linux health: {payload['health']['status'].upper()}"
    )
    click.echo()
    for domain_payload in payload["domains"].values():
        _render_domain(domain_payload)
