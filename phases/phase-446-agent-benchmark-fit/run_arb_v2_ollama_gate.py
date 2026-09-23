"""Run a public outside model through the same ARB V2 binary gate adapter locally."""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_arb_v2_abstention_gate import DATA, evaluate, load_cases, sha256_file, write_json
from run_ollama_toolbehonest_baseline import (
    OLLAMA_URL,
    ResourceReserveError,
    enforce_reserve,
    find_model,
    http_json,
    model_is_loaded,
    parse_decision,
    resource_snapshot,
)


OUTPUT_INSTRUCTION = (
    "\n\nReturn exactly one JSON object with a single key named decision. "
    "Use only abstain or not_abstain as its value. Do not include other text."
)
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {"decision": {"type": "string", "enum": ["abstain", "not_abstain"]}},
    "required": ["decision"],
    "additionalProperties": False,
}


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((fraction * len(ordered) + 0.999999999)) - 1))
    return ordered[index]


def paired_comparison(outside: list[dict[str, Any]], wrench_path: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    wrench: dict[str, dict[str, Any]] = {}
    with wrench_path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                row_id = str(row["id"])
                if row_id in wrench:
                    raise ValueError(f"duplicate Wrench ID: {row_id}")
                wrench[row_id] = row
    other = {row["id"]: row for row in outside}
    case_by_id = {case["id"]: case for case in cases}
    if set(other) != set(wrench) or set(other) != set(case_by_id):
        raise ValueError("outside, Wrench, and ARB V2 case IDs are not a one-to-one match")
    rows: list[dict[str, Any]] = []
    for row_id, case in case_by_id.items():
        if other[row_id]["expected"] != case["expected"] or wrench[row_id]["expected"] != case["expected"]:
            raise ValueError(f"gold label mismatch for {row_id}")
        rows.append({
            "id": row_id,
            "repo": case["repo"],
            "expected": case["expected"],
            "outside_correct": other[row_id]["decision"] == case["expected"],
            "wrench_correct": wrench[row_id]["decision"] == case["expected"],
            "outside_decision": other[row_id]["decision"],
            "wrench_decision": wrench[row_id]["decision"],
        })
    repos: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        repos[row["repo"]].append(row)
    if len(repos) != 25:
        raise ValueError(f"expected 25 ARB V2 repositories, found {len(repos)}")

    def selected_rows(sampled_repos: list[str]) -> list[dict[str, Any]]:
        return [row for repo in sampled_repos for row in repos[repo]]

    def delta(sampled_repos: list[str]) -> float:
        selected = selected_rows(sampled_repos)
        return sum(int(row["outside_correct"]) - int(row["wrench_correct"]) for row in selected) / len(selected)

    def balanced_accuracy(selected: list[dict[str, Any]], field: str) -> float:
        positive = [row for row in selected if row["expected"] == "not_abstain"]
        no_gold = [row for row in selected if row["expected"] == "abstain"]
        return (
            sum(row[field] for row in positive) / len(positive)
            + sum(row[field] for row in no_gold) / len(no_gold)
        ) / 2

    keys = sorted(repos)
    rng = random.Random(20260923)
    draws: list[float] = []
    balanced_draws: list[float] = []
    for _ in range(10_000):
        selected = selected_rows([rng.choice(keys) for _ in keys])
        draws.append(sum(int(row["outside_correct"]) - int(row["wrench_correct"]) for row in selected) / len(selected))
        balanced_draws.append(
            balanced_accuracy(selected, "outside_correct") - balanced_accuracy(selected, "wrench_correct")
        )
    draws.sort()
    balanced_draws.sort()
    full = selected_rows(keys)
    outside_balanced = balanced_accuracy(full, "outside_correct")
    wrench_balanced = balanced_accuracy(full, "wrench_correct")
    return {
        "matched_cases": len(rows),
        "repository_clusters": len(repos),
        "outside_minus_wrench_accuracy_delta": sum(int(row["outside_correct"]) - int(row["wrench_correct"]) for row in rows) / len(rows),
        "paired_repository_cluster_bootstrap_95_ci": [draws[249], draws[9749]],
        "outside_balanced_accuracy_positive_vs_all_no_gold": outside_balanced,
        "wrench_balanced_accuracy_positive_vs_all_no_gold": wrench_balanced,
        "outside_minus_wrench_balanced_accuracy_delta": outside_balanced - wrench_balanced,
        "paired_repository_cluster_bootstrap_95_ci_balanced_accuracy_delta": [balanced_draws[249], balanced_draws[9749]],
        "outside_only_correct": sum(row["outside_correct"] and not row["wrench_correct"] for row in rows),
        "wrench_only_correct": sum(row["wrench_correct"] and not row["outside_correct"] for row in rows),
        "exact_decision_agreement": sum(row["outside_decision"] == row["wrench_decision"] for row in rows) / len(rows),
        "bootstrap": {"method": "paired repository-cluster bootstrap", "seed": 20260923, "resamples": len(draws)},
        "wrench_predictions_sha256": sha256_file(wrench_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Already-installed local Ollama model name")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--wrench-predictions", type=Path, required=True)
    parser.add_argument("--wrench-input-limits", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--check-every", type=int, default=10)
    parser.add_argument("--num-ctx", type=int, default=8192)
    args = parser.parse_args()
    if args.check_every < 1 or args.num_ctx < 1024:
        parser.error("--check-every must be positive and --num-ctx at least 1024")
    data_path = args.data.resolve()
    wrench_path = args.wrench_predictions.resolve()
    limits_path = args.wrench_input_limits.resolve()
    output_dir = args.output_dir.resolve()
    if not data_path.is_file() or not wrench_path.is_file() or not limits_path.is_file():
        parser.error("ARB data, Wrench predictions, and Wrench input-limit audit must exist")
    if output_dir.exists():
        parser.error(f"refusing to overwrite output directory: {output_dir}")
    cases = load_cases(data_path)
    limit_rows = [json.loads(line) for line in limits_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    limits = {str(row["id"]): row for row in limit_rows}
    if len(limits) != len(limit_rows) or set(limits) != {case["id"] for case in cases}:
        raise ValueError("exact Wrench input-limit audit does not match the ARB V2 case IDs")
    model_info = find_model(args.model)
    loaded_before = model_is_loaded(args.model)
    initial = resource_snapshot()
    enforce_reserve(initial)
    output_dir.mkdir(parents=True)
    run: dict[str, Any] = {
        "schema": "wrench.arb-v2-adapted-outside-binary-gate.v1",
        "benchmark": "Agent Retrieval Bench V2 selective natural split, binary gate component adapter",
        "status": "RUNNING",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "model_name": args.model,
        "model_digest": model_info.get("digest"),
        "model_details": model_info.get("details"),
        "model_size_bytes": model_info.get("size"),
        "model_loaded_before_run": loaded_before,
        "dataset_sha256": sha256_file(data_path),
        "wrench_predictions_sha256": sha256_file(wrench_path),
        "wrench_input_limit_audit_sha256": sha256_file(limits_path),
        "wrench_input_limit_policy": {
            "max_chars": 8192,
            "max_tokens": 512,
            "over_limit_cases_skipped": sum(row["limit_reason"] != "within_limits" for row in limit_rows),
            "under_limit_model_calls_expected": sum(row["limit_reason"] == "within_limits" for row in limit_rows),
        },
        "prompt_adapter": "same-base-arb-v2-binary-gate-prompt-plus-strict-json-output-v1",
        "decoding": {"temperature": 0, "seed": 0, "top_k": 1, "num_ctx": args.num_ctx, "num_predict": 32, "think": False},
        "endpoint": OLLAMA_URL,
        "provider_calls": 0,
        "external_api_calls": 0,
        "local_inference_calls": 0,
        "cost": 0,
        "tool_execution": False,
        "training_or_tuning": False,
        "metric_scope": "adapted binary gate comparison only; not official ARB ranking or task-success metrics",
        "protocol_note": "Same 427 case IDs, gold labels, repository names, official query text, and base system prompt as Wrench. Outside model receives only a strict JSON output-format instruction. No gold labels or metadata are sent to the model.",
        "resources": [initial],
    }
    write_json(output_dir / "run.json", run)
    rows: list[dict[str, Any]] = []
    predictions_path = output_dir / "predictions.jsonl"
    try:
        with predictions_path.open("x", encoding="utf-8", newline="\n") as predictions:
            for index, case in enumerate(cases, 1):
                if (index - 1) % args.check_every == 0:
                    sample = resource_snapshot()
                    enforce_reserve(sample)
                    run["resources"].append(sample)
                limit = limits[case["id"]]
                if limit["limit_reason"] != "within_limits":
                    response, content, decision, reason, latency_ms = {}, "", "abstain", "input_too_long", 0.0
                else:
                    messages = [{"role": message["role"], "content": message["content"]} for message in case["messages"]]
                    messages[0]["content"] += OUTPUT_INSTRUCTION
                    request = {
                        "model": args.model,
                        "messages": messages,
                        "stream": False,
                        "think": False,
                        "format": OUTPUT_SCHEMA,
                        "options": {"temperature": 0, "seed": 0, "top_k": 1, "num_ctx": args.num_ctx, "num_predict": 32},
                    }
                    started = time.perf_counter()
                    response = http_json("/api/chat", request)
                    latency_ms = (time.perf_counter() - started) * 1000
                    message = response.get("message")
                    content = message.get("content", "") if isinstance(message, dict) else ""
                    decision, reason = parse_decision(content if isinstance(content, str) else "")
                row = {
                    "id": case["id"],
                    "repo": case["repo"],
                    "group": case["group"],
                    "expected": case["expected"],
                    "input_chars": limit["input_chars"],
                    "input_tokens": limit["input_tokens"],
                    "limit_reason": limit["limit_reason"],
                    "decision": decision,
                    "reason": reason,
                    "raw_response": content,
                    "prompt_eval_count": response.get("prompt_eval_count"),
                    "eval_count": response.get("eval_count"),
                    "latency_ms": latency_ms,
                }
                predictions.write(json.dumps(row, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
                predictions.flush()
                rows.append(row)
                run["completed_rows"] = index
                run["local_inference_calls"] = sum(item["reason"] != "input_too_long" for item in rows)
                if index % args.check_every == 0:
                    write_json(output_dir / "run.json", run)
        if len(rows) != 427 or len({row["id"] for row in rows}) != 427:
            raise RuntimeError(f"expected 427 unique ARB V2 rows, got {len(rows)}")
        run["metrics"] = evaluate(rows)
        latencies = [row["latency_ms"] for row in rows]
        run["latency"] = {
            "first_request_ms": latencies[0] if latencies else None,
            "all_p50_ms": statistics.median(latencies) if latencies else None,
            "all_p95_ms": percentile(latencies, 0.95),
            "steady_state_p50_ms": statistics.median(latencies[1:]) if len(latencies) > 1 else None,
            "steady_state_p95_ms": percentile(latencies[1:], 0.95),
        }
        run["paired_wrench_comparison"] = paired_comparison(rows, wrench_path, cases)
        run["predictions_sha256"] = sha256_file(predictions_path)
        run["status"] = "COMPLETE"
        run["completed_utc"] = datetime.now(timezone.utc).isoformat()
        final = resource_snapshot()
        enforce_reserve(final)
        run["resources"].append(final)
        write_json(output_dir / "run.json", run)
        write_json(output_dir / "summary.json", run)
        print(json.dumps({"status": run["status"], "metrics": run["metrics"], "paired_wrench_comparison": run["paired_wrench_comparison"], "summary": str(output_dir / "summary.json")}, allow_nan=False))
        return 0
    except ResourceReserveError as exc:
        run["status"] = "RESOURCE_UNSAFE_STOP"
        run["error"] = str(exc)
        run["completed_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(output_dir / "run.json", run)
        print(json.dumps({"status": run["status"], "error": str(exc), "completed_rows": run.get("completed_rows", 0)}), file=sys.stderr)
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
