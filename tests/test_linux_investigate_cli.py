from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from app.cli.main import main
from app.schemas.linux import (
    LinuxBootKernelFinding,
    LinuxBootKernelInvestigation,
    LinuxCpuFinding,
    LinuxCpuInvestigation,
    LinuxDiskFinding,
    LinuxDiskInvestigation,
    LinuxMemoryFinding,
    LinuxMemoryInvestigation,
    LinuxNetworkFinding,
    LinuxNetworkInvestigation,
    LinuxServiceFinding,
    LinuxServiceInvestigation,
)


def _investigation() -> LinuxDiskInvestigation:
    return LinuxDiskInvestigation(
        status="diagnosed",
        hostname="db-01",
        path="/var",
        platform="Linux",
        primary_diagnosis="inode_exhaustion",
        severity="critical",
        confidence=98,
        summary="Inode utilization is 97%.",
        filesystem_use_percent=60,
        inode_use_percent=97,
        mount_source="/dev/mapper/vg0-var",
        filesystem_type="xfs",
        mount_point="/var",
        lvm_volume_groups=["vg0 100.00g 2.00g wz--n-"],
        multipath_devices=["mpatha dm-2 NETAPP,LUN"],
        io_sample={
            "device": "dm-2",
            "await_ms": 120.0,
            "util_percent": 98.0,
        },
        findings=[
            LinuxDiskFinding(
                code="inode_exhaustion",
                severity="critical",
                confidence=98,
                summary="Inode utilization is 97%.",
                evidence=["/dev/sda1 100000 97000 3000 97% /var"],
                next="Find directories creating many small files.",
                next_explanation=(
                    "Inode exhaustion can cause writes to fail even when "
                    "byte capacity is available."
                ),
            )
        ],
    )


def _memory_investigation() -> LinuxMemoryInvestigation:
    return LinuxMemoryInvestigation(
        status="diagnosed",
        hostname="web-01",
        platform="Linux",
        pid=4242,
        primary_diagnosis="kernel_oom_kill",
        severity="critical",
        confidence=98,
        summary="Recent kernel evidence contains OOM kill activity.",
        mem_total_kb=16_000_000,
        mem_available_kb=1_000_000,
        mem_available_percent=6.25,
        swap_total_kb=2_000_000,
        swap_free_kb=1_000_000,
        swap_used_percent=50.0,
        swap_in_per_second=20,
        swap_out_per_second=0,
        findings=[
            LinuxMemoryFinding(
                code="kernel_oom_kill",
                severity="critical",
                confidence=98,
                summary="Recent kernel evidence contains OOM kill activity.",
                evidence=["kernel: Out of memory: Killed process 4242"],
                next="Identify the victim process and owning service.",
                next_explanation=(
                    "Kernel OOM evidence proves a process or cgroup could "
                    "not satisfy memory allocation."
                ),
            )
        ],
    )


def _cpu_investigation() -> LinuxCpuInvestigation:
    return LinuxCpuInvestigation(
        status="diagnosed",
        hostname="worker-01",
        platform="Linux",
        primary_diagnosis="d_state_blocked_tasks",
        severity="warning",
        confidence=96,
        summary="Load 8.00 exceeds 4 CPU(s) and 3 task(s) are in D state.",
        load_average=[8.0, 6.0, 4.0],
        cpu_count=4,
        running_tasks=6,
        total_tasks=200,
        process_states={"R": 3, "D": 3, "S": 50},
        vmstat_cpu={"us": 10, "sy": 5, "id": 80, "wa": 20, "st": 0},
        findings=[
            LinuxCpuFinding(
                code="d_state_blocked_tasks",
                severity="warning",
                confidence=96,
                summary="Load includes blocked D-state tasks.",
                evidence=["D=3"],
                next="Inspect blocked process wchan/stack.",
                next_explanation=(
                    "Uninterruptible D-state tasks count toward load average "
                    "but are usually waiting inside the kernel."
                ),
            )
        ],
    )


def _network_investigation() -> LinuxNetworkInvestigation:
    return LinuxNetworkInvestigation(
        status="diagnosed",
        hostname="worker-01",
        platform="Linux",
        iface="ens5",
        primary_diagnosis="no_carrier",
        severity="critical",
        confidence=95,
        summary="Interface carrier is absent.",
        interfaces=["ens5"],
        routes=["default via 10.0.0.1 dev ens5"],
        resolvers=["nameserver 10.0.0.2"],
        nic_signals={
            "operstate": "down",
            "carrier": "0",
            "speed": "unknown",
            "duplex": "unknown",
        },
        findings=[
            LinuxNetworkFinding(
                code="no_carrier",
                severity="critical",
                confidence=95,
                summary="Interface carrier is absent.",
                evidence=["carrier=0"],
                next="Check physical link, switch port, or cloud ENI.",
                next_explanation=(
                    "No carrier means the NIC does not see a physical or "
                    "virtual link."
                ),
            )
        ],
    )


