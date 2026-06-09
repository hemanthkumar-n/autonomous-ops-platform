from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.tools.kubernetes.operations import list_pods


def _state(
    waiting=None,
    terminated=None,
    running=None,
):
    return SimpleNamespace(
        waiting=waiting,
        terminated=terminated,
        running=running,
    )


class KubernetesOperationsTests(unittest.TestCase):
    @patch(
        "app.tools.kubernetes.operations.load_clients"
    )
    def test_ready_restarted_pod_is_not_unhealthy(
        self,
        load_clients,
    ) -> None:
        status = SimpleNamespace(
            ready=True,
            restart_count=2,
            state=_state(
                running=SimpleNamespace(),
            ),
            last_state=SimpleNamespace(
                terminated=SimpleNamespace(
                    reason="OOMKilled",
                )
            ),
        )
        pod = SimpleNamespace(
            metadata=SimpleNamespace(
                namespace="payments",
                name="checkout",
                creation_timestamp=datetime.now(
                    timezone.utc
                ),
            ),
            status=SimpleNamespace(
                container_statuses=[status],
                phase="Running",
            ),
            spec=SimpleNamespace(
                node_name="worker-1",
            ),
        )
        core = Mock()
        core.list_namespaced_pod.return_value = (
            SimpleNamespace(items=[pod])
        )
        load_clients.return_value = (core, Mock())

        result = list_pods(
            namespace="payments",
            unhealthy_only=True,
        )

        self.assertEqual(result, [])

    @patch(
        "app.tools.kubernetes.operations.load_clients"
    )
    def test_succeeded_job_pod_is_not_unhealthy(
        self,
        load_clients,
    ) -> None:
        status = SimpleNamespace(
            ready=False,
            restart_count=0,
            state=_state(
                terminated=SimpleNamespace(
                    reason="Completed",
                    message=None,
                )
            ),
            last_state=None,
        )
        pod = SimpleNamespace(
            metadata=SimpleNamespace(
                namespace="jobs",
                name="backup-job",
                creation_timestamp=datetime.now(
                    timezone.utc
                ),
            ),
            status=SimpleNamespace(
                container_statuses=[status],
                phase="Succeeded",
            ),
            spec=SimpleNamespace(
                node_name="worker-1",
            ),
        )
        core = Mock()
        core.list_namespaced_pod.return_value = (
            SimpleNamespace(items=[pod])
        )
        load_clients.return_value = (core, Mock())

        result = list_pods(
            namespace="jobs",
            unhealthy_only=True,
        )

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
