from __future__ import annotations

import json
from pathlib import Path

from .models import DeviceProfile, WorkloadProfile, WorkloadResult


def load_scenario(path: str | Path) -> tuple[DeviceProfile, list[WorkloadProfile]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    device = DeviceProfile(**payload["device"])
    workloads = [WorkloadProfile(**item) for item in payload["workloads"]]
    return device, workloads


def simulate_workload(device: DeviceProfile, workload: WorkloadProfile) -> WorkloadResult:
    queue_pressure = workload.queue_depth / max(device.max_queue_depth, 1)
    channel_pressure = workload.target_iops / max(device.channels * 22000, 1)
    op_penalty = max(0.0, (1.0 - device.overprovisioning_pct / 20.0)) * 18.0

    base_latency = (
        workload.read_ratio * device.base_read_us
        + workload.write_ratio * (device.base_write_us + device.nand_write_penalty_us)
    )
    block_penalty = max(0, workload.block_kb - 4) * 0.85
    burst_penalty = (workload.burstiness - 1.0) * 45.0
    queue_penalty = queue_pressure * 95.0
    channel_penalty = max(0.0, channel_pressure - 1.0) * 140.0
    p50 = base_latency + block_penalty + burst_penalty + queue_penalty + op_penalty
    p95 = p50 * (1.35 + queue_pressure * 0.30 + max(0.0, channel_pressure - 0.8) * 0.22)
    p99 = p95 * (1.15 + workload.write_ratio * 0.25 + max(0.0, channel_pressure - 1.0) * 0.35)

    pcie_factor = {3: 0.82, 4: 0.93, 5: 1.0, 6: 1.12}.get(device.pcie_generation, 0.9)
    service_budget_iops = device.channels * 22000 * pcie_factor
    qos_penalty = min(0.45, max(0.0, p99 - 800.0) / 4000.0)
    achieved_iops = min(workload.target_iops, service_budget_iops * (1.0 - qos_penalty))
    bandwidth_gbps = achieved_iops * workload.block_kb * 8 / 1_000_000

    return WorkloadResult(
        name=workload.name,
        achieved_iops=round(achieved_iops, 2),
        bandwidth_gbps=round(bandwidth_gbps, 3),
        p50_us=round(p50, 2),
        p95_us=round(p95, 2),
        p99_us=round(p99, 2),
        saturation=round(min(1.5, workload.target_iops / max(service_budget_iops, 1)), 3),
    )


def simulate_scenario(device: DeviceProfile, workloads: list[WorkloadProfile]) -> dict:
    results = [simulate_workload(device, workload) for workload in workloads]
    avg_saturation = sum(result.saturation for result in results) / max(len(results), 1)
    worst_p99 = max((result.p99_us for result in results), default=0.0)
    total_iops = sum(result.achieved_iops for result in results)
    total_bw = sum(result.bandwidth_gbps for result in results)

    recommendations: list[str] = []
    if worst_p99 > 900:
        recommendations.append("Reduce queue-depth hotspots or increase channels to improve tail latency.")
    if avg_saturation > 0.9:
        recommendations.append("Current traffic is near controller saturation; model a higher-channel design.")
    if device.overprovisioning_pct < 15:
        recommendations.append("Increase overprovisioning to reduce write-amplification and garbage-collection stalls.")
    if not recommendations:
        recommendations.append("QoS headroom is healthy; validate with a burstier AI checkpointing workload.")

    return {
        "device": device.__dict__,
        "summary": {
            "total_achieved_iops": round(total_iops, 2),
            "total_bandwidth_gbps": round(total_bw, 3),
            "average_saturation": round(avg_saturation, 3),
            "worst_case_p99_us": round(worst_p99, 2),
        },
        "workloads": [result.__dict__ for result in results],
        "recommendations": recommendations,
    }

