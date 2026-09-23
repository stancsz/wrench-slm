"""Run a local outside-model baseline on the frozen ToolBeHonest adapter.

This is an adapted solvability-decision comparison, not the official
ToolBeHonest leaderboard protocol. It uses the exact same generated case
messages and gold labels as run_qwen_gate_suite.py, then adds only a strict
binary response-format instruction for the generative baseline.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import random
import subprocess
import math
import os
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_qwen_gate_suite import metrics, sha256_file, toolbehonest_cases, write_json


PHASE = Path(__file__).resolve().parent
DEFAULT_DATA = PHASE / "external" / "toolbehonest" / "data" / "test_en.json"
DEFAULT_OUTPUT = PHASE / "external" / "toolbehonest" / "runs" / "qwen35-0.8b-ollama-v2"
OLLAMA_URL = "http://127.0.0.1:11434"
OUTPUT_INSTRUCTION = (
    "\n\nReturn exactly one JSON object with a single key named decision. "
    "Its value must be abstain when the available tools cannot complete the task, "
    "or not_abstain when they can. Do not include any other text."
)
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {"decision": {"type": "string", "enum": ["abstain", "not_abstain"]}},
    "required": ["decision"],
    "additionalProperties": False,
}


class ResourceReserveError(RuntimeError):
    pass


def digest_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def gpu_memory() -> dict[str, int] | None:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    try:
        total, used, free = (int(part.strip()) for part in result.stdout.splitlines()[0].split(","))
    except (IndexError, ValueError):
        return None
    return {"total_mib": total, "used_mib": used, "free_mib": free}


def resource_snapshot() -> dict[str, Any]:
    try:
        import psutil

        total_bytes = int(psutil.virtual_memory().total)
        available_bytes = int(psutil.virtual_memory().available)
    except ImportError:
        if os.name == "nt":
            class MemoryStatusEx(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatusEx()
            status.dwLength = ctypes.sizeof(status)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                raise OSError("GlobalMemoryStatusEx failed")
            total_bytes = int(status.ullTotalPhys)
            available_bytes = int(status.ullAvailPhys)
        else:
            page_size = int(os.sysconf("SC_PAGE_SIZE"))
            total_bytes = int(os.sysconf("SC_PHYS_PAGES")) * page_size
            available_bytes = int(os.sysconf("SC_AVPHYS_PAGES")) * page_size
    return {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "ram_total_bytes": total_bytes,
        "ram_available_bytes": available_bytes,
        "gpu": gpu_memory(),
    }


def enforce_reserve(sample: dict[str, Any]) -> None:
    if sample["ram_available_bytes"] < sample["ram_total_bytes"] * 0.10:
        raise ResourceReserveError("RAM free reserve fell below 10 percent")
    gpu = sample["gpu"]
    if gpu and gpu["free_mib"] < gpu["total_mib"] * 0.10:
        raise ResourceReserveError("VRAM free reserve fell below 10 percent")


def http_json(path: str, payload: dict[str, Any] | None = None, timeout: float = 180.0) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_URL + path,
        data=body,
        headers={"Content-Type": "application/json"} if body is not None else {},
        method="GET" if body is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            decoded = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"local Ollama request failed: {exc}") from exc
    if not isinstance(decoded, dict):
        raise RuntimeError("local Ollama returned a non-object JSON response")
    return decoded


def find_model(model_name: str) -> dict[str, Any]:
    tags = http_json("/api/tags")
    models = tags.get("models")
    if not isinstance(models, list):
        raise RuntimeError("Ollama /api/tags response has no model list")
    matches = [item for item in models if isinstance(item, dict) and item.get("name") == model_name]
    if len(matches) != 1:
        raise RuntimeError(f"expected one local Ollama model named {model_name}, found {len(matches)}")
    return matches[0]


def model_is_loaded(model_name: str) -> bool:
    loaded = http_json("/api/ps").get("models")
    if not isinstance(loaded, list):
        return False
    return any(isinstance(item, dict) and item.get("name") == model_name for item in loaded)


def make_messages(case: dict[str, Any]) -> list[dict[str, str]]:
    messages = [{"role": message["role"], "content": message["content"]} for message in case["messages"]]
    system_index = next((index for index, message in enumerate(messages) if message["role"] == "system"), None)
    if system_index is None:
        messages.insert(0, {"role": "system", "content": OUTPUT_INSTRUCTION.strip()})
    else:
        messages[system_index]["content"] += OUTPUT_INSTRUCTION
    return messages


def parse_decision(content: str) -> tuple[str, str | None]:
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return "abstain", "malformed_json_fail_closed"
    if not isinstance(value, dict) or set(value) != {"decision"}:
        return "abstain", "invalid_decision_schema_fail_closed"
    decision = value.get("decision")
    if decision not in {"abstain", "not_abstain"}:
        return "abstain", "invalid_decision_schema_fail_closed"
    return decision, None


def paired_comparison(ours_path: Path, baseline_rows: list[dict[str, Any]]) -> dict[str, Any]:
    wrench_rows: dict[str, dict[str, Any]] = {}
    with ours_path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                raise ValueError(f"invalid Wrench prediction at line {line_number}")
            if row["id"] in wrench_rows:
                raise ValueError(f"duplicate Wrench prediction id: {row['id']}")
            wrench_rows[row["id"]] = row
    outside_rows = {row["id"]: row for row in baseline_rows}
    if set(wrench_rows) != set(outside_rows):
        raise ValueError(
            f"case ID mismatch: Wrench={len(wrench_rows)}, outside={len(outside_rows)}, "
            f"shared={len(set(wrench_rows) & set(outside_rows))}"
        )
    paired: list[dict[str, Any]] = []
    for case_id in sorted(outside_rows):
        wrench = wrench_rows[case_id]
        outside = outside_rows[case_id]
        if wrench.get("expected_binary") != outside.get("expected_binary"):
            raise ValueError(f"gold label mismatch for {case_id}")
        gold = outside["expected_binary"]
        paired.append({
            "id": case_id,
            "cluster": case_id.rsplit(":", 1)[0],
            "gold": gold,
            "wrench_decision": wrench.get("decision", "abstain"),
            "outside_decision": outside["decision"],
            "wrench_correct": wrench.get("decision", "abstain") == gold,
            "outside_correct": outside["decision"] == gold,
            "exact_agreement": wrench.get("decision", "abstain") == outside["decision"],
        })
    clusters: dict[str, list[dict[str, Any]]] = {}
    for row in paired:
        clusters.setdefault(row["cluster"], []).append(row)
    if len(clusters) != 350:
        raise ValueError(f"expected 350 paired source-record clusters, found {len(clusters)}")

    def delta(sample: list[str]) -> float:
        selected = [row for cluster in sample for row in clusters[cluster]]
        return sum(row["outside_correct"] - row["wrench_correct"] for row in selected) / len(selected)

    keys = sorted(clusters)
    random_source = random.Random(20260922)
    draws = [delta([random_source.choice(keys) for _ in keys]) for _ in range(10_000)]
    draws.sort()
    index_low = max(0, min(len(draws) - 1, int(0.025 * len(draws))))
    index_high = max(0, min(len(draws) - 1, int(0.975 * len(draws)) - 1))
    count = len(paired)
    return {
        "cases": count,
        "source_record_clusters": len(clusters),
        "wrench_accuracy": sum(row["wrench_correct"] for row in paired) / count,
        "outside_model_accuracy": sum(row["outside_correct"] for row in paired) / count,
        "outside_minus_wrench_accuracy_delta": sum(row["outside_correct"] - row["wrench_correct"] for row in paired) / count,
        "paired_cluster_bootstrap_95_ci_for_outside_minus_wrench_accuracy_delta": [draws[index_low], draws[index_high]],
        "exact_decision_agreement": sum(row["exact_agreement"] for row in paired) / count,
        "wrench_only_correct": sum(row["wrench_correct"] and not row["outside_correct"] for row in paired),
        "outside_only_correct": sum(row["outside_correct"] and not row["wrench_correct"] for row in paired),
        "bootstrap": {"method": "paired source-record cluster bootstrap", "seed": 20260922, "resamples": len(draws)},
        "wrench_predictions_sha256": sha256_file(ours_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen3.5:0.8b")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check-every", type=int, default=10)
    parser.add_argument("--num-ctx", type=int, default=16384)
    parser.add_argument("--num-gpu", type=int, help="Ollama GPU layers; set to preserve the host VRAM reserve on large local models")
    parser.add_argument(
        "--wrench-predictions",
        type=Path,
        default=PHASE / "external" / "toolbehonest" / "runs" / "wrench-qwen-head-v1" / "predictions.jsonl",
    )
    args = parser.parse_args()
    if args.check_every < 1 or args.num_ctx < 1024:
        parser.error("--check-every must be positive and --num-ctx must be at least 1024")
    data_path = args.data.resolve()
    output_dir = args.output_dir.resolve()
    if not data_path.is_file():
        parser.error(f"ToolBeHonest data does not exist: {data_path}")
    wrench_predictions = args.wrench_predictions.resolve()
    if not wrench_predictions.is_file():
        parser.error(f"Wrench paired predictions do not exist: {wrench_predictions}")
    if output_dir.exists():
        parser.error(f"refusing to overwrite existing output directory: {output_dir}")
    sample = resource_snapshot()
    enforce_reserve(sample)
    model_info = find_model(args.model)
    was_loaded = model_is_loaded(args.model)
    output_dir.mkdir(parents=True)
    run: dict[str, Any] = {
        "schema": "wrench.external-model-adapted-baseline.v1",
        "benchmark": "ToolBeHonest Level-1 solvability decision",
        "status": "RUNNING",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "model_name": args.model,
        "model_digest": model_info.get("digest"),
        "model_details": model_info.get("details"),
        "model_size_bytes": model_info.get("size"),
        "model_loaded_before_run": was_loaded,
        "data_path": str(data_path),
        "data_sha256": sha256_file(data_path),
        "prompt_adapter": "toolbehonest-task-tools-binary-v1-plus-json-response-v1",
        "prompt_adapter_sha256": digest_json({"base": "toolbehonest-task-tools-binary-v1", "output_instruction": OUTPUT_INSTRUCTION, "schema": OUTPUT_SCHEMA}),
        "decoding": {"temperature": 0, "seed": 0, "top_k": 1, "num_ctx": args.num_ctx, "num_predict": 32, "think": False},
        "num_gpu_layers": args.num_gpu,
        "endpoint": OLLAMA_URL,
        "provider_calls": 0,
        "external_api_calls": 0,
        "local_inference_calls": 0,
        "cost": 0,
        "tool_execution": False,
        "training_or_tuning": False,
        "protocol_note": "Adapted generative binary solvability decision. Wrench and outside-model inputs share the frozen case text and labels; Wrench's learned binary head and this model's JSON completion are different response mechanisms. Not an official ToolBeHonest score.",
        "resources": [sample],
    }
    write_json(output_dir / "run.json", run)

    rows: list[dict[str, Any]] = []
    predictions_path = output_dir / "predictions.jsonl"
    try:
        with predictions_path.open("x", encoding="utf-8", newline="\n") as predictions:
            for index, case in enumerate(toolbehonest_cases(data_path), 1):
                if (index - 1) % args.check_every == 0:
                    sample = resource_snapshot()
                    enforce_reserve(sample)
                    run["resources"].append(sample)
                request = {
                    "model": args.model,
                    "messages": make_messages(case),
                    "stream": False,
                    "think": False,
                    "format": OUTPUT_SCHEMA,
                    "options": {"temperature": 0, "seed": 0, "top_k": 1, "num_ctx": args.num_ctx, "num_predict": 32},
                }
                if args.num_gpu is not None:
                    request["options"]["num_gpu"] = args.num_gpu
                started = time.perf_counter()
                response = http_json("/api/chat", request)
                latency_ms = (time.perf_counter() - started) * 1000
                message = response.get("message")
                content = message.get("content", "") if isinstance(message, dict) else ""
                decision, reason = parse_decision(content if isinstance(content, str) else "")
                record = {
                    "id": str(case["id"]),
                    "group": str(case["group"]),
                    "variant": case["variant"],
                    "benchmark_gold": case["benchmark_gold"],
                    "expected_binary": case["expected_binary"],
                    "decision": decision,
                    "reason": reason,
                    "raw_response": content,
                    "response_chars": len(content),
                    "thinking_chars_discarded": len(message.get("thinking", "")) if isinstance(message, dict) and isinstance(message.get("thinking"), str) else 0,
                    "input_chars": sum(len(item["content"]) for item in case["messages"]),
                    "latency_ms": latency_ms,
                    "prompt_eval_count": response.get("prompt_eval_count"),
                    "eval_count": response.get("eval_count"),
                    "eval_duration_ns": response.get("eval_duration"),
                }
                predictions.write(json.dumps(record, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
                predictions.flush()
                rows.append(record)
                run["completed_rows"] = index
                run["local_inference_calls"] = index
                if index % args.check_every == 0:
                    write_json(output_dir / "run.json", run)

        expected = 700
        if len(rows) != expected or len({row["id"] for row in rows}) != expected:
            raise RuntimeError(f"expected {expected} unique paired variants, got {len(rows)}")
        run["metrics"] = metrics(rows)
        run["wrench_paired_comparison"] = paired_comparison(wrench_predictions, rows)
        latency_values = [row["latency_ms"] for row in rows]
        warm_latency_values = latency_values[1:]
        run["outside_model_latency"] = {
            "first_request_in_run_ms": latency_values[0] if latency_values else None,
            "all_requests_p50_ms": statistics.median(latency_values) if latency_values else None,
            "all_requests_p95_ms": percentile(latency_values, 0.95),
            "steady_state_p50_ms_excluding_first_request": statistics.median(warm_latency_values) if warm_latency_values else None,
            "steady_state_p95_ms_excluding_first_request": percentile(warm_latency_values, 0.95),
        }
        run["predictions_sha256"] = sha256_file(predictions_path)
        run["status"] = "COMPLETE"
        run["completed_utc"] = datetime.now(timezone.utc).isoformat()
        sample = resource_snapshot()
        enforce_reserve(sample)
        run["resources"].append(sample)
        write_json(output_dir / "run.json", run)
        write_json(output_dir / "summary.json", run)
        print(json.dumps({"status": run["status"], "rows": len(rows), "metrics": run["metrics"], "summary": str(output_dir / "summary.json")}, ensure_ascii=False))
        return 0
    except ResourceReserveError as exc:
        run["status"] = "RESOURCE_UNSAFE_STOP"
        run["error"] = str(exc)
        run["completed_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(output_dir / "run.json", run)
        print(json.dumps({"status": run["status"], "error": str(exc), "completed_rows": run.get("completed_rows", 0)}), flush=True)
        return 2
    except Exception as exc:
        run["status"] = "FAILED"
        run["error_type"] = type(exc).__name__
        run["error"] = str(exc)
        run["completed_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(output_dir / "run.json", run)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
