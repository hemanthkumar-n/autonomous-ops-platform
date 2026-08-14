from __future__ import annotations

import click

from app.cli.ai import ai
from app.cli.catalog import catalog
from app.cli.health import health
from app.cli.investigate import investigate
from app.cli.knowledge import knowledge
from app.cli.kubernetes import kubernetes
from app.cli.linux import linux
from app.cli.expert import kx, lx
from app.cli.precheck import precheck
from app.cli.remediate import memory
from app.cli.runbooks import runbooks


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
    }
)
@click.version_option(
    version="0.41.0",
    prog_name="aop",
)
def main() -> None:
    """
    Autonomous Ops Platform command line interface.
    """


main.add_command(health)
main.add_command(ai)
main.add_command(catalog)
main.add_command(precheck)
main.add_command(investigate)
main.add_command(knowledge)
main.add_command(memory)
main.add_command(runbooks)
main.add_command(kubernetes)
main.add_command(kubernetes, name="k8s")
main.add_command(linux)
main.add_command(kx)
main.add_command(lx)


if __name__ == "__main__":
    main()
