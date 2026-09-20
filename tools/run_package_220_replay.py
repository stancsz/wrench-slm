#!/usr/bin/env python3
"""Replay the corrected 220-case workflow against a bundled Wrench package.

The package server and the diagnostic runner stay in one Python process so a
local package smoke does not depend on a manually managed background server.
The teacher arm reuses the sealed proposal capture and makes no provider call.
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--teacher-traces", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--port", type=int, default=28906)
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


if __name__ == "__main__":
    raise SystemExit(main())
