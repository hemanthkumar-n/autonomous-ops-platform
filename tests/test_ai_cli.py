from __future__ import annotations

import json
import unittest

from click.testing import CliRunner

from app.cli.main import main


class AICLITests(unittest.TestCase):
    def test_ai_budget_summary(self) -> None:
        result = CliRunner().invoke(
            main,
            ["ai", "budget", "--task", "classification", "--text", "disk full"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("AOP AI token budget plan", result.output)
        self.assertIn("tier: light", result.output)

    def test_ai_budget_json(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "ai",
                "budget",
                "--task",
                "remediation",
                "--text",
                "restart service",
                "--format",
                "json",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.output)
        self.assertEqual(payload["tier"], "local")
        self.assertEqual(payload["provider_hint"], "ollama")


if __name__ == "__main__":
    unittest.main()
