import unittest
from pathlib import Path

from src.nvme_qos_simulator.simulator import load_scenario, simulate_scenario


class SimulatorTests(unittest.TestCase):
    def test_simulation_returns_expected_sections(self) -> None:
        scenario = Path(__file__).resolve().parents[1] / "samples" / "baseline.json"
        device, workloads = load_scenario(scenario)
        result = simulate_scenario(device, workloads)

        self.assertIn("summary", result)
        self.assertIn("workloads", result)
        self.assertIn("ai_triage_summary", result)
        self.assertEqual(len(result["workloads"]), 3)
        self.assertIn("validation_coverage_pct", result["summary"])
        self.assertIn("triage_label", result["workloads"][0])
        self.assertGreater(
            result["summary"]["worst_case_p99_us"],
            result["workloads"][0]["p50_us"],
        )


if __name__ == "__main__":
    unittest.main()
