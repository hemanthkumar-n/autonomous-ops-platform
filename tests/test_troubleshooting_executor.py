from __future__ import annotations

import subprocess
import unittest
from unittest.mock import Mock, patch

from click.testing import CliRunner

from app.cli.main import main
from app.tools.troubleshooting.catalog import get_command
from app.tools.troubleshooting.executor import SafeTroubleshootingExecutor


class TroubleshootingExecutorTests(unittest.TestCase):
    def test_skips_placeholder_command(self) -> None:
        command = get_command("k8s_node_describe")

        result = SafeTroubleshootingExecutor().execute(command)

        self.assertTrue(result.skipped)
        self.assertEqual(result.status, "skipped")
        self.assertIn("placeholders", result.reason or "")

    def test_skips_careful_command_without_allowance(self) -> None:
        command = get_command("linux_disk_largest_dirs")

        result = SafeTroubleshootingExecutor().execute(command)

        self.assertTrue(result.skipped)
        self.assertIn("careful", result.reason or "")

    @patch("app.tools.troubleshooting.executor.shutil.which")
    @patch("app.tools.troubleshooting.executor.subprocess.run")
    def test_executes_catalog_command_without_shell(
        self,
        run_mock: Mock,
        which_mock: Mock,
    ) -> None:
        which_mock.return_value = "/usr/bin/uptime"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["/usr/bin/uptime"],
            returncode=0,
            stdout="load average: 0.10\n",
            stderr="",
        )
        command = get_command("linux_cpu_load")

        result = SafeTroubleshootingExecutor().execute(command)

        self.assertEqual(result.status, "ok")
        self.assertIn("load average", result.output)
        called_kwargs = run_mock.call_args.kwargs
        self.assertFalse(called_kwargs["shell"])

    def test_catalog_cli_lists_linux_commands(self) -> None:
        result = CliRunner().invoke(main, ["catalog", "list", "--domain", "linux"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("linux_cpu_load", result.output)
        self.assertIn("uptime", result.output)

    def test_catalog_cli_skips_placeholder_run(self) -> None:
        result = CliRunner().invoke(
            main,
            ["catalog", "run", "k8s_node_describe", "--json"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn('"status": "skipped"', result.output)
        self.assertIn("placeholders", result.output)


if __name__ == "__main__":
    unittest.main()
