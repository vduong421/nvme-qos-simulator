# NVMe QoS Simulator

GitHub: https://github.com/vduong421/nvme-qos-simulator

An advanced storage-system simulation project for studying SSD behavior under mixed datacenter workloads such as AI feature stores, vector retrieval, OLTP, and analytics scans, with validation-health overlays for execution visibility.

## Why It Matches The Role

- Models PCIe, NVMe, NAND, queue depth, and garbage collection effects
- Tracks workload coverage, pass rate, and dataset freshness alongside QoS metrics
- Produces AI-style triage summaries useful for dashboarding and validation reviews

## Features

- Multi-workload simulation with mixed read/write traffic
- Tail-latency estimation for `p50`, `p95`, and `p99`
- Queue pressure and NAND backend penalties
- Validation coverage and pass-rate overlays per workload
- Simple recommendation engine for tuning architecture knobs and triage focus

## Run

```powershell
python -m src.nvme_qos_simulator.cli --scenario samples\baseline.json
```

## Web Dashboard

```powershell
python server.py
```

Then open `http://127.0.0.1:8001`.

## Example Output

- Aggregate IOPS and bandwidth
- Estimated latency percentiles
- Queue-utilization summary
- Recommendations for channel count, queue depth, and overprovisioning
