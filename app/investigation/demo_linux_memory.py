from __future__ import annotations

import argparse

from app.investigation.adapters import linux_memory_to_case
from app.investigation.reasoning import build_reasoning_summary
from app.orchestration.linux_memory_workflow import run_linux_memory_workflow
from app.schemas.linux import LinuxMemoryFinding, LinuxMemoryInvestigation


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run the v0.22 InvestigationCase. Use a deterministic fixture on macOS "
            "or --live on a Linux host."
        )
    )
    parser.add_argument(
        "--fixture",
        choices=("oom", "cgroup", "insufficient"),
        default="oom",
        help="Deterministic scenario for local validation. Ignored with --live.",
    )
    parser.add_argument("--live", action="store_true", help="Collect live read-only Linux memory evidence.")
    parser.add_argument("--pid", type=int, default=None)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--recent-minutes", type=int, default=60)
    parser.add_argument("--environment", default="local")
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    return parser


def _fixture(name: str) -> LinuxMemoryInvestigation:
    if name == "oom":
        return LinuxMemoryInvestigation(
            status="diagnosed",
            hostname="demo-node",
            platform="linux",
            primary_diagnosis="kernel_oom_kill",
            severity="critical",
            confidence=98,
            summary="Kernel OOM kill confirmed for the workload.",
            mem_total_kb=8_388_608,
            mem_available_kb=335_544,
            mem_available_percent=4.0,
            swap_total_kb=2_097_152,
            swap_free_kb=1_900_000,
            swap_used_percent=9.4,
            swap_in_per_second=0,
            swap_out_per_second=0,
            oom_events=["Out of memory: Killed process 4242 (checkout-api)"],
            top_memory_processes=["4242 checkout-api 48.2%"],
            findings=[
                LinuxMemoryFinding(
                    code="kernel_oom_kill",
                    severity="critical",
                    confidence=98,
                    summary="Recent kernel evidence contains OOM kill activity.",
                    evidence=["Out of memory: Killed process 4242 (checkout-api)"],
                    next="Identify the victim process, owning service or pod, and memory boundary.",
                    next_explanation="Kernel OOM evidence proves an allocation failure occurred.",
                )
            ],
        )

    if name == "cgroup":
        return LinuxMemoryInvestigation(
            status="diagnosed",
            hostname="demo-node",
            platform="linux",
            pid=4242,
            primary_diagnosis="cgroup_memory_high",
            severity="warning",
            confidence=88,
            summary="The workload crossed its cgroup memory.high boundary.",
            mem_total_kb=16_777_216,
            mem_available_kb=8_388_608,
            mem_available_percent=50.0,
            cgroup_memory={"memory_max": "max", "event_high": 3, "event_oom": 0},
            findings=[
                LinuxMemoryFinding(
                    code="cgroup_memory_high",
                    severity="warning",
                    confidence=88,
                    summary="memory.high events indicate workload-level pressure.",
                    evidence=["event_high=3"],
                    next="Inspect workload memory growth and configured cgroup boundaries.",
                    next_explanation="The host can remain healthy while a workload is throttled by its cgroup.",
                )
            ],
        )

    return LinuxMemoryInvestigation(
        status="diagnosed",
        hostname="demo-node",
        platform="linux",
        primary_diagnosis="insufficient_evidence",
        severity="info",
        confidence=30,
        summary="Memory evidence is insufficient for a reliable diagnosis.",
        evidence_gaps=["meminfo: unavailable", "vmstat: missing"],
        findings=[
            LinuxMemoryFinding(
                code="insufficient_evidence",
                severity="info",
                confidence=30,
                summary="Required memory evidence is unavailable.",
                evidence=[],
                next="Collect meminfo and vmstat evidence before finalizing RCA.",
                next_explanation="AOP should expose missing evidence instead of guessing.",
            )
        ],
    )


def main() -> None:
    args = _parser().parse_args()
    if args.pid is not None and args.pid <= 0:
        raise SystemExit("--pid must be greater than zero")
    if not 1 <= args.top <= 100:
        raise SystemExit("--top must be between 1 and 100")
    if not 1 <= args.recent_minutes <= 10_080:
        raise SystemExit("--recent-minutes must be between 1 and 10080")

    if args.live:
        investigation, _ = run_linux_memory_workflow(
            pid=args.pid,
            top=args.top,
            recent_minutes=args.recent_minutes,
            persist=False,
        )
    else:
        investigation = _fixture(args.fixture)

    case = linux_memory_to_case(investigation, environment=args.environment)

    if args.format == "json":
        print(case.model_dump_json(indent=2))
        return

    decision = case.decision
    print(f"InvestigationCase: {case.id}")
    print(f"Mode: {'live' if args.live else 'fixture:' + args.fixture}")
    print(f"Title: {case.title}")
    print(f"Severity: {case.severity}")
    print(f"Evidence items: {len(case.evidence)}")
    print(f"Evidence gaps: {len(case.evidence_gaps)}")
    if decision:
        print(f"Decision: {decision.state}")
        print(f"Confidence: {decision.confidence:.0%}")
        if decision.leading_hypothesis_id:
            print(f"Leading hypothesis: {decision.leading_hypothesis_id}")
    if case.root_cause:
        print(f"RCA candidate: {case.root_cause}")

    print()
    print(build_reasoning_summary(case))

    if case.recommendations:
        print("\nRecommended next actions")
        for item in case.recommendations:
            print(f"- {item}")


if __name__ == "__main__":
    main()
