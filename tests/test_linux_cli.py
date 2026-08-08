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
            "explain",
            "plan",
            "cpu",
            "memory",
            "nic",
            "disk",
            "space",
            "fs",
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

    def test_explain_renders_command_argument_reasoning(self) -> None:
        result = CliRunner().invoke(
            main,
            ["linux", "explain", "df -hT"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Command: df -hT", result.output)
        self.assertIn("filesystem type", result.output)
        self.assertIn("-h", result.output)
        self.assertIn("-T", result.output)
        self.assertIn("KubernetesDiskPressure", result.output)

    def test_explain_matches_runtime_placeholders(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "linux",
                "explain",
                "netstat",
                "-plane",
                "|",
                "grep",
                ":3045",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Command: netstat -plane | grep <port>", result.output)
        self.assertIn("Show PID/program name", result.output)
        self.assertIn("Prefer ss on modern Linux", result.output)

    def test_explain_supports_json(self) -> None:
        result = CliRunner().invoke(
            main,
            ["linux", "explain", "lsof", "-p", "4242", "--json"],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["status"], "found")
        self.assertEqual(
            payload["explanation"]["variant"],
            "lsof -p <pid>",
        )
        self.assertTrue(payload["explanation"]["requires_root"])

    def test_explain_unknown_command_exits_nonzero(self) -> None:
        result = CliRunner().invoke(
            main,
            ["linux", "explain", "unknownctl", "--magic"],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn(
            "No Linux command explanation is available",
            result.output,
        )

    @patch("app.tools.linux.operations.collect_nic")
    def test_nic_supports_iface_and_json(
        self,
        collect_nic,
    ) -> None:
        collect_nic.return_value = {
            "domain": "nic",
            "status": "collected",
            "host": "node-01",
            "platform": "Linux",
            "message": "",
            "iface": "ens5",
            "interfaces": ["ens5"],
            "results": [
                {
                    "key": "ens5.ethtool",
                    "label": "ens5 link settings",
                    "command": "ethtool ens5",
                    "status": "ok",
                    "output": "Speed: 10000Mb/s",
                    "error": "",
                    "exit_code": 0,
                    "requires_root": False,
                }
            ],
        }

        result = CliRunner().invoke(
            main,
            ["linux", "nic", "--iface", "ens5", "--json"],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["domain"], "nic")
        self.assertEqual(payload["iface"], "ens5")
        self.assertEqual(payload["results"][0]["key"], "ens5.ethtool")
        collect_nic.assert_called_once_with(iface="ens5")

    def test_nic_rejects_invalid_interface_name(self) -> None:
        result = CliRunner().invoke(
            main,
            ["linux", "nic", "--iface", "../../bad"],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("interface names may contain", result.output)

    def test_plan_disk_renders_ordered_troubleshooting_steps(self) -> None:
        result = CliRunner().invoke(
            main,
            ["linux", "plan", "disk", "--path", "/var"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Linux disk investigation plan for /var", result.output)
        self.assertIn("1. Confirm filesystem bytes and type", result.output)
        self.assertIn("Command: df -hT /var", result.output)
        self.assertIn("Command: df -i /var", result.output)
        self.assertIn("Command: lsof +L1 /var", result.output)
        self.assertIn("Kubernetes correlation", result.output)
        self.assertIn("AWS correlation", result.output)

    def test_plan_disk_supports_json(self) -> None:
        result = CliRunner().invoke(
            main,
            ["linux", "plan", "disk", "--path", "/var", "--json"],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["key"], "linux.disk")
        self.assertEqual(payload["path"], "/var")
        self.assertEqual(payload["steps"][0]["command"], "df -hT /var")
        self.assertTrue(payload["steps"][5]["requires_root"])

    def test_plan_disk_does_not_require_local_path(self) -> None:
        result = CliRunner().invoke(
            main,
            ["linux", "plan", "disk", "--path", "/company/app/logs"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn(
            "Linux disk investigation plan for /company/app/logs",
            result.output,
        )

    def test_plan_scenario_lists_complex_scenarios(self) -> None:
        result = CliRunner().invoke(
            main,
            ["linux", "plan", "scenario", "--list"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Linux complex troubleshooting scenarios", result.output)
        self.assertIn("high-load", result.output)
        self.assertIn("memory-pressure", result.output)
        self.assertIn("container-runtime-disk-pressure", result.output)

    def test_plan_scenario_renders_high_load(self) -> None:
        result = CliRunner().invoke(
            main,
            ["linux", "plan", "scenario", "high-load"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("High Load With Low CPU Usage", result.output)
        self.assertIn("First safe checks", result.output)
        self.assertIn("ps -eo state,pid,ppid,comm,wchan:32,cmd", result.output)
        self.assertIn("Kubernetes correlation", result.output)
        self.assertIn("Cgroup context", result.output)

    def test_plan_scenario_supports_aliases_and_json(self) -> None:
        result = CliRunner().invoke(
            main,
            ["linux", "plan", "scenario", "oom", "--json"],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["status"], "found")
        self.assertEqual(
            payload["scenario"]["key"],
            "memory-pressure",
        )
        self.assertIn(
            "journalctl -k -g 'Out of memory|Killed process|oom' --no-pager",
            payload["scenario"]["first_safe_checks"],
        )

    def test_plan_scenario_unknown_exits_nonzero(self) -> None:
        result = CliRunner().invoke(
            main,
            ["linux", "plan", "scenario", "made-up-scenario"],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Unknown Linux scenario", result.output)
        self.assertIn("high-load", result.output)

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

    @patch("app.tools.linux.operations.collect_disk")
    def test_disk_forwards_safe_scope_options(
        self,
        collect_disk,
    ) -> None:
        collect_disk.return_value = {
            "domain": "disk",
            "status": "collected",
            "host": "worker-1",
            "platform": "Linux",
            "message": "",
            "path": "/var",
            "results": [],
        }

        result = CliRunner().invoke(
            main,
            [
                "linux",
                "disk",
                "--path",
                "/var",
                "--top",
                "20",
                "--recent-minutes",
                "30",
                "--large-size-mb",
                "500",
                "--json",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["path"], "/var")
        collect_disk.assert_called_once_with(
            scan_path="/var",
            top=20,
            recent_minutes=30,
            large_size_mb=500,
        )

    @patch("app.tools.linux.operations.collect_disk")
    def test_disk_shortcuts_use_same_collector(
        self,
        collect_disk,
    ) -> None:
        collect_disk.return_value = {
            "domain": "disk",
            "status": "collected",
            "host": "worker-1",
            "platform": "Linux",
            "message": "",
            "path": "/",
            "results": [],
        }

        for alias in ("space", "fs"):
            with self.subTest(alias=alias):
                result = CliRunner().invoke(
                    main,
                    ["linux", alias, "--json"],
                )
                self.assertEqual(result.exit_code, 0)

        self.assertEqual(collect_disk.call_count, 2)

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

    @patch("app.tools.linux.internals.sample_internals")
    def test_internals_interval_uses_timed_sampling(
        self,
        sample_internals,
    ) -> None:
        sample_internals.return_value.model_dump.return_value = {
            "status": "collected",
            "hostname": "worker-1",
            "interval_seconds": 5.0,
            "before": {
                "unavailable": [],
            },
            "after": {},
            "vm_deltas": {
                "pgmajfault": {
                    "before": 10,
                    "after": 20,
                    "delta": 10,
                    "per_second": 2.0,
                }
            },
            "pressure_deltas": {
                "io": {
                    "some_stall_percent": 12.5,
                    "full_stall_percent": 2.0,
                }
            },
            "findings": [],
        }

        result = CliRunner().invoke(
            main,
            ["linux", "internals", "--interval", "5"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("delta=10", result.output)
        self.assertIn("some=12.500%", result.output)
        sample_internals.assert_called_once_with(5.0)

    @patch("app.tools.linux.internals.sample_cgroups")
    def test_cgroups_interval_uses_timed_sampling(
        self,
        sample_cgroups,
    ) -> None:
        sample_cgroups.return_value.model_dump.return_value = {
            "status": "collected",
            "hostname": "worker-1",
            "pid": 4242,
            "interval_seconds": 3.0,
            "before": {
                "version": 2,
                "memory": {"current": 800},
                "unavailable": [],
            },
            "after": {
                "version": 2,
                "memory": {"current": 950},
            },
            "cpu_deltas": {
                "nr_throttled": {
                    "before": 1,
                    "after": 3,
                    "delta": 2,
                    "per_second": 0.667,
                }
            },
            "memory_event_deltas": {},
            "pids_event_deltas": {},
            "pressure_deltas": {},
            "findings": [],
        }

        result = CliRunner().invoke(
            main,
            [
                "linux",
                "cgroups",
                "--pid",
                "4242",
                "--interval",
                "3",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("delta=2", result.output)
        self.assertIn("800 -> 950", result.output)
        sample_cgroups.assert_called_once_with(
            pid=4242,
            interval=3.0,
        )


if __name__ == "__main__":
    unittest.main()
