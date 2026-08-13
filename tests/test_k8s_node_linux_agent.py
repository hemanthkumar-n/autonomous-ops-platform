from __future__ import annotations

import unittest

from app.agents.sre.k8s_node_linux_agent import (
    list_k8s_node_conditions,
    normalize_node_condition,
    plan_k8s_node_linux,
)


class KubernetesNodeLinuxAgentTests(unittest.TestCase):
    def test_disk_pressure_maps_to_linux_host_storage(self) -> None:
        plan = plan_k8s_node_linux(
            node="worker-01",
            conditions=["DiskPressure"],
        )

        self.assertEqual(
            plan.primary_diagnosis,
            "node_disk_pressure_requires_linux_storage_check",
        )
        self.assertEqual(plan.severity, "critical")
        self.assertIn(
            "aop investigate linux host --path /var/lib/kubelet --service kubelet.service",
            plan.next_aop_commands,
        )
        domains = {item.domain for item in plan.linux_evidence}
        self.assertIn("linux-host-storage", domains)

    def test_multiple_conditions_keep_disk_pressure_as_primary(self) -> None:
        plan = plan_k8s_node_linux(
            node="worker-01",
            conditions=["MemoryPressure", "DiskPressure", "ReadyFalse"],
        )

        self.assertEqual(
            plan.primary_diagnosis,
            "node_disk_pressure_requires_linux_storage_check",
        )
        signal_names = [signal.condition for signal in plan.kubernetes_signals]
        self.assertIn("DiskPressure", signal_names)
        self.assertIn("MemoryPressure", signal_names)
        self.assertIn("Ready", signal_names)

    def test_pid_pressure_requests_process_and_cgroup_evidence(self) -> None:
        plan = plan_k8s_node_linux(
            node="worker-01",
            conditions=["pid"],
        )

        self.assertEqual(
            plan.primary_diagnosis,
            "node_pid_pressure_requires_linux_process_check",
        )
        self.assertIn("aop linux processes --top 30", plan.next_aop_commands)
        self.assertTrue(
            any(item.domain == "linux-process-cgroup" for item in plan.linux_evidence)
        )

    def test_alias_and_supported_list(self) -> None:
        self.assertEqual(normalize_node_condition("notready"), "NodeNotReady")
        self.assertIn("NetworkUnavailable", list_k8s_node_conditions())

    def test_unsupported_condition_lists_supported_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "Supported: .*DiskPressure"):
            normalize_node_condition("MadeUpPressure")


if __name__ == "__main__":
    unittest.main()
