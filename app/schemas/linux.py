from __future__ import annotations

from pydantic import BaseModel, Field


class PressureSample(BaseModel):
    avg10: float
    avg60: float
    avg300: float
    total: int


class PressureResource(BaseModel):
    some: PressureSample | None = None
    full: PressureSample | None = None


class LinuxFinding(BaseModel):
    severity: str
    area: str
    summary: str
    next: str


class LinuxInternalsEvidence(BaseModel):
    status: str
    hostname: str
    load_average: list[float] = Field(default_factory=list)
    running_tasks: int | None = None
    total_tasks: int | None = None
    last_pid: int | None = None
    uptime_seconds: float | None = None
    cpu_count: int
    process_states: dict[str, int] = Field(default_factory=dict)
    pressure: dict[str, PressureResource] = Field(default_factory=dict)
    vm_counters: dict[str, int] = Field(default_factory=dict)
    findings: list[LinuxFinding] = Field(default_factory=list)
    unavailable: list[str] = Field(default_factory=list)


class CgroupMembership(BaseModel):
    hierarchy_id: int
    controllers: list[str] = Field(default_factory=list)
    path: str


class CgroupEvidence(BaseModel):
    status: str
    hostname: str
    pid: int
    version: int | None = None
    memberships: list[CgroupMembership] = Field(default_factory=list)
    cgroup_path: str | None = None
    controllers: list[str] = Field(default_factory=list)
    cpu: dict[str, str | int] = Field(default_factory=dict)
    memory: dict[str, str | int] = Field(default_factory=dict)
    io: dict[str, str | int] = Field(default_factory=dict)
    pids: dict[str, str | int] = Field(default_factory=dict)
    pressure: dict[str, PressureResource] = Field(default_factory=dict)
    findings: list[LinuxFinding] = Field(default_factory=list)
    unavailable: list[str] = Field(default_factory=list)