def _service_investigation() -> LinuxServiceInvestigation:
    return LinuxServiceInvestigation(
        status="diagnosed",
        hostname="web-01",
        platform="Linux",
        service="nginx.service",
        primary_diagnosis="start_limit_hit",
        severity="critical",
        confidence=97,
        summary="nginx.service hit the systemd start limit.",
        unit_properties={
            "ActiveState": "failed",
            "Result": "start-limit-hit",
            "ExecMainStatus": "1",
            "NRestarts": "5",
            "Restart": "on-failure",
        },
        findings=[
            LinuxServiceFinding(
                code="start_limit_hit",
                severity="critical",
                confidence=97,
                summary="nginx.service hit the systemd start limit.",
                evidence=["Result=start-limit-hit"],
                next="Inspect the earliest failure.",
                next_explanation=(
                    "start-limit-hit means systemd stopped trying after "
                    "repeated failures."
                ),
            )
        ],
    )


def _boot_kernel_investigation() -> LinuxBootKernelInvestigation:
    return LinuxBootKernelInvestigation(
        status="diagnosed",
        hostname="worker-01",
        platform="Linux",
        primary_diagnosis="previous_boot_panic",
        severity="critical",
        confidence=96,
        summary="Previous boot contains kernel panic/oops evidence.",
        running_kernel="5.14.0-1.el9.x86_64",
        default_kernel="/boot/vmlinuz-5.14.0-2.el9.x86_64",
        default_index="0",
        boot_args="BOOT_IMAGE=/vmlinuz crashkernel=auto",
        kdump_status="Kdump is operational",
        findings=[
            LinuxBootKernelFinding(
                code="previous_boot_panic",
                severity="critical",
                confidence=96,
                summary="Previous boot contains kernel panic/oops evidence.",
                evidence=["kernel: Kernel panic - not syncing"],
                next="Preserve previous-boot journal and check kdump.",
                next_explanation=(
                    "Previous-boot panic evidence is stronger than current "
                    "clean logs after a reboot."
                ),
            )
        ],
    )


