from __future__ import annotations

import subprocess
import unittest
from unittest.mock import Mock, patch

from app.tools.linux.operations import (
    CommandResult,
    CommandSpec,
    collect_disk,
    collect_memory,
    collect_nic,
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

    @patch(
        "app.tools.linux.operations.platform.system",
        return_value="Linux",
    )
    @patch("app.tools.linux.operations.run_command")
    def test_nic_collection_includes_sysfs_and_ethtool_evidence(
        self,
        run_command_mock,
        _platform_system,
    ) -> None:
        run_command_mock.side_effect = lambda spec: CommandResult(
            key=spec.key,
            label=spec.label,
            command=" ".join(spec.argv),
            status="ok",
            output="ok",
            requires_root=spec.requires_root,
        )

        payload = collect_nic(iface="ens5")

        self.assertEqual(payload["domain"], "nic")
        self.assertEqual(payload["interfaces"], ["ens5"])
        keys = [item["key"] for item in payload["results"]]
        self.assertEqual(
            keys,
            [
                "interfaces",
                "addresses",
                "link_stats",
                "ens5.operstate",
                "ens5.carrier",
                "ens5.speed",
                "ens5.duplex",
                "ens5.ethtool",
                "ens5.driver",
                "ens5.driver_stats",
            ],
        )

        specs = [
            call.args[0]
            for call in run_command_mock.call_args_list
        ]
        self.assertIn(
            ("ip", "-s", "link", "show", "dev", "ens5"),
            [spec.argv for spec in specs],
        )
        self.assertIn(("ethtool", "ens5"), [spec.argv for spec in specs])
        self.assertIn(("ethtool", "-i", "ens5"), [spec.argv for spec in specs])
        self.assertIn(("ethtool", "-S", "ens5"), [spec.argv for spec in specs])

    def test_nic_collection_rejects_unsafe_interface_name(self) -> None:
        with self.assertRaises(ValueError):
            collect_nic(iface="../../bad")

    @patch(
        "app.tools.linux.operations.platform.system",
        return_value="Linux",
    )
    @patch("app.tools.linux.operations.run_command")
    def test_disk_collection_is_ordered_and_bounded(
        self,
        run_command_mock,
        _platform_system,
    ) -> None:
        def result(spec):
            output = ""
            if spec.key == "directory_usage":
                output = (
                    "100\t/var/small\n"
                    "5000\t/var/large\n"
                    "1000\t/var/medium\n"
                )
            if spec.key == "large_recent_files":
                output = (
                    "200\t2026-06-10T10:00:00\t/var/a.log\n"
                    "900\t2026-06-10T10:01:00\t/var/b.log\n"
                )
            return CommandResult(
                key=spec.key,
                label=spec.label,
                command=" ".join(spec.argv),
                status="ok",
                output=output,
                requires_root=spec.requires_root,
            )

        run_command_mock.side_effect = result

        payload = collect_disk(
            scan_path="/var",
            top=2,
            recent_minutes=30,
            large_size_mb=500,
        )

        keys = [item["key"] for item in payload["results"]]
        self.assertEqual(
            keys,
            [
                "filesystem",
                "inodes",
                "mount",
                "directory_usage",
                "large_recent_files",
                "deleted_open_files",
                "kernel_storage_errors",
            ],
        )
        self.assertEqual(
            payload["results"][3]["output"].splitlines(),
            ["5000\t/var/large", "1000\t/var/medium"],
        )
        self.assertEqual(
            payload["results"][4]["output"].splitlines(),
            [
                "900\t2026-06-10T10:01:00\t/var/b.log",
                "200\t2026-06-10T10:00:00\t/var/a.log",
            ],
        )

        specs = [
            call.args[0]
            for call in run_command_mock.call_args_list
        ]
        find_spec = next(
            spec
            for spec in specs
            if spec.key == "large_recent_files"
        )
        self.assertIn("-xdev", find_spec.argv)
        self.assertIn("+500M", find_spec.argv)
        self.assertIn("-30", find_spec.argv)

    @patch(
        "app.tools.linux.operations.platform.system",
        return_value="Darwin",
    )
    def test_disk_collection_rejects_non_linux(
        self,
        _platform_system,
    ) -> None:
        payload = collect_disk(scan_path="/")

        self.assertEqual(payload["status"], "unsupported")
        self.assertEqual(payload["results"], [])

    @patch(
        "app.tools.linux.operations.platform.system",
        return_value="Linux",
    )
    @patch("app.tools.linux.operations.run_command")
    def test_memory_collection_includes_oom_and_optional_cgroup(
        self,
        run_command_mock,
        _platform_system,
    ) -> None:
        run_command_mock.side_effect = lambda spec: CommandResult(
            key=spec.key,
            label=spec.label,
            command=" ".join(spec.argv),
            status="ok",
            output="\n".join(["HEADER", "one", "two", "three"]),
            requires_root=spec.requires_root,
        )

        with patch(
            "app.tools.linux.internals.collect_cgroups",
        ) as collect_cgroups:
            collect_cgroups.return_value.model_dump.return_value = {
                "status": "collected",
                "memory": {"event_oom": 1},
            }

            payload = collect_memory(
                pid=4242,
                top=2,
                recent_minutes=30,
            )

        keys = [item["key"] for item in payload["results"]]
        self.assertEqual(
            keys,
            [
                "free",
                "vmstat",
                "memory_processes",
                "meminfo",
                "kernel_oom",
            ],
        )
        self.assertEqual(payload["pid"], 4242)
        self.assertEqual(
            payload["results"][2]["output"].splitlines(),
            ["HEADER", "one", "two"],
        )
        self.assertEqual(payload["cgroup"]["memory"]["event_oom"], 1)

        specs = [
            call.args[0]
            for call in run_command_mock.call_args_list
        ]
        journal_spec = next(
            spec
            for spec in specs
            if spec.key == "kernel_oom"
        )
        self.assertIn("--grep", journal_spec.argv)
        self.assertIn("30 minutes ago", journal_spec.argv)


if __name__ == "__main__":
    unittest.main()
