from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.tools.linux.internals import (
    collect_cgroups,
    collect_internals,
    parse_cgroup_memberships,
    parse_loadavg,
    parse_pressure,
    sample_cgroups,
    sample_internals,
)
from app.schemas.linux import (
    CgroupEvidence,
    LinuxInternalsEvidence,
)


PRESSURE = (
    "some avg10=12.50 avg60=8.00 avg300=3.00 total=1000\n"
    "full avg10=2.00 avg60=1.00 avg300=0.50 total=100\n"
)


class LinuxInternalsTests(unittest.TestCase):
    def test_parses_load_average_and_task_counts(self) -> None:
        load, running, total, last_pid = parse_loadavg(
            "2.50 1.50 1.00 3/200 4567\n"
        )

        self.assertEqual(load, [2.5, 1.5, 1.0])
        self.assertEqual((running, total), (3, 200))
        self.assertEqual(last_pid, 4567)

    def test_parses_pressure_stall_information(self) -> None:
        pressure = parse_pressure(PRESSURE)

        self.assertEqual(pressure.some.avg10, 12.5)
        self.assertEqual(pressure.full.total, 100)

    def test_parses_cgroup_v2_membership(self) -> None:
        memberships = parse_cgroup_memberships(
            "0::/system.slice/app.service\n"
        )

        self.assertEqual(memberships[0].hierarchy_id, 0)
        self.assertEqual(memberships[0].controllers, [])
        self.assertEqual(
            memberships[0].path,
            "/system.slice/app.service",
        )

    @patch(
        "app.tools.linux.internals.platform.system",
        return_value="Linux",
    )
    @patch(
        "app.tools.linux.internals.os.cpu_count",
        return_value=4,
    )
    def test_collects_internals_and_correlates_load(
        self,
        _cpu_count,
        _platform,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            proc = Path(directory)
            (proc / "pressure").mkdir()
            (proc / "loadavg").write_text(
                "8.00 6.00 4.00 5/100 500\n",
                encoding="utf-8",
            )
            (proc / "uptime").write_text(
                "3600.00 1000.00\n",
                encoding="utf-8",
            )
            (proc / "vmstat").write_text(
                "pgfault 100\n"
                "pgmajfault 4\n"
                "oom_kill 1\n",
                encoding="utf-8",
            )
            for resource in ("cpu", "memory", "io"):
                (proc / "pressure" / resource).write_text(
                    PRESSURE,
                    encoding="utf-8",
                )

            for pid, state in ((100, "R"), (101, "D"), (102, "S")):
                process = proc / str(pid)
                process.mkdir()
                (process / "stat").write_text(
                    f"{pid} (worker thread) {state} 1 1 1\n",
                    encoding="utf-8",
                )

            evidence = collect_internals(proc_root=proc)

        self.assertEqual(evidence.status, "collected")
        self.assertEqual(evidence.process_states["D"], 1)
        self.assertEqual(evidence.vm_counters["oom_kill"], 1)
        areas = {finding.area for finding in evidence.findings}
        self.assertIn("scheduler", areas)
        self.assertIn("memory", areas)
        self.assertIn("io_pressure", areas)

    @patch(
        "app.tools.linux.internals.platform.system",
        return_value="Linux",
    )
    def test_collects_cgroup_v2_limits_events_and_pressure(
        self,
        _platform,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc = root / "proc"
            cgroups = root / "cgroup"
            process = proc / "4242"
            group = cgroups / "kubepods" / "pod-a"
            process.mkdir(parents=True)
            group.mkdir(parents=True)

            (process / "cgroup").write_text(
                "0::/kubepods/pod-a\n",
                encoding="utf-8",
            )
            (cgroups / "cgroup.controllers").write_text(
                "cpu memory io pids\n",
                encoding="utf-8",
            )
            (group / "cgroup.controllers").write_text(
                "cpu memory io pids\n",
                encoding="utf-8",
            )
            (group / "cpu.max").write_text(
                "200000 100000\n",
                encoding="utf-8",
            )
            (group / "cpu.weight").write_text("100\n", encoding="utf-8")
            (group / "cpu.stat").write_text(
                "usage_usec 10000\n"
                "nr_periods 20\n"
                "nr_throttled 3\n"
                "throttled_usec 500\n",
                encoding="utf-8",
            )
            for filename, value in {
                "memory.current": "900\n",
                "memory.min": "0\n",
                "memory.low": "0\n",
                "memory.high": "800\n",
                "memory.max": "1000\n",
                "memory.swap.current": "0\n",
                "memory.swap.max": "max\n",
                "io.max": "8:0 rbps=1048576\n",
                "io.weight": "default 100\n",
                "io.stat": "8:0 rbytes=1024 wbytes=2048\n",
                "pids.current": "9\n",
                "pids.max": "10\n",
            }.items():
                (group / filename).write_text(value, encoding="utf-8")
            (group / "memory.events").write_text(
                "low 0\nhigh 2\nmax 1\noom 1\noom_kill 1\n",
                encoding="utf-8",
            )
            (group / "pids.events").write_text(
                "max 1\n",
                encoding="utf-8",
            )
            for resource in ("cpu", "memory", "io"):
                (group / f"{resource}.pressure").write_text(
                    PRESSURE,
                    encoding="utf-8",
                )

            evidence = collect_cgroups(
                pid=4242,
                proc_root=proc,
                cgroup_root=cgroups,
            )

        self.assertEqual(evidence.version, 2)
        self.assertEqual(evidence.memory["current"], 900)
        self.assertEqual(evidence.memory["event_oom_kill"], 1)
        self.assertEqual(evidence.pids["current"], 9)
        areas = {finding.area for finding in evidence.findings}
        self.assertIn("cgroup_cpu", areas)
        self.assertIn("cgroup_memory", areas)
        self.assertIn("cgroup_pids", areas)

    @patch(
        "app.tools.linux.internals.platform.system",
        return_value="Linux",
    )
    def test_reports_cgroup_v1_without_v2_assumptions(
        self,
        _platform,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc = root / "proc"
            cgroups = root / "cgroup"
            process = proc / "99"
            process.mkdir(parents=True)
            cgroups.mkdir()
            (process / "cgroup").write_text(
                "2:cpu,cpuacct:/legacy.slice\n"
                "3:memory:/legacy.slice\n",
                encoding="utf-8",
            )

            evidence = collect_cgroups(
                pid=99,
                proc_root=proc,
                cgroup_root=cgroups,
            )

        self.assertEqual(evidence.version, 1)
        self.assertEqual(len(evidence.memberships), 2)
        self.assertEqual(evidence.cpu, {})
        self.assertIn(
            "v1",
            evidence.findings[0].summary.lower(),
        )

    @patch("app.tools.linux.internals.collect_internals")
    def test_samples_vm_and_pressure_deltas(
        self,
        collect_internals_mock,
    ) -> None:
        before = LinuxInternalsEvidence(
            status="collected",
            hostname="worker-1",
            cpu_count=4,
            vm_counters={
                "pgmajfault": 100,
                "pswpin": 10,
                "pswpout": 20,
                "oom_kill": 1,
            },
            pressure={
                "memory": parse_pressure(
                    "some avg10=0 avg60=0 avg300=0 total=1000000\n"
                    "full avg10=0 avg60=0 avg300=0 total=200000\n"
                )
            },
        )
        after = before.model_copy(
            update={
                "vm_counters": {
                    "pgmajfault": 120,
                    "pswpin": 15,
                    "pswpout": 20,
                    "oom_kill": 2,
                },
                "pressure": {
                    "memory": parse_pressure(
                        "some avg10=0 avg60=0 avg300=0 total=2000000\n"
                        "full avg10=0 avg60=0 avg300=0 total=300000\n"
                    )
                },
            }
        )
        collect_internals_mock.side_effect = [before, after]

        sample = sample_internals(
            interval=5,
            sleep=lambda _seconds: None,
        )

        self.assertEqual(sample.vm_deltas["pgmajfault"].delta, 20)
        self.assertEqual(sample.vm_deltas["pgmajfault"].per_second, 4.0)
        self.assertEqual(
            sample.pressure_deltas["memory"].some_stall_percent,
            20.0,
        )
        areas = {finding.area for finding in sample.findings}
        self.assertIn("memory", areas)
        self.assertIn("memory_pressure", areas)

    @patch("app.tools.linux.internals.collect_cgroups")
    def test_samples_active_cgroup_events(
        self,
        collect_cgroups_mock,
    ) -> None:
        before = CgroupEvidence(
            status="collected",
            hostname="worker-1",
            pid=4242,
            version=2,
            cpu={
                "nr_throttled": 3,
                "throttled_usec": 500,
                "usage_usec": 1000,
            },
            memory={
                "current": 800,
                "max": 1000,
                "event_high": 1,
                "event_oom_kill": 0,
            },
            pids={
                "current": 8,
                "max": 10,
                "event_max": 0,
            },
            pressure={
                "cpu": parse_pressure(
                    "some avg10=0 avg60=0 avg300=0 total=100000\n"
                )
            },
        )
        after = before.model_copy(
            update={
                "cpu": {
                    "nr_throttled": 5,
                    "throttled_usec": 2500,
                    "usage_usec": 6000,
                },
                "memory": {
                    "current": 950,
                    "max": 1000,
                    "event_high": 3,
                    "event_oom_kill": 1,
                },
                "pids": {
                    "current": 9,
                    "max": 10,
                    "event_max": 1,
                },
                "pressure": {
                    "cpu": parse_pressure(
                        "some avg10=0 avg60=0 avg300=0 total=1100000\n"
                    )
                },
            }
        )
        collect_cgroups_mock.side_effect = [before, after]

        sample = sample_cgroups(
            pid=4242,
            interval=5,
            sleep=lambda _seconds: None,
        )

        self.assertEqual(sample.cpu_deltas["nr_throttled"].delta, 2)
        self.assertEqual(
            sample.memory_event_deltas["event_oom_kill"].delta,
            1,
        )
        self.assertEqual(
            sample.pids_event_deltas["event_max"].delta,
            1,
        )
        self.assertEqual(
            sample.pressure_deltas["cpu"].some_stall_percent,
            20.0,
        )
        areas = {finding.area for finding in sample.findings}
        self.assertIn("cgroup_cpu", areas)
        self.assertIn("cgroup_memory", areas)
        self.assertIn("cgroup_pids", areas)

    @patch("app.tools.linux.internals.collect_internals")
    def test_ignores_counter_reset_in_delta_output(
        self,
        collect_internals_mock,
    ) -> None:
        before = LinuxInternalsEvidence(
            status="collected",
            hostname="worker-1",
            cpu_count=4,
            vm_counters={"pgfault": 100},
        )
        after = before.model_copy(
            update={"vm_counters": {"pgfault": 10}}
        )
        collect_internals_mock.side_effect = [before, after]

        sample = sample_internals(
            interval=5,
            sleep=lambda _seconds: None,
        )

        self.assertNotIn("pgfault", sample.vm_deltas)

    @patch("app.tools.linux.internals.collect_cgroups")
    def test_does_not_compare_different_cgroups(
        self,
        collect_cgroups_mock,
    ) -> None:
        before = CgroupEvidence(
            status="collected",
            hostname="worker-1",
            pid=4242,
            version=2,
            cgroup_path="/sys/fs/cgroup/old",
            cpu={"usage_usec": 100},
        )
        after = before.model_copy(
            update={
                "cgroup_path": "/sys/fs/cgroup/new",
                "cpu": {"usage_usec": 1000},
            }
        )
        collect_cgroups_mock.side_effect = [before, after]

        sample = sample_cgroups(
            pid=4242,
            interval=1,
            sleep=lambda _seconds: None,
        )

        self.assertEqual(sample.status, "changed")
        self.assertEqual(sample.cpu_deltas, {})
        self.assertIn(
            "membership changed",
            sample.findings[0].summary,
        )


if __name__ == "__main__":
    unittest.main()
