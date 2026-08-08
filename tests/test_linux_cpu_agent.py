from __future__ import annotations

import unittest

from app.agents.linux.cpu_agent import analyze_cpu_evidence


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


def _vmstat(
    us: int = 10,
    sy: int = 5,
    idle: int = 80,
    wa: int = 0,
    st: int = 0,
) -> str:
    return "\n".join(
        [
            "procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----",
            " r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st",
            " 1  0      0 100000  10000 200000    0    0     0     0  100  200  1  1 98  0  0",
            f" 4  2      0 100000  10000 200000    0    0     0     0  100  200 {us} {sy} {idle} {wa} {st}",
        ]
    )


def _pressure(cpu: float = 0, io: float = 0) -> dict:
    def resource(value: float) -> dict:
        return {
            "some": {
                "avg10": value,
                "avg60": value,
                "avg300": value,
                "total": 1000,
            },
            "full": {
                "avg10": 0.0,
                "avg60": 0.0,
                "avg300": 0.0,
                "total": 0,
            },
        }

    return {
        "cpu": resource(cpu),
        "io": resource(io),
        "memory": resource(0),
    }


def _evidence(
    load: list[float] | None = None,
    cpu_count: int = 4,
    process_states: dict[str, int] | None = None,
    vmstat: str | None = None,
    pressure: dict | None = None,
) -> dict:
    return {
        "domain": "cpu",
        "status": "collected",
        "host": "worker-01",
        "platform": "Linux",
        "message": "",
        "results": [
            _result("uptime", "load average: 8.00, 6.00, 4.00"),
            _result("lscpu", "CPU(s): 4"),
            _result(
                "cpu_processes",
                "PID %CPU COMMAND\n4242 90 java",
            ),
            _result("vmstat", vmstat if vmstat is not None else _vmstat()),
        ],
        "internals": {
            "status": "collected",
            "hostname": "worker-01",
            "load_average": load if load is not None else [8.0, 6.0, 4.0],
            "running_tasks": 6,
            "total_tasks": 200,
            "last_pid": 5000,
            "uptime_seconds": 3600,
            "cpu_count": cpu_count,
            "process_states": process_states or {"R": 3, "S": 50},
            "pressure": pressure or _pressure(),
            "vm_counters": {},
            "findings": [],
            "unavailable": [],
        },
    }


class LinuxCpuAgentTests(unittest.TestCase):
    def test_d_state_outranks_cpu_busy(self) -> None:
        investigation = analyze_cpu_evidence(
            _evidence(
                process_states={"R": 2, "D": 3, "S": 50},
                vmstat=_vmstat(us=80, sy=10, idle=5),
            )
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "d_state_blocked_tasks",
        )
        self.assertIn("blocked work", investigation.findings[0].next_explanation)

    def test_io_pressure_behind_load_is_distinct_from_cpu(self) -> None:
        investigation = analyze_cpu_evidence(
            _evidence(
                vmstat=_vmstat(us=10, sy=5, idle=60, wa=25),
                pressure=_pressure(io=12),
            )
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "io_pressure_behind_load",
        )
        self.assertIn("cloud-volume", investigation.findings[0].next_explanation)

    def test_cpu_saturation_from_busy_sample(self) -> None:
        investigation = analyze_cpu_evidence(
            _evidence(
                load=[3.0, 2.0, 1.0],
                vmstat=_vmstat(us=80, sy=10, idle=5),
            )
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "cpu_saturation",
        )
        self.assertEqual(investigation.vmstat_cpu["us"], 80)

    def test_steal_time_is_virtualization_pressure(self) -> None:
        investigation = analyze_cpu_evidence(
            _evidence(
                load=[2.0, 2.0, 1.0],
                vmstat=_vmstat(us=20, sy=10, idle=50, st=15),
            )
        )

        self.assertEqual(
            investigation.primary_diagnosis,
            "steal_time_pressure",
        )
        self.assertIn("hypervisor", investigation.findings[0].next_explanation)

    def test_missing_internals_becomes_insufficient_evidence(self) -> None:
        evidence = _evidence()
        evidence["internals"] = {
            "status": "unsupported",
            "unavailable": ["Linux internals require a Linux host"],
        }

        investigation = analyze_cpu_evidence(evidence)

        self.assertEqual(
            investigation.primary_diagnosis,
            "insufficient_evidence",
        )
        self.assertTrue(investigation.evidence_gaps)


if __name__ == "__main__":
    unittest.main()
