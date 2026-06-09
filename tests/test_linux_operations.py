from __future__ import annotations

import subprocess
import unittest
from unittest.mock import Mock, patch

from app.tools.linux.operations import (
    CommandResult,
    CommandSpec,
    collect_domain,
    domain_specs,
    run_command,
)


class LinuxOperationsTests(unittest.TestCase):
    @patch("app.tools.linux.operations.shutil.which")
    def test_missing_command_is_evidence(
        self,
        which,
    ) -> None:
        which.return_value = None

        result = run_command(
            CommandSpec(
                key="routes",
                label="Routing table",
                argv=("ip", "route"),
            )
        )

        self.assertEqual(result.status, "unavailable")
        self.assertIn("not installed", result.error)

    @patch("app.tools.linux.operations.subprocess.run")
    @patch("app.tools.linux.operations.shutil.which")
    def test_runner_does_not_use_a_shell(
        self,
        which,
        run,
    ) -> None:
        which.return_value = "/usr/bin/uptime"
        run.return_value = Mock(
            returncode=0,
            stdout="up 10 days\n",
            stderr="",
        )

        result = run_command(
            CommandSpec(
                key="uptime",
                label="Uptime",
                argv=("uptime",),
            )
        )

        self.assertEqual(result.status, "ok")
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["/usr/bin/uptime"])
        self.assertFalse(kwargs["shell"])

    @patch("app.tools.linux.operations.subprocess.run")
    @patch("app.tools.linux.operations.shutil.which")
    def test_timeout_is_normalized(
        self,
        which,
        run,
    ) -> None:
        which.return_value = "/usr/bin/vmstat"
        run.side_effect = subprocess.TimeoutExpired(
            cmd=["vmstat"],
            timeout=1,
        )

        result = run_command(
            CommandSpec(
                key="vmstat",
                label="VM activity",
                argv=("vmstat", "1", "3"),
            ),
            timeout=1,
        )

        self.assertEqual(result.status, "timeout")

    @patch(
        "app.tools.linux.operations.platform.system",
        return_value="Linux",
    )
    @patch("app.tools.linux.operations.run_command")
    def test_process_output_honors_top_limit(
        self,
        run_command_mock,
        _platform_system,
    ) -> None:
        run_command_mock.side_effect = lambda spec: CommandResult(
            key=spec.key,
            label=spec.label,
            command=" ".join(spec.argv),
            status="ok",
            output="\n".join(
                ["HEADER", "one", "two", "three", "four"]
            ),
        )

        payload = collect_domain("processes", top=2)

        self.assertEqual(
            payload["results"][0]["output"].splitlines(),
            ["HEADER", "one", "two"],
        )

    def test_network_sequence_starts_with_link_context(self) -> None:
        keys = [spec.key for spec in domain_specs("network")]

        self.assertEqual(
            keys[:4],
            ["addresses", "link_stats", "routes", "neighbors"],
        )


if __name__ == "__main__":
    unittest.main()
