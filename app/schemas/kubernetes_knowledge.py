from __future__ import annotations

from pydantic import BaseModel, Field


class KubernetesIssueSource(BaseModel):
    title: str
    url: str
    source_type: str = "official-docs"


class KubernetesIssueKnowledge(BaseModel):
    symptom: str
    summary: str
    common_causes: list[str] = Field(default_factory=list)
    kubernetes_evidence: list[str] = Field(default_factory=list)
    linux_evidence: list[str] = Field(default_factory=list)
    safe_kubectl_commands: list[str] = Field(default_factory=list)
    safe_aop_commands: list[str] = Field(default_factory=list)
    do_not_assume: list[str] = Field(default_factory=list)
    escalation_signals: list[str] = Field(default_factory=list)
    sources: list[KubernetesIssueSource] = Field(default_factory=list)
