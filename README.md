# NVMe QoS Simulator

An advanced storage-system simulation project for studying SSD behavior under mixed datacenter workloads such as AI feature stores, vector retrieval, OLTP, and analytics scans.

## Why It Matches The Role

- Models PCIe, NVMe, NAND, queue depth, and garbage collection effects
- Focuses on system-level behavior across diverse workloads
- Produces outputs useful for customer technical reviews and roadmap conversations

## Features

- Multi-workload simulation with mixed read/write traffic
- Tail-latency estimation for `p50`, `p95`, and `p99`
- Queue pressure and NAND backend penalties
- Simple recommendation engine for tuning architecture knobs

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

## Project Workbench

Launch the production-style desktop workbench with:

```powershell
launch-workbench.bat
```

What it adds:

- Local-first AI copilot using `google/gemma-4-e4b` by default
- Operator-focused workbench for reviewing real project inputs and outputs
- System design, production-impact, and operational brief generation on demand
- Grounded responses based on this project's README, sample files, and deterministic outputs
