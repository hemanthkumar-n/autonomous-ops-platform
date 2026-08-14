from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from click.testing import CliRunner

from app.cli.main import main
from app.memory.runbooks.external import (
    BUNDLED_K8S_AF_CATALOG,
    load_external_catalog,
    parse_k8s_af_html,
    search_external_stories,
)


K8S_AF_FIXTURE = """
<html><body><h1>Kubernetes Failure Stories</h1><ul>
<li><a href="https://example.com/dns">DNS outage - Example - 2020</a><ul>
<li>involved: AWS, CoreDNS, conntrack</li>
<li>impact: production outage</li>
</ul></li>
<li><a href="https://example.com/oom">Node OOM - Example - 2019</a><ul>
<li>involved: SystemOOM, cgroup, kubelet</li>
<li>impace: pods killed</li>
</ul></li>
<li><a href="https://example.com/dns">Duplicate DNS story</a><ul>
<li>involved: DNS</li><li>impact: duplicate</li>
</ul></li>
</ul></body></html>
"""


class ExternalKnowledgeImportTests(unittest.TestCase):
    def test_bundled_k8s_af_snapshot_has_unique_provenance_records(self) -> None:
        catalog = load_external_catalog(BUNDLED_K8S_AF_CATALOG)

        self.assertEqual(catalog.story_count, 59)
        self.assertEqual(len(catalog.stories), 59)
        self.assertEqual(
            len({story.story_id for story in catalog.stories}),
            59,
        )
        self.assertEqual(
            len({story.canonical_url for story in catalog.stories}),
            59,
        )
        self.assertTrue(
            all(
                story.review_state == "source_review_required"
                for story in catalog.stories
            )
        )

    def test_parser_imports_metadata_with_provenance_and_deduplication(self) -> None:
        catalog = parse_k8s_af_html(
            K8S_AF_FIXTURE,
            imported_at=datetime(2026, 8, 14, tzinfo=timezone.utc),
        )

        self.assertEqual(catalog.story_count, 2)
        self.assertEqual(catalog.stories[0].published_year, 2020)
        self.assertEqual(catalog.stories[0].technologies[1], "CoreDNS")
        self.assertEqual(catalog.stories[0].content_scope, "metadata_only")
        self.assertEqual(catalog.stories[0].license_status, "unverified")
        self.assertTrue(catalog.stories[0].source_checksum)
        self.assertEqual(catalog.stories[1].impact, "pods killed")

    def test_search_ranks_technology_and_text_matches(self) -> None:
        catalog = parse_k8s_af_html(K8S_AF_FIXTURE)

        matches = search_external_stories(
            catalog,
            text="production DNS conntrack",
            technology="CoreDNS",
            limit=5,
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].story.canonical_url, "https://example.com/dns")
        self.assertGreaterEqual(matches[0].score, 7)

    def test_cli_imports_saved_html_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture_path = Path(directory) / "k8s-af.html"
            output_path = Path(directory) / "k8s-af.json"
            fixture_path.write_text(K8S_AF_FIXTURE, encoding="utf-8")

            result = CliRunner().invoke(
                main,
                [
                    "runbooks",
                    "import",
                    "k8s-af",
                    "--input-file",
                    str(fixture_path),
                    "--output",
                    str(output_path),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("story_count: 2", result.output)
            self.assertIn("metadata_only", result.output)
            imported = load_external_catalog(output_path)
            self.assertEqual(imported.story_count, 2)

    def test_cli_search_marks_results_as_unreviewed_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture_path = Path(directory) / "k8s-af.html"
            output_path = Path(directory) / "k8s-af.json"
            fixture_path.write_text(K8S_AF_FIXTURE, encoding="utf-8")
            import_result = CliRunner().invoke(
                main,
                [
                    "runbooks",
                    "import",
                    "k8s-af",
                    "--input-file",
                    str(fixture_path),
                    "--output",
                    str(output_path),
                ],
            )
            self.assertEqual(import_result.exit_code, 0, import_result.output)

            result = CliRunner().invoke(
                main,
                [
                    "runbooks",
                    "stories",
                    "search",
                    "--catalog",
                    str(output_path),
                    "--technology",
                    "CoreDNS",
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("DNS outage", result.output)
            self.assertIn("source_review_required", result.output)
            self.assertIn("Metadata only", result.output)


if __name__ == "__main__":
    unittest.main()
