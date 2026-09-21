#!/usr/bin/env python3
"""Verify the native FreeToken backend for a Wrench ModelOpt package.

This is deliberately separate from the standard Transformers verifier. Wrench's
NVFP4 safetensors are packed for the FreeToken ModelOpt backend and are not
ordinary dense tensors that ``AutoModel.from_pretrained`` can restore.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


RAW_CONTEXT_TOKENS = 4_000_000
MIN_FREE_FRACTION = 0.10


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resource_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {"ram_free_fraction": None, "gpus": []}
    try:
        if os.name == "nt":
            class _MemoryStatusEx(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            memory = _MemoryStatusEx()
            memory.dwLength = ctypes.sizeof(_MemoryStatusEx)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
                raise OSError("GlobalMemoryStatusEx failed")
            total = int(memory.ullTotalPhys)
            available = int(memory.ullAvailPhys)
        else:
            meminfo = {
                line.split(":", 1)[0]: int(line.split()[1]) * 1024
                for line in Path("/proc/meminfo").read_text().splitlines()
                if ":" in line and len(line.split()) >= 2
            }
            total = meminfo["MemTotal"]
            available = meminfo.get("MemAvailable", meminfo["MemFree"])
        snapshot["ram_total_bytes"] = total
        snapshot["ram_free_bytes"] = available
        snapshot["ram_free_fraction"] = round(available / total, 6)
    except Exception as error:
        snapshot["ram_error"] = f"resource_probe_failed:{type(error).__name__}"
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        snapshot["gpu_error"] = "nvidia_smi_unavailable"
        return snapshot
    completed = subprocess.run(
        [
            nvidia_smi,
            "--query-gpu=name,memory.total,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        snapshot["gpu_error"] = completed.stderr.strip()[:300]
        return snapshot
    for line in completed.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 4:
            continue
        total = float(parts[1])
        used = float(parts[2])
        free = float(parts[3])
        snapshot["gpus"].append(
            {
                "name": parts[0],
                "total_mib": total,
                "used_mib": used,
                "free_mib": free,
                "free_fraction": round(free / total, 6) if total else None,
            }
        )
    return snapshot


def _reserve_ok(snapshot: dict[str, Any]) -> bool:
    fractions: list[float] = []
    ram_fraction = snapshot.get("ram_free_fraction")
    if isinstance(ram_fraction, (int, float)):
        fractions.append(float(ram_fraction))
    for gpu in snapshot.get("gpus", []):
        fraction = gpu.get("free_fraction")
        if isinstance(fraction, (int, float)):
            fractions.append(float(fraction))
    return bool(fractions) and min(fractions) >= MIN_FREE_FRACTION


def _post_chat(endpoint: str, prompt: str, timeout: float) -> tuple[int | None, dict[str, Any], str | None]:
    body = json.dumps(
        {
            "model": "wrench-4b-qwen3.6-8e",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2,
            "temperature": 0,
            "stream": False,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw)
            return response.status, parsed if isinstance(parsed, dict) else {}, None
    except urllib.error.HTTPError as error:
        try:
            detail = error.read().decode("utf-8")[:300]
        except Exception:
            detail = str(error)
        return error.code, {}, detail
    except Exception as error:
        return None, {}, str(error)


def _terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=15)
        return
    except subprocess.TimeoutExpired:
        pass
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
    else:
        process.kill()
    process.wait(timeout=15)


def verify(args: argparse.Namespace) -> dict[str, Any]:
    model_dir = args.model_dir.resolve()
    output = args.output.resolve()
    executable = args.freetoken_executable or os.environ.get("FREETOKEN_EXECUTABLE") or "ft"
    package_manifest = model_dir / "wrench-package.json"
    config_path = model_dir / "config.json"
    if not package_manifest.is_file() or not config_path.is_file():
        raise FileNotFoundError(f"missing Wrench package metadata under {model_dir}")
    manifest = json.loads(package_manifest.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    before = _resource_snapshot()
    if not _reserve_ok(before):
        raise RuntimeError("BLOCKED_HOST_RESOURCE_RESERVE_BEFORE_START")

    stdout_path = output.with_suffix(".stdout.log")
    stderr_path = output.with_suffix(".stderr.log")
    output.parent.mkdir(parents=True, exist_ok=True)
    stdout_handle = stdout_path.open("w", encoding="utf-8", errors="replace")
    stderr_handle = stderr_path.open("w", encoding="utf-8", errors="replace")
    env = os.environ.copy()
    runtime_dir = model_dir / "wrench_runtime"
    env["PYTHONPATH"] = os.pathsep.join(
        [str(runtime_dir), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    env.update(
        {
            "WRENCH_LONG_CONTEXT_OVERLAY": "1",
            "WRENCH_GLOBAL_FULL_LAYERS": "none",
            "WRENCH_SWA_WINDOW": "8192",
            "WRENCH_SWA_POOL_TOKENS": "8192",
            "WRENCH_ROPE_MAX_POSITION": str(RAW_CONTEXT_TOKENS),
            "WRENCH_NATIVE_DIRECT_INPUT": "1",
            "CUDA_MODULE_LOADING": "LAZY",
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
    )
    command = [
        executable,
        "serve",
        "--model",
        str(model_dir),
        "--host",
        "127.0.0.1",
        "--port",
        str(args.port),
        "--served-model-name",
        "wrench-4b-qwen3.6-8e",
        "--moe-strategy",
        "offload",
        "--expert-load",
        "serial",
        "--moe-cache-auto",
        "--kv-reserve-tokens",
        str(args.kv_reserve_tokens),
        "--num-tokens",
        str(RAW_CONTEXT_TOKENS),
        "--max-seq-len-override",
        str(RAW_CONTEXT_TOKENS),
        "--max-prefill-length",
        "32768",
        "--max-running-requests",
        "1",
        "--num-tokenizer",
        "0",
        "--memory-ratio",
        "0.90",
        "--text-model-only",
        "--cache-type",
        "radix",
        "--tool-call-parser",
        "qwen",
        "--reasoning-parser",
        "off",
    ]
    started = time.perf_counter()
    process: subprocess.Popen[str] | None = None
    status_code: int | None = None
    response: dict[str, Any] = {}
    error: str | None = None
    try:
        process = subprocess.Popen(
            command,
            cwd=str(model_dir),
            env=env,
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
        )
        deadline = time.monotonic() + args.startup_timeout_seconds
        while time.monotonic() < deadline:
            if process.poll() is not None:
                error = f"backend exited with code {process.returncode}"
                break
            status_code, response, error = _post_chat(
                f"http://127.0.0.1:{args.port}/v1/chat/completions",
                "Return exactly OK.",
                timeout=3,
            )
            if status_code == 200:
                break
            time.sleep(1)
        if status_code != 200 and error is None:
            error = "startup timeout"
    finally:
        after_ready = _resource_snapshot()
        if process is not None:
            _terminate_process(process)
        stdout_handle.close()
        stderr_handle.close()
    after_stop = _resource_snapshot()
    combined_log = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in (stdout_path, stderr_path)
        if path.is_file()
    )
    native_capacity = (
        f"Allocating {RAW_CONTEXT_TOKENS} tokens for KV cache" in combined_log
        or f"max_seq_len_override={RAW_CONTEXT_TOKENS}" in combined_log
    )
    response_choices = response.get("choices")
    generated_text = ""
    if isinstance(response_choices, list) and response_choices:
        choice = response_choices[0]
        if isinstance(choice, dict):
            message = choice.get("message")
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                generated_text = message["content"]
    generation_ok = status_code == 200 and isinstance(response_choices, list) and bool(response_choices)
    reserves = [before, after_ready, after_stop]
    reserve_maintained = all(_reserve_ok(item) for item in reserves)
    receipt: dict[str, Any] = {
        "schema": "wrench.freetoken-native-backend-receipt.v1",
        "status": (
            "PASS_FREETOKEN_MODEL_LOAD_AND_GENERATION"
            if generation_ok and native_capacity and reserve_maintained
            else "FAIL_FREETOKEN_NATIVE_BACKEND"
        ),
        "model_dir": str(model_dir),
        "package_manifest_sha256": _sha256(package_manifest),
        "candidate_identity": manifest.get("candidate_identity"),
        "model_architectures": config.get("architectures"),
        "backend": "freetoken_modelopt_nvfp4",
        "direct_model_endpoint": True,
        "declared_raw_context_tokens": RAW_CONTEXT_TOKENS,
        "native_context_capacity_configured": native_capacity,
        "full_weight_load_verified": status_code == 200 and native_capacity,
        "native_generation_verified": generation_ok,
        "dense_native_quality_verified": False,
        "http_status": status_code,
        "generated_text": generated_text,
        "error": error,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        "resource_reserve_maintained": reserve_maintained,
        "resource_snapshots": {"before": before, "after_ready": after_ready, "after_stop": after_stop},
        "command": command,
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "quality_claim": False,
        "notes": [
            "This proves the ModelOpt/NVFP4 FreeToken backend path, not ordinary Transformers tensor loading.",
            "The 4M capacity is configured in the model backend; this receipt does not claim a 4M quality pass.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "http_status", "elapsed_ms", "native_context_capacity_configured", "resource_reserve_maintained")}, ensure_ascii=False))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--freetoken-executable")
    parser.add_argument("--port", type=int, default=28982)
    parser.add_argument("--startup-timeout-seconds", type=float, default=300)
    parser.add_argument("--kv-reserve-tokens", type=int, default=8192)
    args = parser.parse_args()
    receipt = verify(args)
    return 0 if receipt["status"] == "PASS_FREETOKEN_MODEL_LOAD_AND_GENERATION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
