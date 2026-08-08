from __future__ import annotations

import unittest

from app.agents.sre.k8s_linux_correlation_agent import (
    correlate_k8s_linux,
    list_k8s_linux_incidents,
)


class KubernetesLinuxCorrelationAgentTests(unittest.TestCase):
    def test_oom_killed_maps_to_memory_and_cgroup_evidence(self) -> None:
        plan = correlate_k8s_linux("OOMKilled")

        self.assertEqual(plan.incident, "OOMKilled")
        domains = {item.domain for item in plan.linux_evidence}
        self.assertIn("memory", domains)
        self.assertIn("cgroups", domains)
        self.assertIn(
            "aop investigate linux memory --pid <container-pid>",
            plan.next_aop_commands,
        )
        self.assertTrue(
            any("host memory" in item for item in plan.do_not_assume)
        )

    def test_image_pull_alias_maps_to_network_nic_and_disk(self) -> None:
        plan = correlate_k8s_linux("imagepull")

        self.assertEqual(plan.incident, "ImagePullBackOff")
        domains = {item.domain for item in plan.linux_evidence}
        self.assertIn("network", domains)
        self.assertIn("nic", domains)
        self.assertIn("disk", domains)
        self.assertIn("aop investigate linux network", plan.next_aop_commands)

    def test_node_not_ready_requests_service_network_and_host_pressure(self) -> None:
        plan = correlate_k8s_linux("notready")

        self.assertEqual(plan.incident, "NodeNotReady")
        domains = {item.domain for item in plan.linux_evidence}
        self.assertEqual(
            domains,
            {"service", "network", "host-pressure"},
        )
        self.assertIn(
            "aop investigate linux service --service kubelet",
            plan.next_aop_commands,
        )

    def test_unsupported_incident_reports_supported_values(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Supported: .*OOMKilled",
        ):
            correlate_k8s_linux("MadeUpBackOff")

    def test_lists_supported_kubernetes_symptoms(self) -> None:
        incidents = list_k8s_linux_incidents()

        self.assertIn("CrashLoopBackOff", incidents)
        self.assertIn("DiskPressure", incidents)
        self.assertIn("OOMKilled", incidents)


if __name__ == "__main__":
    unittest.main()
