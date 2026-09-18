#!/usr/bin/env python3
"""Profile Qwen router activations through the local FreeToken teacher path."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _json_request(url: str, payload: dict[str, Any] | None = None, timeout: float = 10) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _wait_ready(origin: str, process: subprocess.Popen, timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"FreeToken exited during startup with code {process.returncode}")
        try:
            health = _json_request(f"{origin}/health", timeout=5)
            if health.get("maintenance") == "serving":
                return health
        except (OSError, ValueError, urllib.error.URLError):
            pass
        time.sleep(1)
    raise TimeoutError(f"FreeToken was not ready after {timeout:.0f}s")


def _stop(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=False, capture_output=True)
        process.wait(timeout=10)


def _runtime_facts(model_path: Path) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "python": sys.version.split()[0],
    }
    try:
        import torch

        facts["torch"] = torch.__version__
    except Exception:
        pass
    try:
        facts["freetoken"] = importlib.metadata.version("freetoken")
    except importlib.metadata.PackageNotFoundError:
        pass
    metadata_path = model_path / "freetoken_weight.json"
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        facts["teacher_checkpoint_fingerprint"] = metadata.get("fingerprint")
        facts["teacher_quant_format"] = metadata.get("quant_format")
        facts["teacher_total_bytes"] = metadata.get("total_bytes")
    tokenizer = model_path / "tokenizer.json"
    if tokenizer.is_file():
        facts["tokenizer_sha256"] = hashlib.sha256(tokenizer.read_bytes()).hexdigest()
    return facts


def profile(args: argparse.Namespace) -> dict[str, Any]:
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    raw_profile = output.with_name(output.stem + ".raw.json")
    log_path = output.with_suffix(".server.log")
    prompts = [json.loads(line) for line in args.calibration.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit_requests is not None:
        prompts = prompts[:args.limit_requests]
    python_path = Path(args.python).resolve()
    env = os.environ.copy()
    env["WRENCH_ROUTER_PROFILE_PATH"] = str(raw_profile)
    env["WRENCH_FREETOKEN_TCP_ZMQ"] = "1"
    env["WRENCH_ROUTER_PROFILE_NO_JIT"] = "1"
    env["FREETOKEN_FUSED_COPY"] = "0"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(Path(args.hook_dir).resolve()), str(Path(args.freetoken_python).resolve()), env.get("PYTHONPATH", "")]
    )
    command = [
        str(python_path), "-m", "freetoken.cli", "serve",
        "--model", str(Path(args.model).resolve()),
        "--host", args.host, "--port", str(args.port),
        "--moe-strategy", "offload", "--max-running-requests", "1",
        "--max-seq-len-override", "2048", "--memory-ratio", "0.8",
        "--cuda-graph-max-bs", "0", "--text-model-only",
        "--mm-disable", "vision", "audio", "--reasoning-parser", "qwen3",
    ]
    started = time.perf_counter()
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    origin = f"http://{args.host}:{args.port}"
    health = _wait_ready(origin, process, args.startup_timeout)
    model_rows = _json_request(f"{origin}/v1/models")
    model_id = model_rows["data"][0]["id"]
    requests: list[dict[str, Any]] = []
    try:
        for row in prompts:
            request_started = time.perf_counter()
            response = _json_request(
                f"{origin}/v1/chat/completions",
                {
                    "model": model_id,
                    "messages": [{"role": "user", "content": row["prompt"]}],
                    "temperature": 0,
                    "max_tokens": args.max_tokens,
                    "chat_template_kwargs": {"enable_thinking": False},
                },
                timeout=args.request_timeout,
            )
            requests.append(
                {
                    "id": row["id"],
                    "family": row["family"],
                    "prompt": row["prompt"],
                    "response_model": response.get("model"),
                    "usage": response.get("usage"),
                    "wall_seconds": round(time.perf_counter() - request_started, 3),
                }
            )
    finally:
        _stop(process)
    if not raw_profile.is_file():
        raise RuntimeError(f"router hook did not produce profile: {raw_profile}; see {log_path}")
    raw = json.loads(raw_profile.read_text(encoding="utf-8"))
    runtime_facts = _runtime_facts(Path(args.model).resolve())
    layers: dict[str, Any] = {}
    for key, stats in raw.get("layers", {}).items():
        counts = list(stats["expert_activation_counts"])
        total = max(1, int(stats["top_k_assignments"]))
        ranked = sorted(range(len(counts)), key=lambda index: (-counts[index], index))
        layers[key] = {
            **stats,
            "mean_router_entropy": stats["router_entropy_sum"] / max(1, stats["token_count"]),
            "top_experts": [{"expert": index, "activations": counts[index], "fraction": counts[index] / total} for index in ranked[: args.keep]],
        }
    aggregate = [0] * 256
    for stats in layers.values():
        for index, count in enumerate(stats["expert_activation_counts"]):
            if index >= len(aggregate):
                aggregate.extend([0] * (index + 1 - len(aggregate)))
            aggregate[index] += count
    ranked = sorted(range(len(aggregate)), key=lambda index: (-aggregate[index], index))
    receipt = {
        "schema": "wrench.qwen-router-profile.v1",
        "status": "PASS_ROUTER_ACTIVATION_PROFILE",
        "evidence_scope": "real_quantized_teacher_router_gate_hook",
        "teacher_model": model_id,
        "teacher_checkpoint": str(Path(args.model).resolve()),
        **runtime_facts,
        "runtime_python": str(python_path),
        "health": health,
        "calibration_path": str(args.calibration.resolve()),
        "calibration_status": "provisional_pending_human_approval",
        "request_count": len(requests),
        "requests": requests,
        "layers": layers,
        "aggregate_top_experts": [{"expert": index, "activations": aggregate[index]} for index in ranked[: args.keep]],
        "selection_note": "Per-layer rankings are evidence for later selection. The aggregate list is not a final Wrench selection.",
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "quality_claim": False,
    }
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", default=r"C:\Users\stanc\AppData\Local\FreeToken\venv\Scripts\python.exe")
    parser.add_argument("--freetoken-python", default=r"C:\Users\stanc\github\FreeToken\python")
    parser.add_argument("--hook-dir", default=str(Path(__file__).resolve().parent))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=19125)
    parser.add_argument("--keep", type=int, default=8)
    parser.add_argument("--max-tokens", type=int, default=8)
    parser.add_argument("--limit-requests", type=int, default=None)
    parser.add_argument("--startup-timeout", type=float, default=600)
    parser.add_argument("--request-timeout", type=float, default=180)
    args = parser.parse_args()
    receipt = profile(args)
    print(json.dumps({"status": receipt["status"], "requests": receipt["request_count"], "layers": len(receipt["layers"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