class LinuxInvestigateCLITests(unittest.TestCase):
    @patch(
        "app.orchestration.linux_disk_workflow.run_linux_disk_workflow"
    )
    def test_summary_renders_diagnosis_and_memory(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_investigation(), "memory.json")

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "disk",
                "--path",
                "/var",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("inode_exhaustion", result.output)
        self.assertIn("Inode use: 97%", result.output)
        self.assertIn("Mount: source=/dev/mapper/vg0-var", result.output)
        self.assertIn("I/O sample: device=dm-2", result.output)
        self.assertIn("LVM volume groups: 1", result.output)
        self.assertIn("Multipath records: 1", result.output)
        self.assertIn("Why:", result.output)
        self.assertIn("byte capacity is available", result.output)
        self.assertIn("memory.json", result.output)

    @patch(
        "app.orchestration.linux_disk_workflow.run_linux_disk_workflow"
    )
    def test_json_forwards_scope_and_no_persist(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_investigation(), None)

        result = CliRunner().invoke(
            main,
            [
                "investigate",
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
                "--format",
                "json",
                "--no-persist",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["primary_diagnosis"], "inode_exhaustion")
        self.assertIn(
            "byte capacity is available",
            payload["findings"][0]["next_explanation"],
        )
        run_workflow.assert_called_once_with(
            scan_path="/var",
            top=20,
            recent_minutes=30,
            large_size_mb=500,
            persist=False,
        )

    @patch(
        "app.orchestration.linux_memory_workflow.run_linux_memory_workflow"
    )
    def test_memory_summary_renders_diagnosis_and_memory(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_memory_investigation(), "memory.json")

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "memory",
                "--pid",
                "4242",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("kernel_oom_kill", result.output)
        self.assertIn("MemAvailable: 6.2%", result.output)
        self.assertIn("Swap activity: si=20 so=0", result.output)
        self.assertIn("Why:", result.output)
        self.assertIn("memory.json", result.output)

    @patch(
        "app.orchestration.linux_memory_workflow.run_linux_memory_workflow"
    )
    def test_memory_json_forwards_scope_and_no_persist(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_memory_investigation(), None)

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "memory",
                "--pid",
                "4242",
                "--top",
                "20",
                "--recent-minutes",
                "30",
                "--format",
                "json",
                "--no-persist",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["primary_diagnosis"], "kernel_oom_kill")
        self.assertIn(
            "memory allocation",
            payload["findings"][0]["next_explanation"],
        )
        run_workflow.assert_called_once_with(
            pid=4242,
            top=20,
            recent_minutes=30,
            persist=False,
        )

    @patch(
        "app.orchestration.linux_cpu_workflow.run_linux_cpu_workflow"
    )
    def test_cpu_summary_renders_load_state_and_why(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_cpu_investigation(), "cpu.json")

        result = CliRunner().invoke(
            main,
            ["investigate", "linux", "cpu"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("d_state_blocked_tasks", result.output)
        self.assertIn("Load: 8.00 CPUs=4", result.output)
        self.assertIn("Process states: R=3, D=3, S=50", result.output)
        self.assertIn("Why:", result.output)
        self.assertIn("cpu.json", result.output)

    @patch(
        "app.orchestration.linux_cpu_workflow.run_linux_cpu_workflow"
    )
    def test_cpu_json_forwards_scope_and_no_persist(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_cpu_investigation(), None)

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "cpu",
                "--top",
                "20",
                "--format",
                "json",
                "--no-persist",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["primary_diagnosis"], "d_state_blocked_tasks")
        self.assertIn(
            "load average",
            payload["findings"][0]["next_explanation"],
        )
        run_workflow.assert_called_once_with(
            top=20,
            persist=False,
        )

    @patch(
        "app.orchestration.linux_network_workflow.run_linux_network_workflow"
    )
    def test_network_summary_renders_nic_signals_and_why(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_network_investigation(), "net.json")

        result = CliRunner().invoke(
            main,
            ["investigate", "linux", "network", "--iface", "ens5"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("no_carrier", result.output)
        self.assertIn("iface=ens5", result.output)
        self.assertIn("carrier=0", result.output)
        self.assertIn("Why:", result.output)
        self.assertIn("net.json", result.output)

    @patch(
        "app.orchestration.linux_network_workflow.run_linux_network_workflow"
    )
    def test_network_json_forwards_scope_and_no_persist(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_network_investigation(), None)

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "network",
                "--iface",
                "ens5",
                "--format",
                "json",
                "--no-persist",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["primary_diagnosis"], "no_carrier")
        self.assertEqual(payload["iface"], "ens5")
        run_workflow.assert_called_once_with(
            iface="ens5",
            persist=False,
        )

    @patch(
        "app.orchestration.linux_service_workflow.run_linux_service_workflow"
    )
    def test_service_summary_renders_unit_state_and_why(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_service_investigation(), "svc.json")

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "service",
                "--service",
                "nginx.service",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("start_limit_hit", result.output)
        self.assertIn("service=nginx.service", result.output)
        self.assertIn("Result=start-limit-hit", result.output)
        self.assertIn("Why:", result.output)
        self.assertIn("svc.json", result.output)

    @patch(
        "app.orchestration.linux_service_workflow.run_linux_service_workflow"
    )
    def test_service_json_forwards_scope_and_no_persist(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_service_investigation(), None)

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "service",
                "--service",
                "nginx.service",
                "--format",
                "json",
                "--no-persist",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["primary_diagnosis"], "start_limit_hit")
        run_workflow.assert_called_once_with(
            service="nginx.service",
            persist=False,
        )

    @patch(
        "app.orchestration.linux_boot_kernel_workflow.run_linux_boot_kernel_workflow"
    )
    def test_boot_summary_renders_kernel_state_and_why(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_boot_kernel_investigation(), "boot.json")

        result = CliRunner().invoke(
            main,
            ["investigate", "linux", "boot"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("previous_boot_panic", result.output)
        self.assertIn("running=5.14.0-1", result.output)
        self.assertIn("default=/boot/vmlinuz-5.14.0-2", result.output)
        self.assertIn("Boot args:", result.output)
        self.assertIn("Why:", result.output)
        self.assertIn("boot.json", result.output)

    @patch(
        "app.orchestration.linux_boot_kernel_workflow.run_linux_boot_kernel_workflow"
    )
    def test_boot_json_forwards_scope_and_no_persist(
        self,
        run_workflow,
    ) -> None:
        run_workflow.return_value = (_boot_kernel_investigation(), None)

        result = CliRunner().invoke(
            main,
            [
                "investigate",
                "linux",
                "boot",
                "--recent-minutes",
                "30",
                "--format",
                "json",
                "--no-persist",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["primary_diagnosis"], "previous_boot_panic")
        run_workflow.assert_called_once_with(
            recent_minutes=30,
            persist=False,
        )


if __name__ == "__main__":
    unittest.main()
