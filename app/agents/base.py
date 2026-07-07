from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.agent import AgentDomain, AgentFinding, AgentTask


class SpecialistAgent(ABC):
    """
    Base contract for all AOP specialist agents.

    Specialist agents do not directly perform remediation. They inspect task
    context, request or summarize evidence, and return structured findings.
    """

    name: str
    domain: AgentDomain

    @abstractmethod
    def analyze(self, task: AgentTask) -> AgentFinding:
        """
        Analyze a task and return a structured finding.
        """
