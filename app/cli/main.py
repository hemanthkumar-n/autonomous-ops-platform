from __future__ import annotations

import click

from app.cli.health import health
from app.cli.investigate import investigate
from app.cli.kubernetes import kubernetes
from app.cli.linux import linux
from app.cli.precheck import precheck
from app.cli.remediate import memory


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
    }
)
@click.version_option(
    version="0.12.0",
    prog_name="aop",
)
def main() -> None:
    """
    Autonomous Ops Platform command line interface.
    """


main.add_command(health)
main.add_command(precheck)
main.add_command(investigate)
main.add_command(memory)
main.add_command(kubernetes)
main.add_command(kubernetes, name="k8s")
main.add_command(linux)


if __name__ == "__main__":
    main()
