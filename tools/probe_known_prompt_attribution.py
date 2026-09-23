"""Verify no-prompt-change purpose attribution through pinned local clients."""

from __future__ import annotations

import argparse
import hashlib
import json
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
        load_workload,
    )
except ImportError:
    from probe_paired_real_client_canary import (
        EXPECTED,
        PROMPT,
        _LoopbackAccountingProxy,
        _baseline_server,
        _run_direct_clients,
        load_workload,
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
    workload = load_workload(None)
    if workload["cases"][0]["prompt"] != PROMPT or workload["cases"][0]["expected_observation"] != EXPECTED:
        raise RuntimeError("default_workload_identity_changed")
    server, upstream_calls = _baseline_server(
        two_state_read_tool=True,
        task_prompt=PROMPT,
    )
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    proxy = _LoopbackAccountingProxy(
        f"http://127.0.0.1:{server.server_port}/v1",
        task_prompt=PROMPT,
    )
    proxy.start()
    try:
        with tempfile.TemporaryDirectory(prefix="wrench-known-prompt-purpose-") as temp_dir:
            results = _run_direct_clients(
                Path(temp_dir),
                base_url=proxy.base_url,
                model="baseline-local",
                api_key="local-only",
                prompt=PROMPT,
                expected=EXPECTED,
                opencode_executable=opencode_executable or str(PINNED_OPENCODE),
            )
            capture = proxy.snapshot(results)

        purpose_counts = Counter(call.get("purpose", "unknown") for call in capture["calls"])
        validation = capture["task_prompt_validation"]
        client_results = {
            name: {
                "exit_code": result.get("exit_code"),
                "correct": result.get("correct") is True,
                "timed_out": result.get("timed_out") is True,
                "elapsed_ms": result.get("elapsed_ms"),
                "executable_sha256": _sha256(Path(result["executable"]))
                if Path(result.get("executable", "")).is_file() else None,
            }
            for name, result in results.items()
        }
        passed = (
            all(item["correct"] and not item["timed_out"] for item in client_results.values())
            and len(upstream_calls) == 6
            and purpose_counts == Counter({"primary_task_workflow": 4, "session_title_auxiliary": 2})
            and capture["client_attribution_complete"]
            and validation["exact_ordered_two_state_protocol_per_client"]
        )
        receipt = {
            "schema": "wrench.known-workload-purpose-diagnostic.v1",
            "status": "PASS_KNOWN_PROMPT_TASK_PURPOSE_LOCAL_DIAGNOSTIC" if passed else "FAIL_KNOWN_PROMPT_TASK_PURPOSE_LOCAL_DIAGNOSTIC",
            "authorization": "local_deterministic_stub_only",
            "workload_id": workload["workload_id"],
            "workload_sha256": workload["workload_sha256"],
            "provider_endpoint_configured": False,
            "provider_spend": False,
            "client_results": client_results,
            "local_stub_request_count": len(upstream_calls),
            "request_purpose_counts": dict(sorted(purpose_counts.items())),
            "client_attribution_complete": capture["client_attribution_complete"],
            "task_prompt_validation": validation,
            "call_shapes": [
                {
                    "client": call.get("client_attribution"),
                    "purpose": call.get("purpose"),
                    "classification_reason": call.get("purpose_classification_reason"),
                    "message_roles": call.get("request_shape", {}).get("message_roles", []),
                    "tool_definition_count": call.get("request_shape", {}).get("tool_definition_count"),
                    "tool_result_present": call.get("request_shape", {}).get("tool_result_present"),
                }
                for call in capture["calls"]
            ],
            "limits": [
                "unchanged single-case workload; deterministic synthetic response only",
                "per-run HMAC key is not persisted",
                "no provider route, paid cost, teacher quality, utility, or release-gate claim",
                "temporary workspace and isolated client homes are deleted after the run",
            ],
        }
        serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
        if PROMPT in serialized or proxy._task_prompt_hmac_key.hex() in serialized:
            raise RuntimeError("raw_prompt_or_hmac_key_would_be_persisted")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return receipt
    finally:
        proxy.stop()
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--opencode-executable")
    args = parser.parse_args()
    if not args.opencode_executable and not PINNED_OPENCODE.is_file():
        parser.error(f"pinned OpenCode executable not found: {PINNED_OPENCODE}")
    if not (shutil.which("dsh.cmd") or shutil.which("dsh")):
        parser.error("DeepSeek Harness executable is unavailable")
    receipt = run(args.output.resolve(), opencode_executable=args.opencode_executable)
    print(json.dumps({
        "status": receipt["status"],
        "workload_sha256": receipt["workload_sha256"],
        "request_purpose_counts": receipt["request_purpose_counts"],
        "task_prompt_validation": receipt["task_prompt_validation"],
    }))
    return 0 if receipt["status"] == "PASS_KNOWN_PROMPT_TASK_PURPOSE_LOCAL_DIAGNOSTIC" else 1


if __name__ == "__main__":
    raise SystemExit(main())
