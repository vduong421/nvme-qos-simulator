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

    worst_latency = max(results, key=lambda item: item.p99_us, default=None)
    most_saturated = max(results, key=lambda item: item.saturation, default=None)
    highest_bandwidth = max(results, key=lambda item: item.bandwidth_gbps, default=None)

    latency_buckets = {
        "healthy_under_500us": sum(1 for item in results if item.p99_us < 500),
        "watch_500_900us": sum(1 for item in results if 500 <= item.p99_us <= 900),
        "risk_over_900us": sum(1 for item in results if item.p99_us > 900),
    }

    workload_ranking = sorted(
        [result.__dict__ for result in results],
        key=lambda item: (item["p99_us"], item["saturation"]),
        reverse=True,
    )

    release_decision = "hold" if worst_p99 > 900 or avg_saturation > 0.9 else "ready"

    ai_copilot = {
        "result": f"Simulated {len(results)} NVMe workloads with worst p99 latency {round(worst_p99, 2)} us.",
        "answer": "The deterministic simulator found queue pressure, channel pressure, and tail-latency risk across mixed workloads.",
        "evidence": f"Average saturation={round(avg_saturation, 3)}, total IOPS={round(total_iops, 2)}, total bandwidth={round(total_bw, 3)} Gbps.",
        "next_action": "Review the highest p99 and highest saturation workloads first.",
        "recommendation": recommendations[0] if recommendations else "QoS headroom is healthy.",
        "decision": "Hold design review until tail-latency hotspots are mitigated." if release_decision == "hold" else "Proceed with current baseline and validate with burstier workloads.",
        "risks": [
            f"Worst latency workload: {worst_latency.name if worst_latency else 'n/a'}",
            f"Most saturated workload: {most_saturated.name if most_saturated else 'n/a'}",
            f"Risk bucket count: {latency_buckets['risk_over_900us']}"
        ],
        "operator_actions": [
            "Tune queue depth for tail-latency hotspots",
            "Increase channels if saturation remains high",
            "Increase overprovisioning for write-heavy workloads"
        ]
    }

    return {
        "device": device.__dict__,
        "summary": {
            "total_achieved_iops": round(total_iops, 2),
            "total_bandwidth_gbps": round(total_bw, 3),
            "average_saturation": round(avg_saturation, 3),
            "worst_case_p99_us": round(worst_p99, 2),
            "release_decision": release_decision,
            "latency_buckets": latency_buckets,
            "worst_latency_workload": worst_latency.__dict__ if worst_latency else {},
            "most_saturated_workload": most_saturated.__dict__ if most_saturated else {},
            "highest_bandwidth_workload": highest_bandwidth.__dict__ if highest_bandwidth else {},
        },
        "workloads": [result.__dict__ for result in results],
        "workload_ranking": workload_ranking[:15],
        "recommendations": recommendations,
        "ai_copilot": ai_copilot,
    }

