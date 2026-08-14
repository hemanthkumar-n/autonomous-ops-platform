from __future__ import annotations

import argparse

from app.schemas.evidence import EvidenceItem

from .autonomous_loop import AutonomousInvestigationLoop, EvidenceCollectionResult
from .models import EvidenceGap, Hypothesis, InvestigationCase


def _case() -> InvestigationCase:
    return InvestigationCase(
        id="AOP-DEMO-AUTO-1",
        title="CrashLoopBackOff with possible memory pressure",
        source="fixture",
        environment="demo",
        severity="warning",
        symptoms=["CrashLoopBackOff", "possible OOM"],
        evidence_gaps=[
            EvidenceGap(
                id="gap-linux-memory",
                description="Linux node memory evidence is missing.",
                priority="critical",
                reason="Need host evidence to separate workload OOM from node-wide pressure.",
                recommended_checks=["aop investigate linux memory"],
                blocks_rca=True,
            )
        ],
        hypotheses=[
            Hypothesis(
                id="node-memory-pressure",
                statement="Node-wide memory pressure caused the workload restart.",
                required_evidence_ids=["linux.memory.live"],
                missing_evidence_ids=["gap-linux-memory"],
            )
        ],
    )


def _linux_memory_collector(request, case):
    del case
    evidence = EvidenceItem(
        id="linux.memory.live",
        domain="linux",
        source="fixture-linux-memory",
        title="Linux memory pressure evidence",
        summary="Host memory evidence confirms active node-wide memory pressure.",
        severity="critical",
        structured={
            "mem_available_percent": 4.2,
            "swap_out_per_second": 128,
            "kernel_oom_events": 1,
        },
        tags=["memory", "pressure", "fixture"],
    )
    return EvidenceCollectionResult(
        request_id=request.id,
        evidence=[evidence],
        supporting_evidence={"node-memory-pressure": [evidence.id]},
        resolved_gap_ids=["gap-linux-memory"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dry-run the bounded AOP autonomous investigation loop."
    )
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    args = parser.parse_args()

    result = AutonomousInvestigationLoop(
        collectors={"linux_memory": _linux_memory_collector}
    ).run(_case())

    if args.format == "json":
        print(result.model_dump_json(indent=2))
        return

    print("AOP autonomous investigation loop")
    print(f"case: {result.case.id}")
    print(f"stop_reason: {result.stop_reason}")
    print(f"requests_executed: {result.total_requests_executed}")
    print(f"evidence_added: {result.total_evidence_added}")
    print(f"steps: {len(result.steps)}")
    print()

    for step in result.steps:
        print(f"Step {step.number}")
        print(f"  requests: {', '.join(step.executed_request_ids) or 'none'}")
        print(f"  skipped: {', '.join(step.skipped_request_ids) or 'none'}")
        print(f"  evidence_added: {step.evidence_added}")
        print(f"  decision: {step.decision_state}")
        print(f"  confidence: {step.confidence:.0%}")

    print()
    decision = result.case.decision
    if decision is not None:
        print(f"final_decision: {decision.state}")
        print(f"final_confidence: {decision.confidence:.0%}")
        print(f"leading_hypothesis: {decision.leading_hypothesis_id}")

    print("safety: registered read-only collectors only; no remediation executed")


if __name__ == "__main__":
    main()
