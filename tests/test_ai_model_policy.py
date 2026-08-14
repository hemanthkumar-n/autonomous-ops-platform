from __future__ import annotations

import unittest

from app.llm.model_policy import select_model_for_task
from app.llm.token_budget import (
    estimate_tokens,
    evaluate_token_budget,
    trim_to_token_budget,
)


class TokenBudgetTests(unittest.TestCase):
    def test_estimates_empty_text_as_zero(self) -> None:
        self.assertEqual(estimate_tokens(""), 0)

    def test_evaluates_budget_boundaries(self) -> None:
        result = evaluate_token_budget(
            "disk full on /var",
            input_token_budget=100,
            output_token_reserve=20,
        )

        self.assertTrue(result.within_budget)
        self.assertGreater(result.remaining_input_tokens, 0)

    def test_trim_marks_truncated_evidence(self) -> None:
        trimmed = trim_to_token_budget(
            "x" * 1000,
            input_token_budget=10,
        )

        self.assertIn("AOP truncated evidence", trimmed)


class ModelPolicyTests(unittest.TestCase):
    def test_classification_uses_light_tier_for_small_evidence(self) -> None:
        selection = select_model_for_task(
            task="classification",
            evidence_text="pod CrashLoopBackOff after config change",
        )

        self.assertEqual(selection.tier, "light")
        self.assertEqual(selection.model, "gpt-5-nano")

    def test_normal_rca_uses_standard_tier_within_budget(self) -> None:
        selection = select_model_for_task(
            task="normal_rca",
            evidence_text="journalctl shows kubelet image pull timeout",
        )

        self.assertEqual(selection.tier, "standard")
        self.assertEqual(selection.model, "gpt-5-mini")

    def test_large_rca_escalates_to_deep_tier(self) -> None:
        selection = select_model_for_task(
            task="normal_rca",
            evidence_text="log-line\n" * 60000,
        )

        self.assertEqual(selection.tier, "deep")
        self.assertEqual(selection.model, "gpt-5.1")
        self.assertFalse(selection.budget.within_budget)

    def test_remediation_stays_on_local_tier(self) -> None:
        selection = select_model_for_task(
            task="remediation",
            evidence_text="restart kubelet requested",
        )

        self.assertEqual(selection.tier, "local")
        self.assertEqual(selection.provider_hint, "ollama")

    def test_local_only_forces_local_tier(self) -> None:
        selection = select_model_for_task(
            task="classification",
            evidence_text="short evidence",
            allow_external=False,
        )

        self.assertEqual(selection.tier, "local")


if __name__ == "__main__":
    unittest.main()
