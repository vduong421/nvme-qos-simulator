from __future__ import annotations

import argparse
import json

from .simulator import load_scenario, simulate_scenario


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an NVMe QoS scenario.")
    parser.add_argument("--scenario", required=True, help="Path to scenario JSON.")
    args = parser.parse_args()

    device, workloads = load_scenario(args.scenario)
    result = simulate_scenario(device, workloads)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

