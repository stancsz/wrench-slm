#!/usr/bin/env python3
"""Verify the downloaded package's Ollama-shaped model-local surface."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

from run_monster_context_shadow import _build_payload, _free_port, _memory_snapshot


def _get_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, payload: dict[str, Any], timeout: float = 30) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def run(args: argparse.Namespace) -> dict[str, Any]:
    package_dir = args.package_dir.resolve()
    server_script = package_dir / "wrench_server.py"
    if not server_script.is_file():
        raise FileNotFoundError(server_script)
    port = args.port or _free_port()
    base = f"http://127.0.0.1:{port}"
    before = _memory_snapshot()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(package_dir) + os.pathsep + env.get("PYTHONPATH", "")
    process = subprocess.Popen(
        [
            sys.executable,
            str(server_script),
            "--model-dir",
            str(package_dir),
            "--port",
            str(port),
            "--mechanical-only",
            "--max-request-bytes",
            str(512 * 1024 * 1024),
        ],
        cwd=str(package_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    response: dict[str, Any] = {}
    try:
        deadline = time.perf_counter() + 15
        while time.perf_counter() < deadline:
            try:
                if _get_json(f"{base}/health").get("status") == "ok":
                    break
            except Exception:
                if process.poll() is not None:
                    raise RuntimeError("package_server_exited_before_readiness")
            time.sleep(0.1)
        else:
            raise RuntimeError("package_server_readiness_timeout")

        version = _get_json(f"{base}/api/version")
        tags = _get_json(f"{base}/api/tags")
        show_status, show = _post_json(f"{base}/api/show", {"name": "wrench-ollama-shadow"})

        small_status, small = _post_json(
            f"{base}/api/chat",
            {
                "model": "wrench-ollama-shadow",
                "messages": [{"role": "user", "content": "Read wrench-package.json with a 4096 byte limit."}],
                "stream": False,
                "options": {"num_ctx": 4_000_000},
            },
        )

        target_tokens = 4_000_000
        content = _build_payload(target_tokens - 4_096)
        started = time.perf_counter()
        monster_status, monster = _post_json(
            f"{base}/api/chat",
            {
                "model": "wrench-ollama-shadow",
                "messages": [
                    {
                        "role": "user",
                        "content": content.rsplit("CURRENT INTENT:", 1)[0]
                        + "CURRENT INTENT: Read wrench-package.json with a 4096 byte limit.",
                    }
                ],
                "stream": False,
                "options": {"num_ctx": 4_000_000},
            },
            timeout=120,
        )
        monster_elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        after = _memory_snapshot()
        response = {
            "version": version,
            "tags": tags,
            "show_status": show_status,
            "show": show,
            "small_status": small_status,
            "small": small,
            "monster_status": monster_status,
            "monster": monster,
            "monster_elapsed_ms": monster_elapsed_ms,
            "monster_raw_chars": len(content),
        }
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    monster_wrench = response.get("monster", {}).get("wrench", {})
    monster_gate = monster_wrench.get("context_gate", {})
    version_pass = response.get("version", {}).get("wrench_api") == "ollama-compatible"
    tags_pass = bool(response.get("tags", {}).get("models"))
    show_pass = response.get("show_status") == 200 and response.get("show", {}).get("details", {}).get("context_length") == 4_000_000
    small_wrench = response.get("small", {}).get("wrench", {})
    small_pass = response.get("small_status") == 200 and small_wrench.get("model_calls") == 0
    monster_pass = (
        response.get("monster_status") == 200
        and monster_wrench.get("status") in {"accepted", "abstain"}
        and monster_wrench.get("mechanical_fast_path") is True
        and monster_wrench.get("model_calls") == 0
        and monster_gate.get("raw_context_limit_tokens") == 4_000_000
        and monster_gate.get("raw_payload_hash_bound") is True
        and monster_gate.get("effective_working_context_tokens", 0) <= 64_000
        and monster_wrench.get("raw_input_tokens_estimate", 0) >= 3_950_000
    )
    receipt: dict[str, Any] = {
        "schema": "wrench.ollama-portable-package-smoke.v1",
        "status": "PASS_OLLAMA_SHAPED_MODEL_LOCAL_4M" if version_pass and tags_pass and show_pass and small_pass and monster_pass else "FAIL_OLLAMA_SHAPED_MODEL_LOCAL_4M",
        "scope": "downloaded package subprocess; model-local Ollama-shaped route; no dense native or production claim",
        "package_dir": str(package_dir),
        "surface": {"version": version_pass, "tags": tags_pass, "show": show_pass, "chat_small": small_pass, "chat_monster": monster_pass},
        "response": response,
        "resource_before": before,
        "resource_after": after,
        "checks": {
            "ollama_compatible_version": version_pass,
            "model_catalog_available": tags_pass,
            "declared_4m_context": show_pass,
            "small_chat_no_model_call": small_pass,
            "monster_chat_accepted_at_endpoint": monster_pass,
            "ram_reserve_before": before.get("ram_reserve_pass") is True,
            "ram_reserve_after": after.get("ram_reserve_pass") is True,
            "vram_reserve_before": before.get("vram_reserve_pass") is True,
            "vram_reserve_after": after.get("vram_reserve_pass") is True,
        },
        "claims_not_authorized": [
            "dense-native 4M attention",
            "learned MiniMax parity",
            "independent RTX 5060 Ti verification",
            "production readiness",
        ],
    }
    receipt["all_checks_pass"] = all(receipt["checks"].values())
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    receipt = run(args)
    print(json.dumps({"status": receipt["status"], "all_checks_pass": receipt["all_checks_pass"], "output": str(args.output.resolve())}))
    return 0 if receipt["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
