from __future__ import annotations

from datetime import datetime, timezone

import unittest

from app.schemas.evidence import (
    AlertSignal,
    DashboardPanel,
    DashboardSnapshot,
    EvidenceItem,
    EvidenceTimeline,
    MetricPoint,
    MetricSeries,
)


class EvidenceContractTests(unittest.TestCase):
    def test_metric_series_is_provider_neutral(self) -> None:
        point = MetricPoint(
            timestamp=datetime(2026, 8, 8, tzinfo=timezone.utc),
            value=95.0,
            unit="percent",
            labels={"node": "worker-1"},
            source="prometheus",
        )
        series = MetricSeries(
            name="node_filesystem_used_percent",
            query="provider-specific query stays optional",
            unit="percent",
            domain="linux",
            points=[point],
        )

        self.assertEqual(series.points[0].value, 95.0)
        self.assertEqual(series.domain, "linux")
        self.assertEqual(series.points[0].source, "prometheus")

    def test_evidence_timeline_orders_items_by_timestamp(self) -> None:
        later = EvidenceItem(
            id="later",
            timestamp=datetime(2026, 8, 8, 10, 5, tzinfo=timezone.utc),
            domain="linux",
            source="aop linux disk",
            title="Disk full",
            summary="Filesystem is 96% used.",
            severity="warning",
        )
        earlier = EvidenceItem(
            id="earlier",
            timestamp=datetime(2026, 8, 8, 10, 1, tzinfo=timezone.utc),
            domain="kubernetes",
            source="kubectl get events",
            title="Pod evicted",
            summary="Pod evicted due to DiskPressure.",
            severity="critical",
        )

        timeline = EvidenceTimeline(
            incident_id="incident-1",
            title="DiskPressure",
            items=[later, earlier],
        )

        self.assertEqual(
            [item.id for item in timeline.ordered_items()],
            ["earlier", "later"],
        )

    def test_dashboard_snapshot_combines_metrics_evidence_and_alerts(self) -> None:
        alert = AlertSignal(
            name="NodeDiskPressure",
            severity="critical",
            status="firing",
            summary="Node has DiskPressure.",
            source="kubernetes",
        )
        evidence = EvidenceItem(
            id="disk-finding",
            domain="linux",
            source="aop investigate linux disk",
            title="Filesystem capacity exhaustion",
            summary="Filesystem byte utilization is 96%.",
            severity="critical",
            structured={"use_percent": 96},
        )
        panel = DashboardPanel(
            id="disk",
            title="Disk pressure",
            panel_type="stat",
            domain="linux",
            evidence_items=[evidence],
            alerts=[alert],
        )
        snapshot = DashboardSnapshot(
            id="snapshot-1",
            title="Incident dashboard",
            incident_id="incident-1",
            panels=[panel],
            tags=["showcase"],
        )

        payload = snapshot.model_dump(mode="json")

        self.assertEqual(payload["panels"][0]["alerts"][0]["status"], "firing")
        self.assertEqual(
            payload["panels"][0]["evidence_items"][0]["structured"]["use_percent"],
            96,
        )


if __name__ == "__main__":
    unittest.main()
