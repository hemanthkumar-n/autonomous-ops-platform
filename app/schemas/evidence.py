from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


EvidenceDomain = Literal[
    "linux",
    "kubernetes",
    "aws",
    "observability",
    "network",
    "security",
    "application",
    "unknown",
]

Severity = Literal["info", "warning", "critical"]
MetricUnit = Literal[
    "count",
    "percent",
    "bytes",
    "seconds",
    "milliseconds",
    "microseconds",
    "rate",
    "ratio",
    "unknown",
]
PanelType = Literal["timeseries", "stat", "table", "timeline", "logs"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MetricPoint(BaseModel):
    """
    One provider-neutral metric sample.
    """

    timestamp: datetime
    value: float
    unit: MetricUnit = "unknown"
    labels: dict[str, str] = Field(default_factory=dict)
    source: str = ""


class MetricSeries(BaseModel):
    """
    Named metric series usable by CLI, UI, reports, and AI context.
    """

    name: str
    query: str = ""
    unit: MetricUnit = "unknown"
    domain: EvidenceDomain = "unknown"
    points: list[MetricPoint] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)
    source: str = ""


class AlertSignal(BaseModel):
    """
    Normalized alert or threshold signal from any provider.
    """

    name: str
    severity: Severity
    status: Literal["firing", "resolved", "suppressed", "unknown"] = "unknown"
    summary: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    source: str = ""


class EvidenceItem(BaseModel):
    """
    One normalized evidence record collected during investigation.
    """

    id: str
    timestamp: datetime = Field(default_factory=utc_now)
    domain: EvidenceDomain
    source: str
    title: str
    summary: str
    severity: Severity = "info"
    command: str | None = None
    raw: str | None = None
    structured: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class EvidenceTimeline(BaseModel):
    """
    Ordered incident evidence for reports, UI, chat, and memory.
    """

    incident_id: str
    title: str
    items: list[EvidenceItem] = Field(default_factory=list)

    def ordered_items(self) -> list[EvidenceItem]:
        return sorted(self.items, key=lambda item: item.timestamp)


class DashboardPanel(BaseModel):
    """
    Provider-neutral dashboard panel definition.
    """

    id: str
    title: str
    panel_type: PanelType
    domain: EvidenceDomain = "unknown"
    description: str = ""
    metric_series: list[MetricSeries] = Field(default_factory=list)
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    alerts: list[AlertSignal] = Field(default_factory=list)
    options: dict[str, Any] = Field(default_factory=dict)


class DashboardSnapshot(BaseModel):
    """
    Point-in-time dashboard state for UI, reports, and incident memory.
    """

    id: str
    title: str
    created_at: datetime = Field(default_factory=utc_now)
    incident_id: str | None = None
    panels: list[DashboardPanel] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source: str = "aop"
