from __future__ import annotations

import unittest
from unittest.mock import patch

from app.memory.retrieval.hybrid_search import (
    hybrid_incident_search,
)
from app.schemas.memory import (
    MemoryQuery,
    MemorySearchResult,
)


class HybridSearchTests(unittest.TestCase):
    @patch(
        "app.memory.retrieval.hybrid_search.search_similar_incidents",
        side_effect=RuntimeError("embedding service unavailable"),
    )
    @patch(
        "app.memory.retrieval.hybrid_search.search_incident_memory"
    )
    def test_exact_search_survives_semantic_failure(
        self,
        exact_search,
        _semantic_search,
    ) -> None:
        query = MemoryQuery(
            incident_type="MemoryExhaustion",
        )
        exact_search.return_value = MemorySearchResult(
            query=query,
            matches=[],
            total_matches=0,
        )

        result = hybrid_incident_search(query)

        self.assertEqual(result["exact_match_count"], 0)
        self.assertEqual(result["semantic_match_count"], 0)


if __name__ == "__main__":
    unittest.main()
