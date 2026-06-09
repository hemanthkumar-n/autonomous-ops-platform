from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from app.cli.main import main


class LinuxCLITests(unittest.TestCase):
    def test_exposes_linux_commands(self) -> None:
        result = CliRunner().invoke(main, ["linux", "--help"])

        self.assertEqual(result.exit_code, 0)
        for command in (
            "health",
            "cpu",
            "memory",
            "disk",
            "network",
            "processes",
            "services",
            "logs",
            "kernel",
            "boot",
            "security",
            "all",
        ):
            self.assertIn(command, result.output)

    @patch("app.tools.linux.operations.collect_health")
    def test_health_renders_prioritized_findings(
        self,
        collect_health,
    ) -> None:
        collect_health.return_value = {
            "status": "warning",
            "host": {
                "hostname": "web-01",
                "platform": "Linux",
                "kernel": "6.8.0",
                "architecture": "x86_64",
                "cpu_count": 4,
                "load_average": [6.0, 4.0, 2.0],
            },
            "memory": {
                "available_percent": 42.0,
            },
            "filesystems": [],
            "services": {
                "status": "ok",
                "error": "",
            },
            "findings": [
                {
                    "severity": "warning",
                    "area": "cpu",
                    "summary": "Load exceeds logical CPU count.",
                    "next": "Inspect blocked tasks and I/O wait.",
                }
            ],
        }

        result = CliRunner().invoke(main, ["linux", "health"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Linux health: WARNING", result.output)
        self.assertIn("web-01", result.output)
        self.assertIn("blocked tasks", result.output)

    @patch("app.tools.linux.operations.collect_health")
    def test_health_strict_exits_nonzero(
        self,
        collect_health,
    ) -> None:
        collect_health.return_value = {
            "status": "critical",
            "host": {
                "hostname": "db-01",
                "platform": "Linux",
                "kernel": "6.8.0",
                "architecture": "x86_64",
                "cpu_count": 8,
                "load_average": None,
            },
            "memory": None,
            "filesystems": [],
            "services": {
                "status": "unavailable",
                "error": "",
            },
            "findings": [],
        }

        result = CliRunner().invoke(
            main,
            ["linux", "health", "--strict"],
        )

        self.assertEqual(result.exit_code, 1)

    @patch("app.tools.linux.operations.collect_domain")
    def test_domain_supports_json(
        self,
        collect_domain,
    ) -> None:
        collect_domain.return_value = {
            "domain": "network",
            "status": "collected",
            "host": "web-01",
            "platform": "Linux",
            "message": "",
            "results": [
                {
                    "key": "routes",
                    "label": "Routing tables",
                    "command": "ip route show table all",
                    "status": "ok",
                    "output": "default via 10.0.0.1",
                    "error": "",
                    "exit_code": 0,
                    "requires_root": False,
                }
            ],
        }

        result = CliRunner().invoke(
            main,
            ["linux", "network", "--json"],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["domain"], "network")
        self.assertEqual(payload["results"][0]["status"], "ok")
        collect_domain.assert_called_once_with(
            "network",
            scan_path="/",
            top=10,
        )


if __name__ == "__main__":
    unittest.main()
