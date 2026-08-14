from __future__ import annotations

import argparse

from app.schemas.evidence import EvidenceItem

from .autonomous_loop import AutonomousInvestigationLoop, EvidenceCollectionResult
from .models import AffectedResource, EvidenceGap, Hypothesis, InvestigationCase


def _case() -> InvestigationCase:
    return InvestigationCase(
        id="AOP-DEMO-AUTO-2",
        title="CrashLoopBackOff with possible memory pressure",
        source="fixture",
        environment="demo",
        severity="warning",
        symptoms=["CrashLoopBackOff", "possible OOM"],
        affected_resources=[
            AffectedResource(
                domain="kubernetes",
                kind="pod",
                name="checkout-api-7d8f9",
                namespace="payments",
                cluster="demo-cluster",
                node="worker-03",
            ),
            AffectedResource(
                domain="linux",
                kind="host",
                name="worker-03",
            ),
        ],
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
        supporting_reasons={
            "node-memory-pressure": [
                "MemAvailable is critically low at 4.2%.",
                "Active swap-out indicates host reclaim pressure.",
                "Kernel OOM activity is present on the node.",
            ]
        },
        contradicting_reasons={
            "node-memory-pressure": [
                "A workload-only memory limit failure is not yet independently proven."
            ]
        },
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

    print("AOP autonomous investigation loop v0.42")
    print(f"case: {result.case.id}")
    print(f"stop_reason: {result.stop_reason}")
    print(f"requests_executed: {result.total_requests_executed}")
    print(f"evidence_added: {result.total_evidence_added}")
    print(f"steps: {len(result.steps)}")
    print()

    for step in result.steps:
        print(f"Step {step.number}")
        print(f"  requests: {', '.join(step.executed_request_ids) or 'none'}")
        print(f"  evidence_added: {step.evidence_added}")
        print(f"  decision: {step.decision_state}")
        print(f"  confidence: {step.confidence:.0%}")
        for request in step.plan.requests:
            if request.metadata:
                print(f"  resource_context: {request.metadata}")

    candidate = result.case.rca_candidate
    if candidate:
        print()
        print(f"RCA candidate: {candidate.statement}")
        print(f"confidence: {candidate.confidence:.0%}")
        print("why:")
        for reason in candidate.why:
            print(f"  + {reason}")
        print("why-not / alternatives:")
        for reason in candidate.why_not:
            print(f"  - {reason}")
        print("confirmed_root_cause: none")

    print("safety: registered read-only collectors only; no remediation executed")


if __name__ == "__main__":
    main()
