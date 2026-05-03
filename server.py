from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.nvme_qos_simulator.simulator import load_scenario, simulate_scenario


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
GENERATED_SCENARIO = ROOT / "samples" / "generated_scenario.json"
DEFAULT_SCENARIO = GENERATED_SCENARIO if GENERATED_SCENARIO.exists() else ROOT / "samples" / "baseline.json"


def answer_question(question: str, payload: dict) -> dict:
    q = question.lower()
    summary = payload.get("summary", {})
    ai = payload.get("ai_copilot", {})
    workloads = payload.get("workload_ranking", payload.get("workloads", []))

    if "tail" in q or "latency" in q or "p99" in q:
        worst = summary.get("worst_latency_workload", {})
        answer = f"Worst tail latency is {summary.get('worst_case_p99_us', 0)} us from {worst.get('name', 'unknown')}."
        evidence = f"Latency buckets: {summary.get('latency_buckets', {})}."
        next_action = "Reduce queue depth or increase channel count for the worst p99 workload."
        recommendation = "Prioritize p99 mitigation before increasing target IOPS."
        decision = "Hold QoS signoff if p99 remains above 900 us."
    elif "saturation" in q or "queue" in q:
        hot = summary.get("most_saturated_workload", {})
        answer = f"Most saturated workload is {hot.get('name', 'unknown')} at {round(hot.get('saturation', 0) * 100, 1)}%."
        evidence = f"Average saturation is {round(summary.get('average_saturation', 0) * 100, 1)}%."
        next_action = "Review queue depth and channel pressure on saturated workloads."
        recommendation = "Model higher channel count if saturation stays above 90%."
        decision = "Do not scale workload mix until saturation headroom is validated."
    elif "bandwidth" in q or "iops" in q:
        bw = summary.get("highest_bandwidth_workload", {})
        answer = f"Total achieved IOPS is {summary.get('total_achieved_iops', 0)} and total bandwidth is {summary.get('total_bandwidth_gbps', 0)} Gbps."
        evidence = f"Highest bandwidth workload: {bw.get('name', 'unknown')} at {bw.get('bandwidth_gbps', 0)} Gbps."
        next_action = "Compare bandwidth-heavy workloads against PCIe and controller limits."
        recommendation = "Separate bandwidth sizing from p99 QoS sizing."
        decision = "Proceed only if both throughput and p99 targets pass."
    elif "recommend" in q or "improve" in q or "action" in q:
        answer = "Recommended tuning actions are based on queue pressure, channel pressure, and overprovisioning."
        evidence = "; ".join(payload.get("recommendations", []))
        next_action = "Apply the first recommendation and rerun the scenario."
        recommendation = ai.get("recommendation", "Tune queue depth and channel count.")
        decision = ai.get("decision", "Run another simulation after tuning.")
    else:
        answer = f"Simulated {len(payload.get('workloads', []))} workloads with release decision {summary.get('release_decision', 'unknown')}."
        evidence = ai.get("evidence", "Grounded in deterministic simulator output.")
        next_action = ai.get("next_action", "Review top risky workloads.")
        recommendation = ai.get("recommendation", "Tune hotspots first.")
        decision = ai.get("decision", "Use deterministic QoS results for design review.")

    return {
        "answer": answer,
        "evidence": evidence,
        "next_action": next_action,
        "recommendation": recommendation,
        "decision": decision,
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/run":
            query = parse_qs(parsed.query)
            scenario = Path(query.get("scenario", [str(DEFAULT_SCENARIO)])[0])
            if not scenario.is_absolute():
                scenario = ROOT / scenario
            device, workloads = load_scenario(scenario)
            payload = simulate_scenario(device, workloads)
            self._send_json(payload)
            return

        if parsed.path == "/api/chat":
            query = parse_qs(parsed.query)
            question = query.get("q", [""])[0]
            device, workloads = load_scenario(DEFAULT_SCENARIO)
            payload = simulate_scenario(device, workloads)
            self._send_json(answer_question(question, payload))
            return

        target = "index.html" if parsed.path in ("/", "") else parsed.path.lstrip("/")
        file_path = WEB_ROOT / target
        if file_path.exists() and file_path.is_file():
            self._send_file(file_path)
            return
        self.send_error(404, "Not Found")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send_json(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        content_type = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
        }.get(path.suffix, "application/octet-stream")
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8001), Handler)
    print("NVMe QoS dashboard running at http://127.0.0.1:8001")
    server.serve_forever()


if __name__ == "__main__":
    main()

