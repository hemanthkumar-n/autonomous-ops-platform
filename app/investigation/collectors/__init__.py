"""Read-only collector adapters for the autonomous investigation loop."""

from .linux_cpu import build_linux_cpu_collector
from .linux_disk import build_linux_disk_collector
from .linux_memory import build_linux_memory_collector
from .linux_network import build_linux_network_collector


def build_default_linux_collectors() -> dict[str, object]:
    """Build the default registered Linux collector set for autonomous investigation."""

    return {
        "linux_memory": build_linux_memory_collector(),
        "linux_cpu": build_linux_cpu_collector(),
        "linux_disk": build_linux_disk_collector(),
        "linux_network": build_linux_network_collector(),
    }


__all__ = [
    "build_default_linux_collectors",
    "build_linux_cpu_collector",
    "build_linux_disk_collector",
    "build_linux_memory_collector",
    "build_linux_network_collector",
]
