from pydantic import BaseModel
from typing import Optional


class PodMetrics(BaseModel):
    """
    Typed observability metrics contract.
    """

    memory_usage_bytes: Optional[float] = None
    cpu_usage: Optional[float] = None
    restart_metric: Optional[float] = None