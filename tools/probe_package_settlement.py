#!/usr/bin/env python3
"""Exercise the downloaded package's one-review plus one-repair settlement."""

from __future__ import annotations

import argparse
import json
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package_dir = args.package_dir.resolve()
    sys.path.insert(0, str(package_dir))
    from wrench_runtime.server import WrenchHTTPServer
    from wrench_runtime.worker import WrenchWorker

    calls: list[dict[str, object]] = []

    class UpstreamHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers["Content-Length"])
            calls.append(json.loads(self.rfile.read(length).decode("utf-8")))
            content = "not json" if len(calls) == 1 else json.dumps(
                {
                    "schema": "wrench.proposal.v1",
                    "action": "read_file",
                    "path": "pyproject.toml",
                    "max_bytes": 4096,
                }
            )
            body = json.dumps(
                {
                    "choices": [{"message": {"role": "assistant", "content": content}}],
                    "usage": {"prompt_tokens": 100, "completion_tokens": 5, "total_tokens": 105},
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    worker = WrenchWorker.from_pretrained(package_dir, allowed_root=Path.cwd(), load_model=False)
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        worker,
        model_name="wrench-settlement-probe",
        max_request_bytes=4 * 1024 * 1024,
        upstream_url=f"http://127.0.0.1:{upstream.server_port}/v1/chat/completions",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    request_body = json.dumps(
        {
            "model": "wrench-settlement-probe",
            "messages": [
                {"role": "system", "content": "Return one JSON proposal only."},
                {"role": "user", "content": "Review pyproject.toml and return a bounded proposal."},
            ],
            "max_tokens": 64,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status_code = response.status
            body = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)

    wrench = body.get("wrench", {}) if isinstance(body, dict) else {}
    usage = wrench.get("frontier_usage", {}) if isinstance(wrench, dict) else {}
    attempts = wrench.get("upstream_attempts", []) if isinstance(wrench, dict) else []
    status = (
        "PASS_PACKAGE_TWO_PASS_SETTLEMENT"
        if status_code == 200
        and len(calls) == 2
        and wrench.get("status") == "accepted"
        and wrench.get("model_calls") == 2
        and wrench.get("repair_pass_count") == 1
        and usage.get("total_tokens") == 210
        and attempts[0].get("fallback_reason") == "model_output_invalid_json"
        and attempts[1].get("status") == "accepted"
        else "FAIL_PACKAGE_TWO_PASS_SETTLEMENT"
    )
    receipt = {
        "schema": "wrench.package-two-pass-settlement-probe.v1",
        "status": status,
        "package_dir": str(package_dir),
        "http_status": status_code,
        "upstream_call_count": len(calls),
        "wrench": wrench,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "upstream_call_count": len(calls)}))
    return 0 if status == "PASS_PACKAGE_TWO_PASS_SETTLEMENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
