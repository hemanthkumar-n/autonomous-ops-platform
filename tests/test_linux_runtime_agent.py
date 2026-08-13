from __future__ import annotations

import unittest

from app.agents.linux.runtime_agent import (
    build_runtime_plan,
    list_runtime_symptoms,
    list_supported_runtimes,
    normalize_runtime,
    normalize_runtime_symptom,
)


class LinuxRuntimeAgentTests(unittest.TestCase):
    def test_containerd_image_pull_plan_includes_network_storage_and_k8s(self) -> None:
        plan = build_runtime_plan(
            runtime="containerd",
            symptom="imagepullbackoff",
        )

        self.assertEqual(plan.runtime, "containerd")
        self.assertEqual(plan.symptom, "image-pull")
        self.assertEqual(
            plan.primary_diagnosis,
            "containerd_image_pull_requires_runtime_evidence",
        )
        self.assertIn("ImagePullBackOff", plan.kubernetes_correlation)
        self.assertIn("aop investigate linux network", plan.next_aop_commands)
        self.assertTrue(
            any(item.area == "image-pull" for item in plan.evidence)
        )

    def test_crio_disk_pressure_uses_containers_path(self) -> None:
        plan = build_runtime_plan(runtime="cri-o", symptom="disk")

        self.assertEqual(plan.runtime, "crio")
        self.assertIn("/var/lib/containers", plan.storage_paths)
        self.assertIn(
            "aop investigate linux disk --path /var/lib/containers",
            plan.next_aop_commands,
        )
        self.assertEqual(plan.severity, "critical")

    def test_docker_runtime_down_uses_docker_service_and_prune_warning(self) -> None:
        plan = build_runtime_plan(runtime="docker", symptom="runtime-down")

        self.assertIn("docker.service", plan.service_units)
        dangerous = [item.action for item in plan.dangerous_actions]
        self.assertIn("docker system prune", dangerous)
        self.assertTrue(
            any("restart" in item.action for item in plan.dangerous_actions)
        )

    def test_pid_pressure_includes_process_and_cgroup_evidence(self) -> None:
        plan = build_runtime_plan(runtime="containerd", symptom="pid")

        self.assertEqual(plan.symptom, "pid-pressure")
        self.assertIn("PIDPressure", plan.kubernetes_correlation)
        self.assertIn("aop linux processes --top 30", plan.next_aop_commands)

    def test_lists_and_aliases_are_stable(self) -> None:
        self.assertEqual(normalize_runtime("cri_o"), "crio")
        self.assertEqual(normalize_runtime_symptom("logs"), "log-pressure")
        self.assertIn("containerd", list_supported_runtimes())
        self.assertIn("cgroup", list_runtime_symptoms())

    def test_unknown_runtime_reports_supported_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "Supported: .*containerd"):
            normalize_runtime("madeup")


if __name__ == "__main__":
    unittest.main()
