"""Run Wrench's frozen binary gate on BFCL V4 non-live irrelevance cases.

This is an abstain/continue component adapter. It does not emit function calls,
invoke benchmark functions, or claim an official BFCL leaderboard score.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from run_qwen_gate_suite import ResourceReserveError, WRENCH_ACTIONS, resource_sample, sha256_file, write_json


PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[1]
UPSTREAM = PHASE / "external" / "bfcl-v4" / "upstream" / "berkeley-function-call-leaderboard"
SOURCE_REVISION = "f7cf7359b7ac615a0b294831c5ba2bc95ee4a000"
DATA_PATH = UPSTREAM / "bfcl_eval" / "data" / "BFCL_v4_irrelevance.json"
EXPECTED_ROWS = 240


def cases(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"BFCL row {line_number} is not an object")
            case_id = row.get("id")
            function_defs = row.get("function")
            question_variants = row.get("question")
            if not isinstance(case_id, str) or not isinstance(function_defs, list):
                raise ValueError(f"invalid BFCL id or function list at row {line_number}")
            if not isinstance(question_variants, list) or not question_variants:
                raise ValueError(f"invalid BFCL question at row {line_number}")
            turns = question_variants[0]
            if not isinstance(turns, list) or not turns:
                raise ValueError(f"invalid BFCL turns at row {line_number}")
            messages: list[dict[str, str]] = [{
                "role": "system",
                "content": (
                    "Decide whether the supplied functions should be called for the user request. "
                    "Treat the listed function schemas as the complete available function set.\n"
                    "<tools>\n"
                    + json.dumps(function_defs, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                    + "\n</tools>"
                ),
            }]
            for turn in turns:
                if not isinstance(turn, dict) or not isinstance(turn.get("role"), str) or not isinstance(turn.get("content"), str):
                    raise ValueError(f"invalid BFCL message at row {line_number}")
                messages.append({"role": turn["role"], "content": turn["content"]})
            names = [
                item.get("name") for item in function_defs
                if isinstance(item, dict) and isinstance(item.get("name"), str)
            ]
            yield {
                "id": case_id,
                "group": "non_live_irrelevance",
                "expected_binary": "abstain",
                "benchmark_gold": "no_function_call",
                "messages": messages,
                "function_names": names,
                "function_count": len(function_defs),
            }


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--head", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resource-check-every", type=int, default=25)
    args = parser.parse_args()
    if args.resource_check_every < 1:
        parser.error("--resource-check-every must be at least 1")
    if not DATA_PATH.is_file() or not args.model_dir.is_dir() or not args.head.is_file():
        parser.error("pinned BFCL data, model directory, and head artifact must exist")
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    run: dict[str, Any] = {
        "schema": "wrench.external-binary-suite-run.v1",
        "suite": "bfcl_v4_irrelevance_non_live",
        "status": "LOADING",
        "source_revision": SOURCE_REVISION,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "data_path": str(DATA_PATH.resolve()),
        "data_sha256": sha256_file(DATA_PATH),
        "head_sha256": sha256_file(args.head.resolve()),
        "model_dir": str(args.model_dir.resolve()),
        "checkpoint_identity": json.loads(args.head.read_text(encoding="utf-8")).get("checkpoint_sha256"),
        "predictions_file": "predictions.jsonl",
        "provider_calls": 0,
        "generated_tokens": 0,
        "tool_execution": False,
        "training_or_tuning": False,
        "quality_claim": False,
        "resources": [],
    }
    write_json(output_dir / "run.json", run)
    try:
        import torch
        import transformers
        from wrench_harness.worker import WrenchWorker

        run["torch_version"] = torch.__version__
        run["transformers_version"] = transformers.__version__
        run["resources"].append(resource_sample(torch))
        worker = WrenchWorker.from_pretrained(
            args.model_dir.resolve(),
            allowed_root=output_dir,
            binary_abstain_artifact=args.head.resolve(),
        )
        if worker.binary_abstain_gate is None:
            raise ValueError("binary abstention head did not load")
        run["head_threshold"] = worker.binary_abstain_gate.threshold
        run["max_input_tokens"] = worker.binary_abstain_gate.max_tokens
        run["max_input_chars"] = worker.binary_abstain_gate.max_chars
        run["prompt_adapter"] = "bfcl-v4-non-live-irrelevance-tools-json-v1"
        run["resources"].append(resource_sample(torch))
        run["status"] = "RUNNING"
        write_json(output_dir / "run.json", run)

        rows: list[dict[str, Any]] = []
        with (output_dir / "predictions.jsonl").open("x", encoding="utf-8") as output:
            for index, case in enumerate(cases(DATA_PATH), 1):
                if (index - 1) % args.resource_check_every == 0:
                    run["resources"].append(resource_sample(torch))
                started = time.perf_counter()
                receipt = worker.classify_abstention(case["messages"])
                latency = (time.perf_counter() - started) * 1000
                result = {
                    "id": case["id"],
                    "group": case["group"],
                    "benchmark_gold": case["benchmark_gold"],
                    "expected_binary": case["expected_binary"],
                    "decision": receipt.get("decision", "abstain"),
                    "reason": receipt.get("reason"),
                    "probabilities": receipt.get("probabilities"),
                    "input_tokens": receipt.get("input_tokens"),
                    "input_chars": sum(len(message["content"]) for message in case["messages"]),
                    "function_count": case["function_count"],
                    "function_names": case["function_names"],
                    "function_names_match_wrench": any(name in WRENCH_ACTIONS for name in case["function_names"]),
                    "latency_ms": latency,
                }
                output.write(json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
                output.flush()
                rows.append(result)
                run["completed_rows"] = index
                if index % args.resource_check_every == 0:
                    write_json(output_dir / "run.json", run)
        if len(rows) != EXPECTED_ROWS or len({row["id"] for row in rows}) != EXPECTED_ROWS:
            raise ValueError(f"expected {EXPECTED_ROWS} unique BFCL cases, got {len(rows)}")
        abstain = sum(row["decision"] == "abstain" for row in rows)
        over_limit = sum(row["reason"] == "input_too_long" for row in rows)
        decision_latencies = [row["latency_ms"] for row in rows if row["reason"] != "input_too_long"]
        run["metrics"] = {
            "rows": len(rows),
            "unique_ids": len({row["id"] for row in rows}),
            "abstention_accuracy": abstain / len(rows),
            "false_continue_count": len(rows) - abstain,
            "false_continue_rate": (len(rows) - abstain) / len(rows),
            "over_limit_rows": over_limit,
            "over_limit_rate": over_limit / len(rows),
            "function_names_matching_wrench": sum(row["function_names_match_wrench"] for row in rows),
            "decision_counts": dict(Counter(row["decision"] for row in rows)),
            "reason_counts": dict(Counter(row["reason"] for row in rows)),
            "model_decision_latency_p50_ms": statistics.median(decision_latencies) if decision_latencies else None,
            "model_decision_latency_p95_ms": percentile(decision_latencies, .95),
        }
        run["status"] = "COMPLETE"
        run["completed_utc"] = datetime.now(timezone.utc).isoformat()
        run["resources"].append(resource_sample(torch))
        write_json(output_dir / "run.json", run)
        write_json(output_dir / "summary.json", run)
        print(json.dumps({"status": run["status"], "rows": len(rows), "summary": str(output_dir / "summary.json")}))
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
