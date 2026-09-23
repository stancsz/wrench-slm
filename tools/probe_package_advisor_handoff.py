#!/usr/bin/env python3
"""Verify the bounded advisor handoff through a downloaded package endpoint."""

from __future__ import annotations

import argparse
import json
import sys
import threading
import urllib.request
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

    worker = WrenchWorker.from_pretrained(package_dir, allowed_root=Path.cwd(), load_model=False)
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        worker,
        model_name="wrench-handoff-probe",
        max_request_bytes=4 * 1024 * 1024,
        use_mechanical_route=False,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    request_body = json.dumps(
        {
            "model": "wrench-handoff-probe",
            "messages": [
                {"role": "system", "content": "proposal only, no mutation"},
                {"role": "user", "content": "Implement and deploy a new subsystem."},
            ],
            "max_tokens": 64,
            "stream": False,
        },
        ensure_ascii=False,
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

    wrench = body.get("wrench", {}) if isinstance(body, dict) else {}
    handoff = wrench.get("advisor_handoff") if isinstance(wrench, dict) else None
    status = (
        "PASS_PACKAGE_ADVISOR_HANDOFF"
        if status_code == 200
        and isinstance(handoff, dict)
        and handoff.get("schema") == "wrench.advisor-handoff.v1"
        and handoff.get("handoff_required") is True
        and handoff.get("raw_payload_hash_bound") is True
        and handoff.get("authority") == "proposal_only_no_mutation"
        and handoff.get("frontier_policy", {}).get("max_frontier_calls") == 2
        and handoff.get("frontier_policy", {}).get("frontier_must_not_execute_tools") is True
        else "FAIL_PACKAGE_ADVISOR_HANDOFF"
    )
    receipt = {
        "schema": "wrench.package-advisor-handoff-probe.v1",
        "status": status,
        "package_dir": str(package_dir),
        "http_status": status_code,
        "wrench": wrench,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "http_status": status_code}))
    return 0 if status == "PASS_PACKAGE_ADVISOR_HANDOFF" else 1


if __name__ == "__main__":
    raise SystemExit(main())
