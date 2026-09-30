"""Measure typed compact source labels against the Iteration 141 prompt arms.

Tokenizer-only and synthetic-only. No model generation or provider call.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for entry in (ROOT, ROOT / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from examples.gateway_context_mvp import run_demo as demo
from examples.gateway_context_mvp import run_local_model_mvp as one_case
from examples.gateway_context_mvp import run_paired_local_context_baseline as paired

JOB_ID = "WRENCH-TYPED-COMPACT-PROMPT-ITER147"
OUTPUT = Path(
    r"C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\iter147-typed-compact-context.json"
)
APPROVED_ROOT = Path(r"C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def run() -> dict[str, object]:
    if OUTPUT.exists() or APPROVED_ROOT.resolve() not in OUTPUT.resolve().parents:
        raise FileExistsError("refusing_existing_or_unapproved_output")
    if any(expected in question or expected in paired.SYSTEM_PROMPT for _, question, expected in paired.CASES):
        raise RuntimeError("expected_answer_leaked_into_question")

    target_tokenizer, target_runtime = demo._load_tokenizer()
    from transformers import AutoTokenizer

    local_tokenizer = AutoTokenizer.from_pretrained(
        one_case.MODEL_DIR, local_files_only=True, trust_remote_code=False
    )
    original_tasks = demo.TASKS
    original_system, original_user = one_case.SYSTEM_PROMPT, one_case.USER_PROMPT
    original_budget = one_case.CONTEXT_BUDGET
    one_case.CONTEXT_BUDGET = paired.CONTEXT_BUDGET
    one_case.SYSTEM_PROMPT = paired.SYSTEM_PROMPT
    try:
        task_by_id = {row["case_id"]: row for row in original_tasks}
        baseline_total = {"target": 0, "local": 0}
        totals = {
            "legacy_json_string": {"target": 0, "local": 0},
            "compact_json_segments": {"target": 0, "local": 0},
        }
        case_rows: list[dict[str, object]] = []
        for case_id, question, expected in paired.CASES:
            demo.TASKS = (task_by_id[case_id] | {"case_id": "retry-function"},)
            one_case.USER_PROMPT = question
            base = [
                {"role": "system", "content": paired.SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ]
            full_context = "Synthetic repository context:\n" + "\n".join(
                f"--- {path} ---\n{demo.FIXTURE_FILES[path]}"
                for path in sorted(demo.FIXTURE_FILES)
            )
            baseline = [*base, {"role": "user", "content": full_context}]
            baseline_target = demo._template_tokens(target_tokenizer, baseline)
            baseline_local = demo._template_tokens(local_tokenizer, baseline)
            baseline_total["target"] += baseline_target
            baseline_total["local"] += baseline_local

            legacy_messages, legacy_meta = one_case.prepare_context(target_tokenizer)
            compact_messages, compact_meta = one_case.prepare_context(
                target_tokenizer, context_render_mode="compact_json_segments"
            )
            if compact_meta["compact_label_to_segment_id"] is None:
                raise RuntimeError("compact_label_mapping_missing")
            refs = compact_meta["selected_source_references"]
            if not isinstance(refs, dict) or refs.get("selected_segment_ids") != list(
                compact_meta["compact_label_to_segment_id"].values()
            ):
                raise RuntimeError("compact_label_mapping_source_order_mismatch")
            for name, messages in (
                ("legacy_json_string", legacy_messages),
                ("compact_json_segments", compact_messages),
            ):
                totals[name]["target"] += demo._template_tokens(target_tokenizer, messages)
                totals[name]["local"] += demo._template_tokens(local_tokenizer, messages)
            expected_quotes = tuple(str(item) for item in task_by_id[case_id]["required_quotes"])
            if not all(quote in json.dumps(compact_messages, ensure_ascii=False) for quote in expected_quotes):
                raise RuntimeError("compact_required_quote_missing")
            case_rows.append(
                {
                    "case_id": case_id,
                    "expected_answer_in_question": expected in question,
                    "required_quote_count": len(expected_quotes),
                    "compact_label_to_segment_id": compact_meta["compact_label_to_segment_id"],
                    "selected_source_references_sha256": refs["receipt_sha256"],
                    "legacy_required_quotes_visible": legacy_meta["required_quotes_visible"],
                    "compact_required_quotes_visible": compact_meta["required_quotes_visible"],
                    "target_tokens": {
                        "baseline": demo._template_tokens(target_tokenizer, baseline),
                        "legacy": demo._template_tokens(target_tokenizer, legacy_messages),
                        "compact": demo._template_tokens(target_tokenizer, compact_messages),
                    },
                }
            )
        summary = {
            name: {
                **counts,
                "target_reduction_percent": round(
                    100 * (1 - counts["target"] / baseline_total["target"]), 6
                ),
                "local_reduction_percent": round(
                    100 * (1 - counts["local"] / baseline_total["local"]), 6
                ),
            }
            for name, counts in totals.items()
        }
        return {
            "schema": "wrench.gateway-typed-compact-context.v1",
            "job_id": JOB_ID,
            "status": "complete",
            "claim_scope": "tokenizer_only_three_authored_synthetic_lookup_tasks",
            "target_tokenizer_runtime": target_runtime,
            "local_model_tokenizer_id": "Qwen/Qwen3.5-0.8B@2fc06364715b967f1860aea9cf38778875588b17",
            "context_budget": paired.CONTEXT_BUDGET,
            "baseline_input_tokens": baseline_total,
            "summary": summary,
            "cases": case_rows,
            "source_sha256": {
                name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                for name in (
                    "src/wrench_harness/context.py",
                    "src/wrench_harness/prompt_compiler.py",
                    "src/wrench_harness/e0_context_pipeline.py",
                    "examples/gateway_context_mvp/run_local_model_mvp.py",
                    "examples/gateway_context_mvp/run_paired_local_context_baseline.py",
                )
            },
            "limitations": [
                "no model generation, verified answer outcome, LoRA, provider call, frontier-token or cost measurement",
                "three authored lookup tasks only; no broad coding-task coverage",
                "compact labels rely on deterministic selection order and an external source-reference receipt",
            ],
        }
    finally:
        demo.TASKS = original_tasks
        one_case.SYSTEM_PROMPT, one_case.USER_PROMPT = original_system, original_user
        one_case.CONTEXT_BUDGET = original_budget


if __name__ == "__main__":
    result = run()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    with OUTPUT.with_suffix(".json.tmp").open("xb") as handle:
        handle.write(encoded)
        handle.flush()
    OUTPUT.with_suffix(".json.tmp").replace(OUTPUT)
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "bytes": len(encoded),
                "sha256": sha256_bytes(encoded),
                "summary": result["summary"],
            },
            sort_keys=True,
        )
    )
