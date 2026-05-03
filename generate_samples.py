import json
import random
from pathlib import Path

random.seed(42)

workload_types = [
    ("AI Feature Store", 0.82, 0.18, 16),
    ("Vector Retrieval", 0.90, 0.10, 32),
    ("OLTP", 0.68, 0.32, 8),
    ("Analytics Scan", 0.95, 0.05, 128),
    ("Checkpoint Writer", 0.30, 0.70, 64),
    ("Metadata Service", 0.75, 0.25, 4),
    ("RAG Index Build", 0.55, 0.45, 32),
    ("Model Serving Cache", 0.88, 0.12, 16),
]

workloads = []
for i in range(1, 61):
    name, read_ratio, write_ratio, block_kb = random.choice(workload_types)
    jitter = random.uniform(-0.06, 0.06)
    rr = min(0.98, max(0.20, read_ratio + jitter))
    wr = round(1.0 - rr, 2)

    workloads.append({
        "name": f"{name} {i:02d}",
        "read_ratio": round(rr, 2),
        "write_ratio": wr,
        "block_kb": block_kb,
        "queue_depth": random.choice([16, 32, 48, 64, 96, 128, 192]),
        "target_iops": random.randint(25000, 360000),
        "burstiness": round(random.uniform(1.0, 1.75), 2)
    })

scenario = {
    "device": {
        "name": "PCIe Gen5 TLC SSD",
        "pcie_generation": 5,
        "channels": 16,
        "max_queue_depth": 256,
        "overprovisioning_pct": 12,
        "base_read_us": 82,
        "base_write_us": 118,
        "nand_write_penalty_us": 46
    },
    "workloads": workloads
}

Path("samples").mkdir(exist_ok=True)
Path("samples/generated_scenario.json").write_text(json.dumps(scenario, indent=2), encoding="utf-8")
print(f"[OK] Generated {len(workloads)} NVMe workloads")