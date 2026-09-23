"""Run the frozen Wrench binary abstention gate on pinned external data.

The runner records both the benchmark-component label and the separate
Wrench-allowlist view. It never generates a proposal or executes a tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PHASE = Path(__file__).resolve().parent
REPO = PHASE.parents[1]
EXTERNAL = PHASE / "external"
sys.path.insert(0, str(REPO / "src"))

WRENCH_ACTIONS = {
    "read_file",
    "read_lines",
    "literal_search",
    "git_read_status",
    "health_read",
    "patch_draft",
}

WHEN2CALL_SYSTEM = """You are Qwen, created by Alibaba Cloud. You are a helpful assistant.

# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{tools}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{{"name": <function-name>, "arguments": <args-json-object>}}
</tool_call>"""

TOOLBH_SYSTEM = """Judge task solvability using only the tool names and capabilities shown.
Do not invent tools or capabilities. Decide whether the supplied tools are sufficient
to complete the task as stated."""


class ResourceReserveError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resource_sample(torch) -> dict[str, Any]:
    try:
        import psutil

        ram_free = int(psutil.virtual_memory().available)
        ram_total = int(psutil.virtual_memory().total)
    except ImportError:
        import ctypes

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
        status.dwLength = ctypes.sizeof(MemoryStatusEx)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise OSError("GlobalMemoryStatusEx failed")
        ram_free = int(status.ullAvailPhys)
        ram_total = int(status.ullTotalPhys)
    sample: dict[str, Any] = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "ram_free_bytes": ram_free,
        "ram_total_bytes": ram_total,
        "vram_free_bytes": None,
        "vram_total_bytes": None,
    }
    if torch.cuda.is_available():
        free, total = torch.cuda.mem_get_info()
        sample["vram_free_bytes"] = int(free)
        sample["vram_total_bytes"] = int(total)
        if free < total * 0.10:
            raise ResourceReserveError("less than 10 percent VRAM reserve remains")
    if ram_free < ram_total * 0.10:
        raise ResourceReserveError("less than 10 percent RAM reserve remains")
    return sample


def jsonable_tools(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def parse_target_tool(row: dict[str, Any]) -> str | None:
    target = row.get("target_tool")
    if isinstance(target, str) and target:
        return target
    answers = row.get("answers")
    call = answers.get("tool_call") if isinstance(answers, dict) else None
    if isinstance(call, str):
        try:
            parsed = json.loads(call)
        except json.JSONDecodeError:
            return None
        name = parsed.get("name") if isinstance(parsed, dict) else None
        return name if isinstance(name, str) else None
    return None


def when2call_cases(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"When2Call row {line_number} is not an object")
            question = row.get("question")
            tools = row.get("tools")
            label = row.get("correct_answer")
            if not isinstance(question, str) or not isinstance(tools, list):
                raise ValueError(f"invalid When2Call question or tool list at row {line_number}")
            if label not in {"tool_call", "request_for_info", "cannot_answer"}:
                raise ValueError(f"unexpected When2Call gold label at row {line_number}")
            tool_text = "\n".join(item if isinstance(item, str) else jsonable_tools(item) for item in tools)
            yield {
                "id": row.get("uuid", str(line_number)),
                "group": row.get("source", "unknown"),
                "variant": "abstract_tool_decision",
                "benchmark_gold": label,
                "expected_binary": "not_abstain" if label == "tool_call" else "abstain",
                "target_tool": parse_target_tool(row),
                "messages": [
                    {"role": "system", "content": WHEN2CALL_SYSTEM.format(tools=tool_text)},
                    {"role": "user", "content": question},
                ],
            }


def toolbehonest_cases(path: Path) -> Iterable[dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("ToolBeHonest input must be a JSON array")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("ToolBeHonest row is not an object")
        group = row.get("subtask", "unknown")
        row_id = row.get("id")
        task = row.get("task")
        toolset = row.get("tools")
        unsolvable_task = row.get("unsolvable_task")
        unsolvable_tools = row.get("unsolvable_tools")
        if not all(isinstance(x, str) and x for x in (task, toolset, unsolvable_task, unsolvable_tools)):
            raise ValueError(f"invalid paired ToolBeHonest record id={row_id}")
        yield {
            "id": f"{row_id}:solvable",
            "group": group,
            "variant": "solvable",
            "benchmark_gold": "solvable",
            "expected_binary": "not_abstain",
            "target_tool": None,
            "messages": [
                {"role": "system", "content": TOOLBH_SYSTEM + "\n\nAvailable tools:\n" + toolset},
                {"role": "user", "content": task},
            ],
        }
        yield {
            "id": f"{row_id}:unsolvable",
            "group": group,
            "variant": "unsolvable",
            "benchmark_gold": "unsolvable",
            "expected_binary": "abstain",
            "target_tool": None,
            "messages": [
                {"role": "system", "content": TOOLBH_SYSTEM + "\n\nAvailable tools:\n" + unsolvable_tools},
                {"role": "user", "content": unsolvable_task},
            ],
        }


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[tuple[str, str]] = Counter()
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    no_call: list[dict[str, Any]] = []
    abstract_call: list[dict[str, Any]] = []
    mapped_call: list[dict[str, Any]] = []
    solvable: list[dict[str, Any]] = []
    unsolvable: list[dict[str, Any]] = []
    for row in rows:
        expected = row["expected_binary"]
        predicted = row["decision"]
        counts[(expected, predicted)] += 1
        groups[row["group"]].append(row)
        if row["benchmark_gold"] == "solvable":
            solvable.append(row)
        elif row["benchmark_gold"] == "unsolvable":
            unsolvable.append(row)
        if row["variant"] == "unsolvable" or row["benchmark_gold"] in {"request_for_info", "cannot_answer"}:
            no_call.append(row)
        if row["benchmark_gold"] == "tool_call":
            abstract_call.append(row)
            if row.get("target_tool") in WRENCH_ACTIONS:
                mapped_call.append(row)

    tp = counts[("not_abstain", "not_abstain")]
    fp = counts[("abstain", "not_abstain")]
    fn = counts[("not_abstain", "abstain")]
    tn = counts[("abstain", "abstain")]
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else 0.0
    policy_unsupported = [row for row in abstract_call if row.get("target_tool") not in WRENCH_ACTIONS]
    return {
        "rows": len(rows),
        "abstract_confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "abstract_call_precision": precision,
        "abstract_call_recall": recall,
        "abstract_call_f1": f1,
        "abstract_decision_accuracy": (tp + tn) / len(rows) if rows else None,
        "abstract_tool_call_count": len(abstract_call),
        "unsupported_tool_call_count": len(policy_unsupported),
        "unsupported_tool_false_continue_rate": (
            sum(row["decision"] == "not_abstain" for row in policy_unsupported) / len(policy_unsupported)
            if policy_unsupported else None
        ),
        "audited_wrench_eligible_call_count": len(mapped_call),
        "audited_wrench_eligible_call_recall": (
            sum(row["decision"] == "not_abstain" for row in mapped_call) / len(mapped_call)
            if mapped_call else None
        ),
        "no_call_false_continue_rate": (
            sum(row["decision"] == "not_abstain" for row in no_call) / len(no_call)
            if no_call else None
        ),
        "toolbehonest_solvable_pass_rate": (
            sum(row["decision"] == "not_abstain" for row in solvable) / len(solvable)
            if solvable else None
        ),
        "toolbehonest_false_solvable_rate": (
            sum(row["decision"] == "not_abstain" for row in unsolvable) / len(unsolvable)
            if unsolvable else None
        ),
        "over_limit_rows": sum(row.get("reason") == "input_too_long" for row in rows),
        "context_resolution_rows": sum(row.get("reason") == "context_requires_resolution" for row in rows),
        "mean_latency_ms": statistics.fmean(row["latency_ms"] for row in rows) if rows else None,
        "p50_latency_ms": percentile([row["latency_ms"] for row in rows], 0.50),
        "p95_latency_ms": percentile([row["latency_ms"] for row in rows], 0.95),
        "by_group": {
            group: {
                "rows": len(items),
                "accuracy": sum(item["decision"] == item["expected_binary"] for item in items) / len(items),
                "not_abstain": sum(item["decision"] == "not_abstain" for item in items),
                "abstain": sum(item["decision"] == "abstain" for item in items),
            }
            for group, items in sorted(groups.items())
        },
    }


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("when2call", "toolbehonest"), required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--head", type=Path, required=True)
    parser.add_argument("--data", type=Path, help="Override the pinned suite data path")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resource-check-every", type=int, default=25)
    args = parser.parse_args()
    if args.resource_check_every < 1:
        parser.error("--resource-check-every must be at least 1")

    data_path = args.data or (
        EXTERNAL / "when2call" / "data" / "when2call_test_mcq.jsonl"
        if args.suite == "when2call"
        else EXTERNAL / "toolbehonest" / "data" / "test_en.json"
    )
    data_path = data_path.resolve()
    model_dir = args.model_dir.resolve()
    head_path = args.head.resolve()
    output_dir = args.output_dir.resolve()
    if not data_path.is_file() or not model_dir.is_dir() or not head_path.is_file():
        parser.error("suite data, model directory, and head artifact must exist")
    output_dir.mkdir(parents=True, exist_ok=False)

    run_meta: dict[str, Any] = {
        "schema": "wrench.external-binary-suite-run.v1",
        "suite": args.suite,
        "status": "LOADING",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "data_path": str(data_path),
        "data_sha256": sha256_file(data_path),
        "head_sha256": sha256_file(head_path),
        "model_dir": str(model_dir),
        "checkpoint_identity": json.loads(head_path.read_text(encoding="utf-8")).get("checkpoint_sha256"),
        "predictions_file": "predictions.jsonl",
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
        run_meta["resources"].append(resource_sample(torch))
        worker = WrenchWorker.from_pretrained(
            model_dir,
            allowed_root=output_dir,
            binary_abstain_artifact=head_path,
        )
        if worker.binary_abstain_gate is None:
            raise ValueError("binary abstention head did not load")
        run_meta["head_threshold"] = worker.binary_abstain_gate.threshold
        run_meta["max_input_tokens"] = worker.binary_abstain_gate.max_tokens
        run_meta["max_input_chars"] = worker.binary_abstain_gate.max_chars
        run_meta["prompt_adapter"] = "when2call-official-qwen2.5-system-template-v1" if args.suite == "when2call" else "toolbehonest-task-tools-binary-v1"
        run_meta["resources"].append(resource_sample(torch))
        run_meta["status"] = "RUNNING"
        write_json(output_dir / "run.json", run_meta)

        case_iter = when2call_cases(data_path) if args.suite == "when2call" else toolbehonest_cases(data_path)
        all_rows: list[dict[str, Any]] = []
        with (output_dir / "predictions.jsonl").open("x", encoding="utf-8") as predictions:
            for index, case in enumerate(case_iter, 1):
                if (index - 1) % args.resource_check_every == 0:
                    run_meta["resources"].append(resource_sample(torch))
                started = time.perf_counter()
                receipt = worker.classify_abstention(case["messages"])
                latency_ms = (time.perf_counter() - started) * 1000
                result = {
                    "id": str(case["id"]),
                    "group": str(case["group"]),
                    "variant": case["variant"],
                    "benchmark_gold": case["benchmark_gold"],
                    "expected_binary": case["expected_binary"],
                    "target_tool": case.get("target_tool"),
                    "target_is_wrench_action": case.get("target_tool") in WRENCH_ACTIONS,
                    "decision": receipt.get("decision", "abstain"),
                    "reason": receipt.get("reason"),
                    "probabilities": receipt.get("probabilities"),
                    "input_tokens": receipt.get("input_tokens"),
                    "input_chars": sum(len(message["content"]) for message in case["messages"]),
                    "latency_ms": latency_ms,
                }
                predictions.write(json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
                predictions.flush()
                all_rows.append(result)
                run_meta["completed_rows"] = index
                if index % args.resource_check_every == 0:
                    write_json(output_dir / "run.json", run_meta)
        run_meta["metrics"] = metrics(all_rows)
        run_meta["status"] = "COMPLETE"
        run_meta["completed_utc"] = datetime.now(timezone.utc).isoformat()
        run_meta["resources"].append(resource_sample(torch))
        write_json(output_dir / "run.json", run_meta)
        write_json(output_dir / "summary.json", run_meta)
        print(json.dumps({"status": run_meta["status"], "suite": args.suite, "rows": len(all_rows), "summary": str(output_dir / "summary.json")}, ensure_ascii=False))
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
