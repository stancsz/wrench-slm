"""Score Wrench's frozen binary gate on ARB V2 labels.

This is a decision-only component adapter. It does not measure retrieval rank,
Recall@20, MRR, context yield, selective retrieval success, or task completion.
The gold labels and metadata are used only after inference for scoring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
import platform
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[1]
EXTERNAL = PHASE / "external" / "agent-retrieval-bench"
DATA = EXTERNAL / "data" / "benchmark" / "v2_selective_retrieval_natural" / "samples.jsonl"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(EXTERNAL / "upstream" / "src"))


class ResourceReserveError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resource_sample(torch) -> dict[str, Any]:
    import psutil

    memory = psutil.virtual_memory()
    sample: dict[str, Any] = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "ram_free_bytes": int(memory.available),
        "ram_total_bytes": int(memory.total),
        "vram_free_bytes": None,
        "vram_total_bytes": None,
    }
    if sample["ram_free_bytes"] < sample["ram_total_bytes"] * 0.10:
        raise ResourceReserveError("less than 10 percent RAM reserve remains")
    if torch.cuda.is_available():
        free, total = torch.cuda.mem_get_info()
        sample["vram_free_bytes"] = int(free)
        sample["vram_total_bytes"] = int(total)
        if free < total * 0.10:
            raise ResourceReserveError("less than 10 percent VRAM reserve remains")
    return sample


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def evaluate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["group"]].append(row)
    positive = groups.get("positive", [])
    natural = groups.get("natural_no_gold", [])
    counterfactual = groups.get("counterfactual_no_gold", [])
    all_no_gold = natural + counterfactual

    def rate(items: list[dict[str, Any]], pred: str) -> float | None:
        if not items:
            return None
        return sum(row["decision"] == pred for row in items) / len(items)

    accuracy = sum(row["decision"] == row["expected"] for row in rows) / len(rows) if rows else None
    balanced_accuracy = (
        (rate(positive, "not_abstain") + rate(natural, "abstain")) / 2
        if positive and natural else None
    )
    accepted = [row for row in rows if row["decision"] == "not_abstain"]
    model_scored = [row for row in rows if row.get("reason") != "input_too_long"]
    model_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in model_scored:
        model_groups[row["group"]].append(row)

    def subset_rate(items: list[dict[str, Any]], pred: str) -> float | None:
        return sum(row["decision"] == pred for row in items) / len(items) if items else None

    return {
        "rows": len(rows),
        "binary_decision_accuracy": accuracy,
        "balanced_accuracy_positive_vs_natural_no_gold": balanced_accuracy,
        "balanced_accuracy_positive_vs_all_no_gold": (
            (rate(positive, "not_abstain") + rate(all_no_gold, "abstain")) / 2
            if positive and all_no_gold else None
        ),
        "positive_cases": len(positive),
        "positive_continue_rate": rate(positive, "not_abstain"),
        "natural_no_gold_cases": len(natural),
        "natural_no_gold_abstention_rate": rate(natural, "abstain"),
        "natural_no_gold_false_continue_rate": rate(natural, "not_abstain"),
        "counterfactual_no_gold_cases": len(counterfactual),
        "counterfactual_no_gold_abstention_rate": rate(counterfactual, "abstain"),
        "accepted_case_positive_precision": (
            sum(row["group"] == "positive" for row in accepted) / len(accepted) if accepted else None
        ),
        "input_limit_abstentions": sum(row.get("reason") == "input_too_long" for row in rows),
        "model_scored_cases": len(model_scored),
        "model_scored_positive_cases": len(model_groups.get("positive", [])),
        "model_scored_positive_continue_rate": subset_rate(model_groups.get("positive", []), "not_abstain"),
        "model_scored_natural_no_gold_cases": len(model_groups.get("natural_no_gold", [])),
        "model_scored_natural_no_gold_abstention_rate": subset_rate(model_groups.get("natural_no_gold", []), "abstain"),
        "model_scored_counterfactual_no_gold_cases": len(model_groups.get("counterfactual_no_gold", [])),
        "model_scored_counterfactual_no_gold_abstention_rate": subset_rate(model_groups.get("counterfactual_no_gold", []), "abstain"),
        "model_scored_mean_latency_ms": statistics.fmean(row["latency_ms"] for row in model_scored) if model_scored else None,
        "model_scored_p50_latency_ms": percentile([row["latency_ms"] for row in model_scored], 0.50),
        "model_scored_p95_latency_ms": percentile([row["latency_ms"] for row in model_scored], 0.95),
        "mean_latency_ms": statistics.fmean(row["latency_ms"] for row in rows) if rows else None,
        "p50_latency_ms": percentile([row["latency_ms"] for row in rows], 0.50),
        "p95_latency_ms": percentile([row["latency_ms"] for row in rows], 0.95),
        "by_group": {
            group: {
                "rows": len(items),
                "accuracy": sum(row["decision"] == row["expected"] for row in items) / len(items),
                "abstain": sum(row["decision"] == "abstain" for row in items),
                "not_abstain": sum(row["decision"] == "not_abstain" for row in items),
            }
            for group, items in sorted(groups.items())
        },
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def load_cases(data_path: Path) -> list[dict[str, Any]]:
    from agent_retrieval_bench.baseline import query_has_leakage, query_text_for_eval

    cases: list[dict[str, Any]] = []
    with data_path.open("r", encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            sample = json.loads(line)
            query = query_text_for_eval(sample)
            if query_has_leakage(sample, query):
                raise ValueError(f"official ARB query leakage check failed at row {number}")
            no_gold = bool((sample.get("gold") or {}).get("no_gold"))
            organic = (sample.get("metadata") or {}).get("organic")
            if no_gold and organic is True:
                group = "natural_no_gold"
            elif no_gold:
                group = "counterfactual_no_gold"
            else:
                group = "positive"
            expected = "abstain" if no_gold else "not_abstain"
            user_content = f"Repository: {sample['repo']}\nRequest: {query}"
            cases.append({
                "id": str(sample["id"]),
                "repo": str(sample["repo"]),
                "group": group,
                "expected": expected,
                "messages": [
                    {"role": "system", "content": (
                        "You are the binary continuation gate for a bounded, read-only repository context worker. "
                        "The worker may continue only to propose permitted file reading or literal search. "
                        "Continue when the request appears to seek relevant evidence in the named repository. "
                        "Abstain when the request is unsupported by that repository or cannot be handled by those "
                        "read-only actions. A continue decision grants no execution authority."
                    )},
                    {"role": "user", "content": user_content},
                ],
            })
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--head", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resource-check-every", type=int, default=20)
    args = parser.parse_args()
    if args.resource_check_every < 1:
        parser.error("--resource-check-every must be at least 1")

    data_path, model_dir, head_path = args.data.resolve(), args.model_dir.resolve(), args.head.resolve()
    output_dir = args.output_dir.resolve()
    if not data_path.is_file() or not model_dir.is_dir() or not head_path.is_file():
        parser.error("ARB data, model directory, and head artifact must exist")
    if output_dir.exists():
        parser.error(f"output directory already exists: {output_dir}")
    cases = load_cases(data_path)
    output_dir.mkdir(parents=True)
    run_meta: dict[str, Any] = {
        "schema": "wrench.arb-v2-binary-gate-component.v1",
        "suite": "Agent Retrieval Bench V2 selective natural split",
        "status": "LOADING",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "data_sha256": sha256_file(data_path),
        "rows": len(cases),
        "head_sha256": sha256_file(head_path),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "model_dir": str(model_dir),
        "predictions_file": "predictions.jsonl",
        "prompt_adapter": "arb-v2-official-query-text-plus-repository-name-binary-gate-v1",
        "official_query_text": "agent_retrieval_bench.baseline.query_text_for_eval",
        "gold_or_metadata_in_prompt": False,
        "official_leakage_check_passed": True,
        "metric_scope": "binary continuation and abstention component only; not retrieval ranking or task success",
        "provider_calls": 0,
        "generated_tokens": 0,
        "tool_execution": False,
        "training_or_tuning": False,
        "resources": [],
    }
    write_json(output_dir / "run.json", run_meta)
    try:
        import torch
        import transformers
        from wrench_harness.worker import WrenchWorker

        run_meta["torch_version"] = torch.__version__
        run_meta["transformers_version"] = transformers.__version__
        run_meta["python_version"] = platform.python_version()
        run_meta["device"] = "cuda" if torch.cuda.is_available() else "cpu"
        run_meta["device_name"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"
        run_meta["resources"].append(resource_sample(torch))
        worker = WrenchWorker.from_pretrained(
            model_dir,
            allowed_root=output_dir,
            binary_abstain_artifact=head_path,
        )
        if worker.binary_abstain_gate is None:
            raise ValueError("binary abstention head did not load")
        gate = worker.binary_abstain_gate
        run_meta["checkpoint_sha256"] = json.loads(head_path.read_text(encoding="utf-8"))["checkpoint_sha256"]
        run_meta["head_threshold"] = gate.threshold
        run_meta["max_input_tokens"] = gate.max_tokens
        run_meta["max_input_chars"] = gate.max_chars
        run_meta["resources"].append(resource_sample(torch))
        warmup_messages = [
            {"role": "system", "content": "Bounded read-only repository evidence gate."},
            {"role": "user", "content": "Repository: warmup/example\nRequest: locate the matching implementation."},
        ]
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        warmup_started = time.perf_counter()
        worker.classify_abstention(warmup_messages)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        run_meta["warmup_latency_ms"] = (time.perf_counter() - warmup_started) * 1000
        run_meta["status"] = "RUNNING"
        write_json(output_dir / "run.json", run_meta)

        predictions: list[dict[str, Any]] = []
        with (output_dir / "predictions.jsonl").open("x", encoding="utf-8") as stream:
            for index, case in enumerate(cases, 1):
                if (index - 1) % args.resource_check_every == 0:
                    run_meta["resources"].append(resource_sample(torch))
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
                started = time.perf_counter()
                receipt = worker.classify_abstention(case["messages"])
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
                result = {
                    "id": case["id"],
                    "group": case["group"],
                    "expected": case["expected"],
                    "decision": receipt.get("decision", "abstain"),
                    "reason": receipt.get("reason"),
                    "probabilities": receipt.get("probabilities"),
                    "input_tokens": receipt.get("input_tokens"),
                    "input_chars": sum(len(message["content"]) for message in case["messages"]),
                    "latency_ms": (time.perf_counter() - started) * 1000,
                }
                stream.write(json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
                stream.flush()
                predictions.append(result)
                run_meta["completed_rows"] = index
                if index % args.resource_check_every == 0:
                    write_json(output_dir / "run.json", run_meta)

        run_meta["metrics"] = evaluate(predictions)
        run_meta["status"] = "COMPLETE"
        run_meta["completed_utc"] = datetime.now(timezone.utc).isoformat()
        run_meta["resources"].append(resource_sample(torch))
        write_json(output_dir / "run.json", run_meta)
        write_json(output_dir / "summary.json", run_meta)
        print(json.dumps({"status": "COMPLETE", "metrics": run_meta["metrics"], "summary": str(output_dir / "summary.json")}, allow_nan=False))
        return 0
    except ResourceReserveError as exc:
        run_meta["status"] = "RESOURCE_UNSAFE_STOP"
        run_meta["error"] = str(exc)
        run_meta["completed_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(output_dir / "run.json", run_meta)
        print(json.dumps({"status": run_meta["status"], "error": str(exc), "completed_rows": run_meta.get("completed_rows", 0)}), file=sys.stderr)
        return 2
    except Exception as exc:
        run_meta["status"] = "FAILED"
        run_meta["error_type"] = type(exc).__name__
        run_meta["error"] = str(exc)
        run_meta["completed_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(output_dir / "run.json", run_meta)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
