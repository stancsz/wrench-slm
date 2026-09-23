"""Run a pinned-client, loopback-only two-state task-marker diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import shutil
import tempfile
import threading
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .probe_paired_real_client_canary import (
        EXPECTED,
        PROMPT,
        _LoopbackAccountingProxy,
        _baseline_server,
        _run_direct_clients,
    )
except ImportError:
    from probe_paired_real_client_canary import (
        EXPECTED,
        PROMPT,
        _LoopbackAccountingProxy,
        _baseline_server,
        _run_direct_clients,
    )


REPO_ROOT = Path(__file__).resolve().parents[1]
PINNED_OPENCODE = REPO_ROOT / "artifacts" / "tools" / "opencode-v1.18.32" / "opencode.exe"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(output_path: Path, *, opencode_executable: str | None = None) -> dict[str, Any]:
    marker = f"wrench-diag-{secrets.token_urlsafe(24)}"
    # Keep the marker on one line because the pinned DSH .cmd wrapper passes
    # positional task text through PowerShell before Node parses argv.
    prompt = f"{PROMPT} Diagnostic reference: {marker}"
    server, upstream_calls = _baseline_server(
        two_state_read_tool=True,
        task_marker=marker,
    )
    proxy = _LoopbackAccountingProxy(
        f"http://127.0.0.1:{server.server_port}/v1",
        task_marker=marker,
    )
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    proxy.start()
    try:
        with tempfile.TemporaryDirectory(prefix="wrench-task-marker-local-") as temp_dir:
            results = _run_direct_clients(
                Path(temp_dir),
                base_url=proxy.base_url,
                model="baseline-local",
                api_key="local-only",
                prompt=prompt,
                expected=EXPECTED,
                opencode_executable=opencode_executable or str(PINNED_OPENCODE),
            )
            capture = proxy.snapshot(results)
        purpose_counts = Counter(call.get("purpose", "unknown") for call in capture["calls"])
        task_requests_with_tools = sum(
            bool(call.get("tools"))
            and any(marker in text for message in call.get("messages", []) for text in _text_values(message))
            and not any(message.get("role") in {"tool", "function"} for message in call.get("messages", []) if isinstance(message, dict))
            for call in upstream_calls
        )
        task_requests_with_result = sum(
            any(message.get("role") in {"tool", "function"} for message in call.get("messages", []) if isinstance(message, dict))
            and any(marker in text for message in call.get("messages", []) for text in _text_values(message))
            for call in upstream_calls
        )
        client_results = {
            name: {
                "exit_code": result.get("exit_code"),
                "correct": result.get("correct") is True,
                "timed_out": result.get("timed_out") is True,
                "elapsed_ms": result.get("elapsed_ms"),
                "started_at_unix_ms": result.get("started_at_unix_ms"),
                "finished_at_unix_ms": result.get("finished_at_unix_ms"),
                "executable_sha256": _sha256(Path(result["executable"]))
                if Path(result.get("executable", "")).is_file() else None,
            }
            for name, result in results.items()
        }
        receipt = {
            "schema": "wrench.pinned-client-task-marker-diagnostic.v1",
            "status": "PASS_LOCAL_TWO_STATE_MARKER_DIAGNOSTIC"
            if all(item["correct"] and not item["timed_out"] for item in client_results.values())
            and task_requests_with_tools == 2
            and task_requests_with_result == 2
            and capture["task_marker_validation"]["exact_two_matches_per_client"]
            and capture["client_attribution_complete"]
            and purpose_counts.get("unknown", 0) == 0
            else "FAIL_LOCAL_TWO_STATE_MARKER_DIAGNOSTIC",
            "authorization": "local_deterministic_stub_only",
            "provider_endpoint_configured": False,
            "provider_spend": False,
            "marker_sha256": capture["task_marker_validation"]["marker_sha256"],
            "client_results": client_results,
            "local_stub_request_count": len(upstream_calls),
            "task_request_with_tool_definitions_count": task_requests_with_tools,
            "task_request_with_tool_result_count": task_requests_with_result,
            "request_purpose_counts": dict(sorted(purpose_counts.items())),
            "client_attribution_complete": capture["client_attribution_complete"],
            "task_marker_validation": capture["task_marker_validation"],
            "call_shapes": [
                {
                    "client": call.get("client_attribution"),
                    "purpose": call.get("purpose"),
                    "purpose_classification_reason": call.get("purpose_classification_reason"),
                    "task_marker_matched": call.get("task_marker_matched"),
                    "message_roles": call.get("request_shape", {}).get("message_roles", []),
                    "tool_definition_count": call.get("request_shape", {}).get("tool_definition_count"),
                    "tool_result_present": call.get("request_shape", {}).get("tool_result_present"),
                    "status": call.get("status"),
                }
                for call in capture["calls"]
            ],
            "limits": [
                "synthetic local model responses only",
                "no teacher quality, provider route, cost, or release-gate claim",
                "temporary workspace and client home are deleted after the run",
            ],
        }
        serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
        if marker in serialized:
            raise RuntimeError("raw_task_marker_would_be_persisted")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return receipt
    finally:
        proxy.stop()
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)


def _text_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _text_values(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _text_values(item)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--opencode-executable")
    args = parser.parse_args()
    if not args.opencode_executable and not PINNED_OPENCODE.is_file():
        parser.error(f"pinned OpenCode executable not found: {PINNED_OPENCODE}")
    dsh = shutil.which("dsh.cmd") or shutil.which("dsh")
    if not dsh:
        parser.error("DeepSeek Harness executable is unavailable")
    receipt = run(args.output.resolve(), opencode_executable=args.opencode_executable)
    print(json.dumps({key: receipt[key] for key in ("status", "marker_sha256", "local_stub_request_count", "request_purpose_counts", "task_marker_validation")}))
    return 0 if receipt["status"] == "PASS_LOCAL_TWO_STATE_MARKER_DIAGNOSTIC" else 1


if __name__ == "__main__":
    raise SystemExit(main())
