from __future__ import annotations

import unittest

from app.agents.sre.incident_classifier import classify_incident
from app.schemas.incident import ContainerState, IncidentContext


class IncidentClassifierTests(unittest.TestCase):
    def test_selects_one_highest_severity_incident_per_pod(self) -> None:
        incident = IncidentContext(
            pod_name="checkout",
            namespace="payments",
            phase="Running",
            container_states=[
                ContainerState(
                    container="sidecar",
                    state="CrashLoopBackOff",
                    restart_count=4,
                ),
                ContainerState(
                    container="application",
                    state="CrashLoopBackOff",
                    restart_count=8,
                    last_termination={
                        "reason": "OOMKilled",
                        "exit_code": 137,
                    },
                ),
            ],
        )

        results = classify_incident([incident])

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].incident_type,
            "MemoryExhaustion",
        )
        self.assertEqual(
            results[0].container,
            "application",
        )


if __name__ == "__main__":
    unittest.main()
