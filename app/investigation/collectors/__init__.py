"""Read-only collector adapters for the autonomous investigation loop."""

from .linux_cpu import build_linux_cpu_collector
from .linux_memory import build_linux_memory_collector

__all__ = ["build_linux_cpu_collector", "build_linux_memory_collector"]
