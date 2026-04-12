from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.nvme_qos_simulator.simulator import load_scenario, simulate_scenario


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
DEFAULT_SCENARIO = ROOT / "samples" / "baseline.json"


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

