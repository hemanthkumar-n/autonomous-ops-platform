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
            "internals",
            "cgroups",
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

    @patch("app.tools.linux.internals.collect_internals")
    def test_internals_renders_pressure_and_findings(
        self,
        collect_internals,
    ) -> None:
        collect_internals.return_value.model_dump.return_value = {
            "status": "collected",
            "hostname": "worker-1",
            "load_average": [8.0, 6.0, 4.0],
            "running_tasks": 6,
            "total_tasks": 200,
            "last_pid": 900,
            "uptime_seconds": 1000.0,
            "cpu_count": 4,
            "process_states": {"D": 2, "R": 6, "S": 192},
            "pressure": {
                "io": {
                    "some": {
                        "avg10": 18.0,
                        "avg60": 10.0,
                        "avg300": 5.0,
                        "total": 100,
                    },
                    "full": {
                        "avg10": 4.0,
                        "avg60": 3.0,
                        "avg300": 2.0,
                        "total": 50,
                    },
                }
            },
            "vm_counters": {},
            "findings": [
                {
                    "severity": "warning",
                    "area": "scheduler",
                    "summary": "Two tasks are blocked.",
                    "next": "Inspect storage and NFS.",
                }
            ],
            "unavailable": [],
        }

        result = CliRunner().invoke(main, ["linux", "internals"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("worker-1", result.output)
        self.assertIn("some=18.00%", result.output)
        self.assertIn("Inspect storage and NFS", result.output)

    @patch("app.tools.linux.internals.collect_cgroups")
    def test_cgroups_supports_pid_and_json(
        self,
        collect_cgroups,
    ) -> None:
        collect_cgroups.return_value.model_dump.return_value = {
            "status": "collected",
            "hostname": "worker-1",
            "pid": 4242,
            "version": 2,
            "memberships": [],
            "cgroup_path": "/sys/fs/cgroup/kubepods/pod-a",
            "controllers": ["cpu", "memory", "pids"],
            "cpu": {"max": "200000 100000"},
            "memory": {"current": 1024, "max": 2048},
            "io": {},
            "pids": {"current": 5, "max": 100},
            "pressure": {},
            "findings": [],
            "unavailable": [],
        }

        result = CliRunner().invoke(
            main,
            ["linux", "cgroups", "--pid", "4242", "--json"],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["pid"], 4242)
        self.assertEqual(payload["memory"]["max"], 2048)
        collect_cgroups.assert_called_once_with(4242)


if __name__ == "__main__":
    unittest.main()
