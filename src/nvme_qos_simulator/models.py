from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceProfile:
    name: str
    pcie_generation: int
    channels: int
    max_queue_depth: int
    overprovisioning_pct: float
    base_read_us: float
    base_write_us: float
    nand_write_penalty_us: float


@dataclass(frozen=True)
class WorkloadProfile:
    name: str
    read_ratio: float
    write_ratio: float
    block_kb: int
    queue_depth: int
    target_iops: int
    burstiness: float


@dataclass(frozen=True)
class WorkloadResult:
    name: str
    achieved_iops: float
    bandwidth_gbps: float
    p50_us: float
    p95_us: float
    p99_us: float
    saturation: float

