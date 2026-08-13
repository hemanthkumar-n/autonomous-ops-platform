from __future__ import annotations

import unittest

from app.agents.linux.boot_kernel_agent import analyze_boot_kernel_evidence


def _result(key: str, output: str = "", status: str = "ok") -> dict:
    return {
        "key": key,
        "label": key,
        "command": key,
        "status": status,
        "output": output,
        "error": "",
        "exit_code": 0,
        "requires_root": False,
    }


def _evidence(*results: dict) -> dict:
    return {
        "domain": "boot_kernel",
        "status": "collected",
        "host": "worker-1",
        "platform": "Linux",
        "recent_minutes": 240,
        "results": list(results),
    }


class LinuxBootKernelAgentTests(unittest.TestCase):
    def test_previous_boot_panic_is_primary(self) -> None:
        investigation = analyze_boot_kernel_evidence(
            _evidence(
                _result("running_kernel", "5.14.0-1.el9.x86_64"),
                _result("previous_boot_errors", "kernel: Kernel panic - not syncing"),
                _result("current_kernel_errors", "-- No entries --"),
            )
        )

        self.assertEqual(investigation.primary_diagnosis, "previous_boot_panic")
        self.assertEqual(investigation.severity, "critical")
        self.assertIn("Kernel panic", investigation.findings[0].evidence[0])

    def test_default_kernel_mismatch_is_detected(self) -> None:
        investigation = analyze_boot_kernel_evidence(
            _evidence(
                _result("running_kernel", "5.14.0-1.el9.x86_64"),
                _result("grubby_default", "/boot/vmlinuz-5.14.0-2.el9.x86_64"),
                _result("grubby_index", "0"),
                _result("current_kernel_errors", "-- No entries --"),
                _result("previous_boot_errors", "-- No entries --"),
            )
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "default_kernel_mismatch",
        )
        self.assertIn("5.14.0-2", investigation.default_kernel)

    def test_risky_boot_args_are_reported(self) -> None:
        investigation = analyze_boot_kernel_evidence(
            _evidence(
                _result("boot_args", "BOOT_IMAGE=/vmlinuz crashkernel=auto cgroup_no_v1=all"),
                _result("current_kernel_errors", "-- No entries --"),
                _result("previous_boot_errors", "-- No entries --"),
            )
        )

        self.assertEqual(investigation.primary_diagnosis, "risky_boot_args")
        self.assertIn("cgroup_no_v1=all", investigation.findings[0].evidence)

    def test_insufficient_evidence_when_commands_missing(self) -> None:
        investigation = analyze_boot_kernel_evidence(
            _evidence(
                _result("boot_history", status="unavailable"),
                _result("current_kernel_errors", status="unavailable"),
            )
        )

        self.assertEqual(investigation.primary_diagnosis, "insufficient_evidence")
        self.assertTrue(investigation.evidence_gaps)


if __name__ == "__main__":
    unittest.main()
