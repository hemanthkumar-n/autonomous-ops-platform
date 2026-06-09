from __future__ import annotations

import unittest

from click.testing import CliRunner

from app.cli.main import main


class CLITests(unittest.TestCase):
    def test_exposes_showcase_commands(self) -> None:
        result = CliRunner().invoke(main, ["--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("investigate", result.output)
        self.assertIn("health", result.output)
        self.assertIn("kb", result.output)
        self.assertIn("memory", result.output)

    def test_exposes_kubernetes_investigation_options(self) -> None:
        result = CliRunner().invoke(
            main,
            ["investigate", "k8s", "--help"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("--namespace", result.output)
        self.assertIn("--format", result.output)
        self.assertIn("--no-persist", result.output)

    def test_exposes_kubernetes_shortcuts(self) -> None:
        result = CliRunner().invoke(
            main,
            ["kb", "--help"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("health", result.output)
        self.assertIn("pods", result.output)
        self.assertIn("po", result.output)
        self.assertIn("events", result.output)
        self.assertIn("logs", result.output)
        self.assertIn("describe", result.output)
        self.assertIn("investigate", result.output)


if __name__ == "__main__":
    unittest.main()
