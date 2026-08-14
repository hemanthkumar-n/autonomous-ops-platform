from __future__ import annotations

import unittest

from click.testing import CliRunner

from app.cli.main import main
from app.memory.runbooks.external import load_external_catalog
from app.memory.runbooks.retrieval import search_runbooks
from app.memory.runbooks.reviewed import (
    load_review_catalog,
    review_queue,
    reviewed_guidance_chunks,
    search_reviews,
)
from app.schemas.memory import RunbookQuery


class ExternalKnowledgeReviewTests(unittest.TestCase):
    def test_reviews_reference_imported_story_ids(self) -> None:
        external = load_external_catalog()
        catalog = load_review_catalog()
        story_ids = {story.story_id for story in external.stories}

        self.assertEqual(catalog.review_count, 2)
        self.assertTrue(
            all(review.story_id in story_ids for review in catalog.reviews)
        )
        self.assertTrue(
            all(review.review_state == "guidance_reviewed" for review in catalog.reviews)
        )

    def test_review_queue_excludes_reviewed_stories(self) -> None:
        pending = review_queue()

        self.assertEqual(len(pending), 57)
        pending_ids = {item["story_id"] for item in pending}
        self.assertNotIn("k8s-af-9d90f871f00c4013", pending_ids)
        self.assertNotIn("k8s-af-ed6ee8cc4ae3478d", pending_ids)

    def test_reviewed_chunks_exclude_risky_mutation_actions(self) -> None:
        chunks = reviewed_guidance_chunks()

        self.assertEqual(len(chunks), 2)
        rendered = " ".join(
            [
                *[guidance for chunk in chunks for guidance in chunk.guidance],
                *[command for chunk in chunks for command in chunk.commands],
            ]
        )
        self.assertNotIn("sysctl -w", rendered)
        self.assertNotIn("2000Mi", rendered)
        self.assertIn("conntrack -S", rendered)

    def test_reviewed_dns_guidance_is_available_to_bounded_rag(self) -> None:
        result = search_runbooks(
            RunbookQuery(
                domain="kubernetes.networking",
                incident_type="DNSFailure",
                text="CoreDNS OOM ndots retries monitoring",
                limit=3,
            )
        )

        self.assertGreaterEqual(result.total_matches, 1)
        self.assertEqual(
            result.matches[0].chunk.runbook_id,
            "review-k8s-dns-coredns-oom-zalando-2019",
        )
        self.assertIn("github.com/zalando-incubator", result.matches[0].chunk.source or "")

    def test_review_search_finds_conntrack_source(self) -> None:
        matches = search_reviews(
            "conntrack resets node memory",
            review_state="guidance_reviewed",
        )

        self.assertEqual(
            matches[0].review_id,
            "review-k8s-linux-conntrack-loveholidays-2020",
        )

    def test_cli_review_show_separates_safe_and_risky_actions(self) -> None:
        result = CliRunner().invoke(
            main,
            [
                "runbooks",
                "review",
                "show",
                "review-k8s-linux-conntrack-loveholidays-2020",
            ],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Reported root cause", result.output)
        self.assertIn("Safe read-only commands", result.output)
        self.assertIn("Risky or historical actions", result.output)
        self.assertIn("Do not copy", result.output)

    def test_cli_review_queue_reports_remaining_count(self) -> None:
        result = CliRunner().invoke(
            main,
            ["runbooks", "review", "queue", "--limit", "1"],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("pending_count: 57", result.output)
        self.assertIn("reviewed_count: 2", result.output)


if __name__ == "__main__":
    unittest.main()
