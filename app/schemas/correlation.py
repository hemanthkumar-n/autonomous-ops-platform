from __future__ import annotations

from pydantic import BaseModel, Field


class LinuxEvidenceRequirement(BaseModel):
    domain: str
    reason: str
    commands: list[str] = Field(default_factory=list)


class KubernetesLinuxCorrelation(BaseModel):
    incident: str
    kubernetes_meaning: str
    linux_evidence: list[LinuxEvidenceRequirement] = Field(
        default_factory=list
    )
    kubernetes_checks: list[str] = Field(default_factory=list)
    cloud_checks: list[str] = Field(default_factory=list)
    do_not_assume: list[str] = Field(default_factory=list)
    next_aop_commands: list[str] = Field(default_factory=list)
    memory_note: str
