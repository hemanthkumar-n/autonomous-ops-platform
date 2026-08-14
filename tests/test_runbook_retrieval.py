from __future__ import annotations

import unittest

from click.testing import CliRunner

from app.cli.main import main
from app.memory.runbooks.retrieval import (
    format_runbook_context_for_prompt,
    search_runbooks,
)
from app.schemas.memory import RunbookQuery


class RunbookRetrievalTests(unittest.TestCase):
    def test_search_prefers_matching_domain_and_incident_type(self) -> None:
        result = search_runbooks(
            RunbookQuery(
                domain="kubernetes",
                incident_type="MemoryExhaustion",
                text="pod CrashLoopBackOff OOMKilled cgroup memory limit",
                limit=2,
            )
        )

        self.assertGreaterEqual(result.total_matches, 1)
        self.assertEqual(
            result.matches[0].chunk.runbook_id,
            "k8s-oom-linux-memory",
        )
        self.assertIn("MemoryExhaustion", result.matches[0].matched_terms)

    def test_prompt_context_is_bounded_and_contains_boundary(self) -> None:
        result = search_runbooks(
            RunbookQuery(
                domain="linux.memory",
                incident_type="OOMKilled",
                text="cgroup memory.events oom_kill psi",
                limit=5,
            )
        )

        prompt_context = format_runbook_context_for_prompt(
            result,
            max_chunks=1,
            max_guidance_items=2,
            max_commands=1,
        )

        self.assertIn("guidance, not proof", prompt_context)
        self.assertIn("Linux Cgroup Memory Pressure", prompt_context)
        self.assertLessEqual(prompt_context.count("   - "), 3)

    def test_no_match_prompt_context_does_not_invent_guidance(self) -> None:
        result = search_runbooks(
            RunbookQuery(
                domain="aws.rds",
                incident_type="StorageLatency",
                text="aurora replica lag",
                limit=2,
            )
        )

        prompt_context = format_runbook_context_for_prompt(result)

        self.assertIn("No trusted runbook chunks matched", prompt_context)
        self.assertIn("Do not invent", prompt_context)

    def test_runbooks_cli_search_outputs_boundary(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "runbooks",
                "search",
                "--domain",
                "kubernetes",
                "--incident-type",
                "ImagePullBackOff",
                "--text",
                "registry dns timeout",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("AOP runbook retrieval", result.output)
        self.assertIn("guidance, not proof", result.output)
        self.assertIn("ImagePullBackOff", result.output)


if __name__ == "__main__":
    unittest.main()
