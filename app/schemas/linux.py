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


class LinuxDiskFinding(BaseModel):
    code: str
    severity: str
    confidence: int = Field(ge=0, le=100)
    summary: str
    evidence: list[str] = Field(default_factory=list)
    next: str


class LinuxDiskInvestigation(BaseModel):
    status: str
    hostname: str
    path: str
    platform: str
    primary_diagnosis: str
    severity: str
    confidence: int = Field(ge=0, le=100)
    summary: str
    filesystem_use_percent: float | None = None
    inode_use_percent: float | None = None
    mount_source: str | None = None
    filesystem_type: str | None = None
    mount_point: str | None = None
    mount_options: list[str] = Field(default_factory=list)
    largest_paths: list[str] = Field(default_factory=list)
    recent_large_files: list[str] = Field(default_factory=list)
    deleted_open_files: list[str] = Field(default_factory=list)
    kernel_storage_errors: list[str] = Field(default_factory=list)
    findings: list[LinuxDiskFinding] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    raw_evidence: dict = Field(default_factory=dict)


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


class CounterDelta(BaseModel):
    before: int
    after: int
    delta: int
    per_second: float


class PressureDelta(BaseModel):
    some_stall_percent: float | None = None
    full_stall_percent: float | None = None


class LinuxInternalsSample(BaseModel):
    status: str
    hostname: str
    interval_seconds: float
    before: LinuxInternalsEvidence
    after: LinuxInternalsEvidence
    vm_deltas: dict[str, CounterDelta] = Field(default_factory=dict)
    pressure_deltas: dict[str, PressureDelta] = Field(default_factory=dict)
    findings: list[LinuxFinding] = Field(default_factory=list)


class CgroupSample(BaseModel):
    status: str
    hostname: str
    pid: int
    interval_seconds: float
    before: CgroupEvidence
    after: CgroupEvidence
    cpu_deltas: dict[str, CounterDelta] = Field(default_factory=dict)
    memory_event_deltas: dict[str, CounterDelta] = Field(default_factory=dict)
    pids_event_deltas: dict[str, CounterDelta] = Field(default_factory=dict)
    pressure_deltas: dict[str, PressureDelta] = Field(default_factory=dict)
    findings: list[LinuxFinding] = Field(default_factory=list)
