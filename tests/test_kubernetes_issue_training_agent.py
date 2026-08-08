from __future__ import annotations

import unittest

from app.agents.sre.kubernetes_issue_training_agent import (
    get_kubernetes_issue_knowledge,
    list_kubernetes_issue_symptoms,
)


class KubernetesIssueTrainingAgentTests(unittest.TestCase):
    def test_crashloop_preserves_previous_log_guidance(self) -> None:
        knowledge = get_kubernetes_issue_knowledge("crashloop")

        self.assertEqual(knowledge.symptom, "CrashLoopBackOff")
        self.assertIn(
            "kubectl logs <pod> -n <namespace> --previous",
            knowledge.safe_kubectl_commands,
        )
        self.assertTrue(
            any("previous termination" in item for item in knowledge.do_not_assume)
        )

    def test_disk_pressure_preserves_linux_disk_depth(self) -> None:
        knowledge = get_kubernetes_issue_knowledge("DiskPressure")

        self.assertIn("inode exhaustion", knowledge.common_causes)
        self.assertTrue(
            any("deleted-open" in item for item in knowledge.linux_evidence)
        )
        self.assertIn(
            "aop investigate linux disk --path /var/lib/kubelet",
            knowledge.safe_aop_commands,
        )

    def test_node_conditions_include_pid_and_network(self) -> None:
        symptoms = list_kubernetes_issue_symptoms()

        self.assertIn("PIDPressure", symptoms)
        self.assertIn("NetworkUnavailable", symptoms)
        self.assertIn("NodeNotReady", symptoms)

    def test_unsupported_symptom_lists_supported_values(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Supported: .*CrashLoopBackOff",
        ):
            get_kubernetes_issue_knowledge("UnknownPodState")


if __name__ == "__main__":
    unittest.main()
