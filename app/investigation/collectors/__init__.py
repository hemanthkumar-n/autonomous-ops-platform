"""Read-only collector adapters for the autonomous investigation loop."""

from .linux_memory import build_linux_memory_collector

__all__ = ["build_linux_memory_collector"]
