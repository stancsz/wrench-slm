#!/usr/bin/env python3
"""Verify all portable client launchers traverse a bounded local upstream.

This is a protocol and wiring probe. The upstream is a deterministic local
stub, so the receipt must not be read as model-quality or paid-provider proof.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _summarize_upstream_request(
    headers: object,
    payload: dict[str, object],
    tool_result: str | None,
    timestamp_unix: float | None = None,
) -> dict[str, object]:
    """Retain local-stub request identity without storing prompt contents."""

    header_map = headers if hasattr(headers, "get") else {}
    messages = payload.get("messages")
    roles = [
        message.get("role")
        for message in messages
        if isinstance(message, dict) and isinstance(message.get("role"), str)
    ] if isinstance(messages, list) else []
    message_shapes = []
    if isinstance(messages, list):
        for message in messages:
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            content_bytes = json.dumps(
                content, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
            message_shapes.append(
                {
                    "role": message.get("role"),
                    "content_bytes": len(content_bytes),
                    "content_sha256": hashlib.sha256(content_bytes).hexdigest(),
                }
            )
    tool_definitions = payload.get("tools")
    tool_definitions_bytes = json.dumps(
        tool_definitions, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    canonical_payload = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return {
        "request_index": None,
        "timestamp_unix": timestamp_unix,
        "user_agent": str(header_map.get("User-Agent", ""))[:200],
        "model": payload.get("model"),
        "stream": bool(payload.get("stream")),
        "message_roles": roles,
        "message_shapes": message_shapes,
        "tool_definitions_present": isinstance(tool_definitions, list),
        "tool_definition_count": (
            len(tool_definitions) if isinstance(tool_definitions, list) else 0
        ),
        "tool_definitions_sha256": (
            hashlib.sha256(tool_definitions_bytes).hexdigest()
            if isinstance(tool_definitions, list)
            else None
        ),
        "tool_result_present": tool_result is not None,
        "tool_result_sha256": (
            hashlib.sha256(tool_result.encode("utf-8")).hexdigest()
            if tool_result is not None
            else None
        ),
        "request_payload_sha256": hashlib.sha256(canonical_payload).hexdigest(),
    }


def _client_for_timestamp(
    timestamp_unix: object,
    windows: dict[str, tuple[float, float]],
) -> str | None:
    """Return a client only when exactly one recorded invocation contains the request."""

    if not isinstance(timestamp_unix, (int, float)):
        return None
    matches = [
        client
        for client, (started, finished) in windows.items()
        if started <= timestamp_unix <= finished
    ]
    return matches[0] if len(matches) == 1 else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--port", type=int, default=28980)
    parser.add_argument("--client-port", type=int, default=28981)
    parser.add_argument("--claude-port", type=int, default=28982)
    parser.add_argument("--claude-proxy-port", type=int, default=28983)
    parser.add_argument("--opencode-executable", type=Path)
    parser.add_argument("--dsh-executable", type=Path)
    args = parser.parse_args()

    package_dir = args.package_dir.resolve()
    opencode_executable = None
    if args.opencode_executable is not None:
        opencode_executable = args.opencode_executable.resolve()
        if not opencode_executable.is_file():
            parser.error("--opencode-executable must name an existing executable")
    dsh_executable = None
    if args.dsh_executable is not None:
        dsh_executable = args.dsh_executable.resolve()
        if not dsh_executable.is_file():
            parser.error("--dsh-executable must name an existing launcher")
    calls: list[dict[str, object]] = []

    def bounded_tool_result(messages: object) -> str | None:
        if not isinstance(messages, list):
            return None
        for message in reversed(messages):
            if not isinstance(message, dict):
                continue
            if message.get("role") != "tool":
                continue
            content = message.get("content")
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                parts = [
                    block.get("text")
                    for block in content
                    if isinstance(block, dict) and isinstance(block.get("text"), str)
                ]
                text = "\n".join(parts)
            else:
                text = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
            bounded = text[:16_384] or "(client tool returned no displayable content)"
            if len(text) > len(bounded):
                bounded += "\n[tool result truncated by Wrench]"
            return bounded
        return None

    class UpstreamHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            tool_result = bounded_tool_result(payload.get("messages"))
            summary = _summarize_upstream_request(
                self.headers, payload, tool_result, timestamp_unix=time.time()
            )
            summary["request_index"] = len(calls) + 1
            calls.append(summary)
            if tool_result is not None:
                proposal = json.dumps(
                    {
                        "schema": "wrench.final-answer.v1",
                        "answer": "Read-only result received and verified.",
                        "tool_result_sha256": hashlib.sha256(tool_result.encode("utf-8")).hexdigest(),
                    }
                )
            else:
                proposal = json.dumps(
                    {
                        "schema": "wrench.proposal.v1",
                        "action": "read_lines",
                        "path": "README.md",
                        "start": 1,
                        "end": 1,
                    }
                )
            body = json.dumps(
                {
                    "choices": [{"message": {"role": "assistant", "content": proposal}}],
                    "usage": {"prompt_tokens": 100, "completion_tokens": 8, "total_tokens": 108},
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
    thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    output_dir = args.output.resolve().parent / (args.output.stem + "-client-output")
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if powershell is None:
        raise RuntimeError("powershell.exe is required for the portable client probe")
    command = [
        powershell,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(REPO_ROOT / "tools" / "smoke_portable_clients.ps1"),
        "-PackageDir",
        str(package_dir),
        "-AllowedRoot",
        str(REPO_ROOT),
        "-OutputDir",
        str(output_dir),
        "-Port",
        str(args.client_port),
        "-ClaudePort",
        str(args.claude_port),
        "-ClaudeProxyPort",
        str(args.claude_proxy_port),
        "-Prompt",
        "Review README.md and return a bounded proposal.",
        "-UpstreamUrl",
        f"http://127.0.0.1:{upstream.server_port}/v1/chat/completions",
        "-DisableMechanicalRoute",
    ]
    if opencode_executable is not None:
        command.extend(["-OpenCodeExecutable", str(opencode_executable)])
    if dsh_executable is not None:
        command.extend(["-DshExecutable", str(dsh_executable)])
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    finally:
        upstream.shutdown()
        upstream.server_close()
        thread.join(timeout=5)

    receipt_path = output_dir / "receipt.json"
    client_receipt = (
        json.loads(receipt_path.read_text(encoding="utf-8-sig"))
        if receipt_path.is_file()
        else {}
    )
    clients = client_receipt.get("clients", {}) if isinstance(client_receipt, dict) else {}
    client_windows: dict[str, tuple[float, float]] = {}
    for name in ("opencode", "deepseek_harness", "claude_code"):
        client = clients.get(name)
        if not isinstance(client, dict):
            continue
        started_ms = client.get("started_at_unix_ms")
        finished_ms = client.get("finished_at_unix_ms")
        if (
            isinstance(started_ms, (int, float))
            and isinstance(finished_ms, (int, float))
            and started_ms <= finished_ms
        ):
            client_windows[name] = (started_ms / 1000, finished_ms / 1000)
    attributed_request_counts = {name: 0 for name in client_windows}
    attributed_tool_result_counts = {name: 0 for name in client_windows}
    unattributed_request_count = 0
    for request in calls:
        client_name = _client_for_timestamp(request.get("timestamp_unix"), client_windows)
        request["client_attribution"] = client_name
        if client_name is None:
            unattributed_request_count += 1
            continue
        attributed_request_counts[client_name] += 1
        if request.get("tool_result_present") is True:
            attributed_tool_result_counts[client_name] += 1
    trace_path = client_receipt.get("trace", {}).get("path") if isinstance(client_receipt, dict) else None
    trace_rows: list[dict[str, object]] = []
    if isinstance(trace_path, str) and Path(trace_path).is_file():
        trace_rows = [
            json.loads(line)
            for line in Path(trace_path).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    accepted_count = sum(1 for row in trace_rows if row.get("status") == "accepted")
    final_answer_count = sum(1 for row in trace_rows if row.get("final_answer") is True)
    abstain_count = sum(1 for row in trace_rows if row.get("status") == "abstain")
    all_clients_passed = all(
        isinstance(clients.get(name), dict)
        and clients[name].get("exit_code") == 0
        and clients[name].get("structured_read_observed") is True
        for name in ("opencode", "deepseek_harness", "claude_code")
    )
    status = (
        "PASS_PORTABLE_CLIENT_UPSTREAM_WIRING"
        if completed.returncode == 0
        and client_receipt.get("status") == "PASSED"
        and client_receipt.get("upstream_enabled") is True
        and client_receipt.get("mechanical_route_enabled") is False
        and len(calls) > 0
        and accepted_count > 0
        and final_answer_count > 0
        and len(trace_rows) <= 20
        and all_clients_passed
        else "FAIL_PORTABLE_CLIENT_UPSTREAM_WIRING"
    )
    receipt = {
        "schema": "wrench.portable-client-upstream-wiring.v1",
        "status": status,
        "package_dir": str(package_dir),
        "upstream_call_count": len(calls),
        "upstream_request_summaries": calls,
        "request_attribution": {
            "method": "request_timestamp_within_smoke_client_invocation_window",
            "client_request_counts": attributed_request_counts,
            "client_tool_result_request_counts": attributed_tool_result_counts,
            "unattributed_request_count": unattributed_request_count,
            "complete": bool(client_windows)
            and unattributed_request_count == 0
            and sum(attributed_request_counts.values()) == len(calls),
        },
        "trace_row_count": len(trace_rows),
        "accepted_trace_count": accepted_count,
        "final_answer_trace_count": final_answer_count,
        "abstain_trace_count": abstain_count,
        "client_receipt": client_receipt,
        "subprocess_returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "quality_claim": False,
        "paid_provider_claim": False,
        "notes": [
            "The upstream is a deterministic local protocol stub.",
            "This verifies launcher wiring and Wrench settlement only.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "upstream_call_count": len(calls)}))
    return 0 if status == "PASS_PORTABLE_CLIENT_UPSTREAM_WIRING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
