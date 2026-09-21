#!/usr/bin/env python3
"""Probe the OpenAI-compatible server shipped inside a Wrench package."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import time
import urllib.request
from pathlib import Path


UNIT = "old reference status observed record=000000; inert lookup only.\n"


def probe(package_dir: Path, output: Path, target_tokens: int) -> dict[str, object]:
    sys.path.insert(0, str(package_dir.resolve()))
    from wrench_runtime.server import WrenchHTTPServer
    from wrench_runtime.worker import WrenchWorker
    from wrench_runtime.prefill import _estimate_token_count

    allowed_root = Path.cwd().resolve()
    worker = WrenchWorker.from_pretrained(package_dir, allowed_root=allowed_root, load_model=False)
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        worker,
        model_name="wrench-package",
        max_request_bytes=256 * 1024 * 1024,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # _estimated_tokens adds its final +1 once per message, not once per
    # repeated unit. Reserve the current-intent suffix before selecting the
    # repeated reference units so a nominal 4M probe never exceeds the
    # package's declared logical context limit.
    unit_tokens = max(1, UNIT.count(" ") + UNIT.count("\n"))
    current_intent = "\nCURRENT INTENT: Read src/wrench_harness/worker.py with a 65536 byte limit."
    suffix_tokens = current_intent.count(" ") + current_intent.count("\n")
    repetitions = max(1, (target_tokens - suffix_tokens - 1) // unit_tokens)
    payload_text = UNIT * repetitions + current_intent
    estimated_tokens = _estimate_token_count(payload_text)
    while estimated_tokens > target_tokens and repetitions > 1:
        decrement = max(1, (estimated_tokens - target_tokens + unit_tokens - 1) // unit_tokens)
        repetitions = max(1, repetitions - decrement)
        payload_text = UNIT * repetitions + current_intent
        estimated_tokens = _estimate_token_count(payload_text)
    request_body = json.dumps(
        {
            "model": "wrench-package",
            "messages": [{"role": "user", "content": payload_text}],
            "max_tokens": 64,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    request_started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            status_code = response.status
            body = json.loads(response.read().decode("utf-8"))
        request_elapsed_ms = round((time.perf_counter() - request_started) * 1000, 3)
    finally:
        shutdown_started = time.perf_counter()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        shutdown_elapsed_ms = round((time.perf_counter() - shutdown_started) * 1000, 3)
    choice = body.get("choices", [{}])[0]
    message = choice.get("message", {}) if isinstance(choice, dict) else {}
    content = message.get("content", "") if isinstance(message, dict) else ""
    wrench = body.get("wrench", {})
    result = {
        "schema": "wrench.model-local-server-4m-probe.v1",
        "status": (
            "PASS_MODEL_LOCAL_SERVER_4M"
            if status_code == 200
            and isinstance(content, str)
            and '"action":"read_file"' in content
            and wrench.get("backend") == "embedded-mechanical"
            and wrench.get("model_calls") == 0
            and isinstance(body.get("usage"), dict)
            and body["usage"].get("prompt_tokens", 0) >= target_tokens * 0.95
            else "FAIL_MODEL_LOCAL_SERVER_4M"
        ),
        "package_dir": str(package_dir.resolve()),
        "requested_payload_tokens": target_tokens,
        "raw_payload_chars": len(payload_text),
        "request_bytes": len(request_body),
        "request_sha256": hashlib.sha256(payload_text.encode("utf-8")).hexdigest(),
        "http_status": status_code,
        "elapsed_ms": request_elapsed_ms,
        "shutdown_elapsed_ms": shutdown_elapsed_ms,
        "response_model": body.get("model"),
        "usage": body.get("usage"),
        "wrench": wrench,
        "assistant_content": content,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "elapsed_ms": request_elapsed_ms, "raw_payload_chars": len(payload_text)}))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--target-tokens", type=int, default=4_000_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.package_dir, args.output, args.target_tokens)
    return 0 if result["status"] == "PASS_MODEL_LOCAL_SERVER_4M" else 1


if __name__ == "__main__":
    raise SystemExit(main())
