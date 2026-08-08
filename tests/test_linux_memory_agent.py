from __future__ import annotations

import unittest

from app.agents.linux.memory_agent import analyze_memory_evidence


def _result(
    key: str,
    output: str = "",
    status: str = "ok",
) -> dict:
    return {
        "key": key,
        "label": key.replace("_", " "),
        "command": key,
        "status": status,
        "output": output,
        "error": "",
        "exit_code": 0 if status == "ok" else 1,
        "requires_root": False,
    }


def _meminfo(
    available_kb: int = 8_000_000,
    total_kb: int = 16_000_000,
    swap_total_kb: int = 2_000_000,
    swap_free_kb: int = 2_000_000,
) -> str:
    return "\n".join(
        [
            f"MemTotal:       {total_kb} kB",
            f"MemAvailable:   {available_kb} kB",
            f"SwapTotal:      {swap_total_kb} kB",
            f"SwapFree:       {swap_free_kb} kB",
        ]
    )


def _vmstat(si: int = 0, so: int = 0) -> str:
    return "\n".join(
        [
            "procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----",
            " r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st",
            " 1  0      0 100000  10000 200000    0    0     0     0  100  200  1  1 98  0  0",
            f" 1  0      0  90000  10000 200000   {si}   {so}     0     0  100  200  1  1 98  0  0",
        ]
    )


def _evidence(
    meminfo: str | None = None,
    vmstat: str | None = None,
    oom: str = "-- No entries --",
    cgroup: dict | None = None,
) -> dict:
    payload = {
        "domain": "memory",
        "status": "collected",
        "host": "web-01",
        "platform": "Linux",
        "message": "",
        "pid": 4242,
        "results": [
            _result("free", "free output"),
            _result("vmstat", vmstat if vmstat is not None else _vmstat()),
            _result(
                "memory_processes",
                "PID RSS COMMAND\n4242 900000 java",
            ),
            _result("meminfo", meminfo if meminfo is not None else _meminfo()),
            _result("kernel_oom", oom),
        ],
    }
    if cgroup is not None:
        payload["cgroup"] = cgroup
    return payload


class LinuxMemoryAgentTests(unittest.TestCase):
    def test_classifies_kernel_oom_as_primary(self) -> None:
        investigation = analyze_memory_evidence(
            _evidence(
                oom=(
                    "kernel: Out of memory: Killed process 4242 "
                    "(java) total-vm:100000kB"
                )
            )
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "kernel_oom_kill",
        )
        self.assertEqual(investigation.severity, "critical")
        self.assertIn("victim", investigation.findings[0].next_explanation)

    def test_cgroup_oom_is_distinct_from_host_memory(self) -> None:
        investigation = analyze_memory_evidence(
            _evidence(
                cgroup={
                    "status": "collected",
                    "memory": {
                        "current": 52_428_800,
                        "max": 52_428_800,
                        "event_oom": 2,
                        "event_oom_kill": 1,
                    },
                }
            )
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "cgroup_memory_oom",
        )
        self.assertIn("configured container", investigation.findings[0].next_explanation)

    def test_active_swap_outranks_low_available_memory(self) -> None:
        investigation = analyze_memory_evidence(
            _evidence(
                meminfo=_meminfo(available_kb=1_000_000),
                vmstat=_vmstat(si=20, so=30),
            )
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "active_swap_pressure",
        )
        self.assertEqual(investigation.swap_in_per_second, 20)
        self.assertEqual(investigation.swap_out_per_second, 30)
        codes = [item.code for item in investigation.findings]
        self.assertIn("low_available_memory", codes)

    def test_low_available_memory_without_swap_is_warning(self) -> None:
        investigation = analyze_memory_evidence(
            _evidence(meminfo=_meminfo(available_kb=1_000_000))
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "low_available_memory",
        )
        self.assertAlmostEqual(investigation.mem_available_percent or 0, 6.25)

    def test_missing_meminfo_becomes_insufficient_evidence(self) -> None:
        evidence = _evidence()
        evidence["results"][3] = _result("meminfo", status="unavailable")

        investigation = analyze_memory_evidence(evidence)

        self.assertEqual(
            investigation.primary_diagnosis,
            "insufficient_evidence",
        )
        self.assertTrue(investigation.evidence_gaps)

    def test_unsupported_platform_has_no_false_memory_findings(self) -> None:
        investigation = analyze_memory_evidence(
            {
                "status": "unsupported",
                "host": "laptop",
                "platform": "macOS",
                "pid": None,
                "message": "Linux diagnostics require a Linux host",
                "results": [],
            }
        )

        self.assertEqual(investigation.status, "unsupported")
        self.assertEqual(
            investigation.primary_diagnosis,
            "unsupported_platform",
        )
        self.assertEqual(investigation.findings, [])


if __name__ == "__main__":
    unittest.main()
