from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


AgentDomain = Literal[
    "linux",
    "kubernetes",
    "observability",
    "memory",
    "reasoning",
    "remediation",
    "orchestrator",
]

AgentPriority = Literal["low", "medium", "high", "critical"]
AgentFindingSeverity = Literal["info", "warning", "high", "critical"]


class AgentTask(BaseModel):
    """
    Work request assigned to a specialist AOP agent.
    """

    task_id: str
    domain: AgentDomain
    objective: str
    priority: AgentPriority = "medium"
    context: dict[str, Any] = Field(default_factory=dict)
    requested_evidence: list[str] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class AgentFinding(BaseModel):
    """
    Structured output produced by a specialist AOP agent.
    """

    agent_name: str
    domain: AgentDomain
    summary: str
    severity: AgentFindingSeverity = "info"
    confidence: int = Field(default=50, ge=0, le=100)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
