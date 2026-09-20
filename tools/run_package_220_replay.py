#!/usr/bin/env python3
"""Replay the corrected 220-case workflow against a bundled Wrench package.

The package server and the diagnostic runner stay in one Python process so a
local package smoke does not depend on a manually managed background server.
The teacher arm reuses the sealed proposal capture and makes no provider call.
"""

from __future__ import annotations

import argparse
import http.server
import os
import sys
import threading
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class _HealthFixtureHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/health", "/v1/models"}:
            payload = b'{"status":"ok","fixture":true}\n'
            status = 200
        else:
            payload = b"not found\n"
            status = 404
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--teacher-traces", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--port", type=int, default=28906)
    parser.add_argument("--health-fixture", action="store_true")
    parser.add_argument("--health-fixture-port", type=int, default=28907)
    parser.add_argument(
        "--allow-noncanonical-count",
        action="store_true",
        help="allow a sealed diagnostic slice such as final.jsonl instead of the 220-case fixture",
    )
    args = parser.parse_args()

    package_dir = args.package_dir.resolve()
    if not package_dir.is_dir():
        raise ValueError(f"package directory does not exist: {package_dir}")
    sys.path.insert(0, str(package_dir))
    sys.path.insert(0, str(REPO_ROOT))

    from wrench_runtime.server import WrenchHTTPServer
    from wrench_runtime.worker import WrenchWorker

    allowed_root = args.root.resolve()
    worker = WrenchWorker(tokenizer=None, model=None, allowed_root=allowed_root)
    fixture = None
    if args.health_fixture:
        fixture = http.server.ThreadingHTTPServer(("127.0.0.1", args.health_fixture_port), _HealthFixtureHandler)
        fixture_thread = threading.Thread(target=fixture.serve_forever, daemon=True)
        fixture_thread.start()
        os.environ["WRENCH_TEST_HEALTH_FIXTURE_BASE_URL"] = f"http://127.0.0.1:{args.health_fixture_port}"
    server = WrenchHTTPServer(
        ("127.0.0.1", args.port),
        worker,
        model_name="wrench-package-replay",
        max_request_bytes=512 * 1024 * 1024,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)
    try:
        from tools import run_diagnostic_worker_arms

        sys.argv = [
            "run_diagnostic_worker_arms.py",
            "--cases",
            str(args.cases),
            "--root",
            str(args.root),
            "--teacher-traces",
            str(args.teacher_traces),
            "--wrench-endpoint",
            f"http://127.0.0.1:{args.port}/v1/chat/completions",
            "--wrench-model",
            "wrench-package-replay",
            "--output-dir",
            str(args.output_dir),
            "--disable-client-mechanical-fast-path",
        ]
        return run_diagnostic_worker_arms.main()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        if fixture is not None:
            fixture.shutdown()
            fixture.server_close()
            fixture_thread.join(timeout=5)
            os.environ.pop("WRENCH_TEST_HEALTH_FIXTURE_BASE_URL", None)


if __name__ == "__main__":
    raise SystemExit(main())
