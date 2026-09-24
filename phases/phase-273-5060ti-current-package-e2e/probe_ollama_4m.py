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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target-tokens", type=int, default=4_000_000)
    args = parser.parse_args()

    sys.path.insert(0, str(args.package_dir.resolve()))
    from wrench_runtime.prefill import _estimate_token_count
    from wrench_runtime.server import WrenchHTTPServer
    from wrench_runtime.worker import WrenchWorker

    worker = WrenchWorker.from_pretrained(args.package_dir, allowed_root=Path.cwd(), load_model=False)
    server = WrenchHTTPServer(("127.0.0.1", 0), worker, model_name="wrench-package", max_request_bytes=512 * 1024 * 1024)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    suffix = "\nCURRENT INTENT: Read src/wrench_harness/worker.py with a 65536 byte limit."
    unit_tokens = max(1, UNIT.count(" ") + UNIT.count("\n"))
    suffix_tokens = suffix.count(" ") + suffix.count("\n")
    repetitions = max(1, (args.target_tokens - suffix_tokens - 1) // unit_tokens)
    content = UNIT * repetitions + suffix
    estimated = _estimate_token_count(content)
    while estimated > args.target_tokens and repetitions > 1:
        repetitions -= 1
        content = UNIT * repetitions + suffix
        estimated = _estimate_token_count(content)
    body = json.dumps({"model": "wrench-package", "messages": [{"role": "user", "content": content}], "stream": False, "options": {"num_predict": 64}}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/api/chat", data=body, headers={"Content-Type": "application/json"}, method="POST")
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            status_code = response.status
            result = json.loads(response.read().decode("utf-8"))
        error = None
    except Exception as exc:
        status_code = getattr(exc, "code", None)
        result = {}
        error = str(exc)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)
    message = result.get("message", {}) if isinstance(result, dict) else {}
    output = message.get("content", "") if isinstance(message, dict) else ""
    wrench = result.get("wrench", {}) if isinstance(result, dict) else {}
    status = "PASS_OLLAMA_API_CHAT_4M" if status_code == 200 and '"action":"read_file"' in output and wrench.get("backend") == "embedded-mechanical" and wrench.get("model_calls") == 0 and result.get("prompt_eval_count", 0) >= args.target_tokens * 0.95 else "FAIL_OLLAMA_API_CHAT_4M"
    receipt = {"schema": "wrench.ollama-api-chat-4m-probe.v1", "status": status, "endpoint": f"http://127.0.0.1:{server.server_port}/api/chat", "package_dir": str(args.package_dir.resolve()), "requested_payload_tokens": args.target_tokens, "raw_payload_chars": len(content), "request_bytes": len(body), "request_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(), "http_status": status_code, "elapsed_ms": elapsed_ms, "usage": {"prompt_eval_count": result.get("prompt_eval_count"), "eval_count": result.get("eval_count")}, "wrench": wrench, "assistant_content": output, "error": error}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "http_status": status_code, "elapsed_ms": elapsed_ms, "raw_payload_chars": len(content)}))
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
