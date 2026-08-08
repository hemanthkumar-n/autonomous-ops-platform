from __future__ import annotations

import unittest

from app.agents.linux.service_agent import analyze_service_evidence


def _result(key: str, output: str = "", status: str = "ok") -> dict:
    return {
        "key": key,
        "label": key.replace("_", " "),
        "command": key,
        "status": status,
        "output": output,
        "error": "",
        "exit_code": 0 if status == "ok" else 1,
        "requires_root": False,
    }


def _properties(
    active: str = "active",
    result: str = "success",
    status: str = "0",
    restarts: str = "0",
    restart: str = "no",
) -> str:
    return "\n".join(
        [
            f"ActiveState={active}",
            "SubState=running",
            f"Result={result}",
            "ExecMainCode=1",
            f"ExecMainStatus={status}",
            f"NRestarts={restarts}",
            f"Restart={restart}",
            "RestartUSec=100ms",
            "LoadState=loaded",
            "UnitFileState=enabled",
        ]
    )


def _evidence(properties: str | None = None, journal: str = "") -> dict:
    return {
        "domain": "service",
        "status": "collected",
        "host": "web-01",
        "platform": "Linux",
        "service": "nginx.service",
        "results": [
            _result("status", "nginx.service - running"),
            _result("properties", properties if properties is not None else _properties()),
            _result("unit_file", "[Service]\nRestart=on-failure"),
            _result("journal", journal or "-- No entries --"),
        ],
    }


class LinuxServiceAgentTests(unittest.TestCase):
    def test_start_limit_hit_is_primary(self) -> None:
        investigation = analyze_service_evidence(
            _evidence(
                properties=_properties(
                    active="failed",
                    result="start-limit-hit",
                    status="1",
                    restarts="5",
                    restart="on-failure",
                )
            )
        )

        self.assertEqual(investigation.primary_diagnosis, "start_limit_hit")
        self.assertIn("repeated failures", investigation.findings[0].next_explanation)

    def test_failed_exit_status_is_detected(self) -> None:
        investigation = analyze_service_evidence(
            _evidence(
                properties=_properties(
                    active="failed",
                    result="exit-code",
                    status="2",
                )
            )
        )

        codes = [finding.code for finding in investigation.findings]
        self.assertEqual(investigation.primary_diagnosis, "service_failed")
        self.assertIn("nonzero_exit_status", codes)

    def test_restart_policy_loop_is_detected(self) -> None:
        investigation = analyze_service_evidence(
            _evidence(
                properties=_properties(
                    restart="always",
                    restarts="3",
                )
            )
        )

        self.assertEqual(investigation.primary_diagnosis, "restart_policy_loop")
        self.assertIn("crash loop", investigation.findings[0].next_explanation)

    def test_journal_errors_are_preserved(self) -> None:
        investigation = analyze_service_evidence(
            _evidence(journal="nginx[1]: config test failed")
        )

        self.assertEqual(investigation.primary_diagnosis, "journal_error_evidence")
        self.assertEqual(investigation.journal_errors[0], "nginx[1]: config test failed")

    def test_missing_properties_becomes_insufficient_evidence(self) -> None:
        evidence = _evidence()
        evidence["results"][1] = _result("properties", status="unavailable")

        investigation = analyze_service_evidence(evidence)

        self.assertEqual(investigation.primary_diagnosis, "insufficient_evidence")
        self.assertTrue(investigation.evidence_gaps)


if __name__ == "__main__":
    unittest.main()
