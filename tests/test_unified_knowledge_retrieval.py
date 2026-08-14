from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from click.testing import CliRunner

from app.cli.main import main
from app.memory.retrieval.knowledge import (
    format_knowledge_context_for_prompt,
    retrieve_knowledge,
)
from app.schemas.memory import (
    IncidentFingerprint,
    IncidentMemory,
    IncidentPatternReport,
    IncidentPatternSummary,
    KnowledgeQuery,
    MemoryQuery,
    MemorySearchResult,
)


class UnifiedKnowledgeRetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        pattern_patcher = patch(
            "app.memory.retrieval.knowledge.find_incident_patterns",
            return_value=IncidentPatternReport(
                patterns=[],
                total_patterns=0,
                total_occurrences=0,
                min_count=2,
            ),
        )
        self.addCleanup(pattern_patcher.stop)
        pattern_patcher.start()

    @patch("app.memory.retrieval.knowledge.search_incident_memory")
    def test_combines_internal_and_reviewed_guidance_with_provenance(
        self, memory_search
    ) -> None:
        query = KnowledgeQuery(
            domain="kubernetes.networking",
            incident_type="DNSFailure",
            text="CoreDNS OOM retries ndots",
            limit=4,
        )
        memory_search.return_value = MemorySearchResult(
            query=MemoryQuery(incident_type="DNSFailure"),
            matches=[],
            total_matches=0,
        )

        result = retrieve_knowledge(query)

        self.assertEqual(result.matches[0].source_type, "reviewed_external")
        self.assertEqual(result.matches[0].trust_level, "source_reviewed")
        self.assertTrue(result.matches[0].source.startswith("https://"))

    @patch("app.memory.retrieval.knowledge.search_incident_memory")
    def test_default_pipeline_does_not_call_semantic_provider(
        self, memory_search
    ) -> None:
        query = KnowledgeQuery(text="disk full deleted open file", limit=2)
        memory_search.return_value = MemorySearchResult(
            query=MemoryQuery(limit=2), matches=[], total_matches=0
        )

        with patch(
            "app.memory.retrieval.knowledge.search_similar_incidents"
        ) as semantic_search:
            result = retrieve_knowledge(query)

        semantic_search.assert_not_called()
        self.assertFalse(result.semantic_attempted)

    @patch("app.memory.retrieval.knowledge.search_incident_memory")
    def test_exact_history_is_normalized_as_evidence_not_guidance(
        self, memory_search
    ) -> None:
        query = KnowledgeQuery(incident_type="MemoryExhaustion", limit=3)
        memory_search.return_value = MemorySearchResult(
            query=MemoryQuery(incident_type="MemoryExhaustion", limit=3),
            matches=[
                IncidentMemory(
                    incident_id="inc-123",
                    timestamp=datetime.now(timezone.utc),
                    environment="production",
                    fingerprint=IncidentFingerprint(
                        incident_type="MemoryExhaustion",
                        namespace="payments",
                        workload_name="checkout",
                        failure_reason="OOMKilled",
                    ),
                    severity="critical",
                    confidence=90,
                    pod_name="checkout-abc",
                    namespace="payments",
                    node="worker-1",
                    incident_type="MemoryExhaustion",
                    rca_summary="Container memory limit was exhausted.",
                    remediation_summary="Validate the current limit and workload.",
                    source_workflow_version="v1",
                )
            ],
            total_matches=1,
        )

        result = retrieve_knowledge(query)
        historical = next(
            match
            for match in result.matches
            if match.source_type == "incident_memory_exact"
        )

        self.assertEqual(historical.trust_level, "historical_evidence")
        self.assertIn("clue, not proof", historical.safety_boundary)

    @patch("app.memory.retrieval.knowledge.search_incident_memory")
    @patch(
        "app.memory.retrieval.knowledge.search_similar_incidents",
        side_effect=RuntimeError("offline"),
    )
    def test_semantic_failure_preserves_deterministic_results(
        self, _semantic_search, memory_search
    ) -> None:
        memory_search.return_value = MemorySearchResult(
            query=MemoryQuery(limit=3), matches=[], total_matches=0
        )

        result = retrieve_knowledge(
            KnowledgeQuery(text="OOMKilled cgroup", limit=3),
            include_semantic=True,
        )

        self.assertGreater(len(result.matches), 0)
        self.assertIn("incident_memory_semantic", result.unavailable_sources)

    @patch("app.memory.retrieval.knowledge.find_incident_patterns")
    @patch("app.memory.retrieval.knowledge.search_incident_memory")
    def test_recurring_patterns_enter_pipeline_as_correlation_clues(
        self, memory_search, pattern_search
    ) -> None:
        memory_search.return_value = MemorySearchResult(
            query=MemoryQuery(incident_type="OOMKilled"),
            matches=[],
            total_matches=0,
        )
        pattern_search.return_value = IncidentPatternReport(
            patterns=[
                IncidentPatternSummary(
                    fingerprint="kubernetes:payments:checkout:oomkilled",
                    domain="kubernetes",
                    incident_type="OOMKilled",
                    occurrence_count=4,
                    latest_timestamp=datetime.now(timezone.utc),
                    severities=["critical"],
                    resources=["payments/checkout"],
                    occurrences=[],
                )
            ],
            total_patterns=1,
            total_occurrences=4,
            min_count=2,
        )

        result = retrieve_knowledge(
            KnowledgeQuery(incident_type="OOMKilled", limit=5)
        )
        pattern = next(
            match for match in result.matches if match.source_type == "incident_pattern"
        )

        self.assertEqual(pattern.trust_level, "historical_recurrence")
        self.assertIn("not proof", pattern.safety_boundary)

    @patch("app.memory.retrieval.knowledge.search_incident_memory")
    def test_prompt_budget_keeps_provenance_and_evidence_reference(
        self, memory_search
    ) -> None:
        memory_search.return_value = MemorySearchResult(
            query=MemoryQuery(limit=5), matches=[], total_matches=0
        )
        result = retrieve_knowledge(
            KnowledgeQuery(
                text="OOMKilled memory cgroup",
                evidence_references=["kubernetes://payments/checkout"],
                limit=5,
            )
        )

        context = format_knowledge_context_for_prompt(
            result, max_items=1, max_guidance_items=1, max_commands=1
        )

        self.assertIn("provenance:", context)
        self.assertIn("kubernetes://payments/checkout", context)
        self.assertEqual(context.count("\n   guidance:"), 1)
        self.assertLessEqual(context.count("\n   safe_command:"), 1)

    @patch("app.memory.retrieval.knowledge.search_incident_memory")
    def test_cli_exposes_unified_search(self, memory_search) -> None:
        memory_search.return_value = MemorySearchResult(
            query=MemoryQuery(limit=2), matches=[], total_matches=0
        )

        result = CliRunner().invoke(
            main,
            ["knowledge", "search", "--text", "disk inode", "--limit", "2"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("AOP unified knowledge retrieval", result.output)
        self.assertIn("provenance:", result.output)
        self.assertIn("semantic_attempted: False", result.output)


if __name__ == "__main__":
    unittest.main()
