"""Measure Wrench-or-abstain accuracy and decision speed on the pinned suite.

No proposal, file action, network call, provider call, or generation is run.
The independent verifier remains outside this classifier-only measurement.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import random
import sys
import time

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from train_qwen_abstain import Guard


def wilson(successes: int, total: int) -> list[float]:
    z = 1.959963984540054
    p = successes / total
    d = 1 + z*z/total
    centre = (p + z*z/(2*total))/d
    half = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/d
    return [max(0., centre-half), min(1., centre+half)]


def grouped_interval(groups: list[tuple[int, int]], *, draws: int = 2000) -> list[float]:
    rng = random.Random(47)
    estimates = []
    for _ in range(draws):
        sample = [groups[rng.randrange(len(groups))] for _ in groups]
        estimates.append(sum(correct for correct, _ in sample) / sum(total for _, total in sample))
    estimates.sort()
    return [estimates[int(.025 * draws)], estimates[int(.975 * draws) - 1]]


def run(args):
    import torch
    import transformers
    from transformers import AutoModelForImageTextToText, AutoTokenizer
    from wrench_harness.qwen_abstain import QwenAbstainGate, checkpoint_identity, sha256_file
    from wrench_harness.system_one_preflight import WrenchBinaryRouter

    args.output.mkdir(parents=True, exist_ok=False)
    guard = Guard(args.max_seconds)
    receipt = {"schema": "wrench.system-one-5k-evaluation.v1", "status": "RUNNING",
               "scope": "binary classifier with abstain-only preflight" if args.preflight else "binary classifier decision only",
               "preflight_enabled": args.preflight, "provider_calls": 0,
               "generated_tokens": 0, "tool_actions": 0, "final_split_read": False,
               "production_enabled": False, "evaluator_sha256": sha256_file(Path(__file__)),
               "environment": {"torch": torch.__version__,
                                                       "transformers": transformers.__version__}}
    try:
        guard.check()
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if manifest.get("labels") != {"abstain": 5000, "wrench": 600}:
            raise ValueError("suite label manifest mismatch")
        with args.cases.open("rb") as stream:
            raw = stream.read(3_000_001)
        if len(raw) > 3_000_000 or hashlib.sha256(raw).hexdigest() != manifest.get("cases_sha256"):
            raise ValueError("suite case hash or byte budget mismatch")
        cases = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
        if len(cases) != 5600 or Counter(case.get("label") for case in cases) != {"abstain": 5000, "wrench": 600}:
            raise ValueError("suite row count mismatch")
        if dict(Counter(case.get("category") for case in cases)) != manifest.get("categories"):
            raise ValueError("suite category manifest mismatch")
        ids = {case.get("id") for case in cases}
        if len(ids) != len(cases) or any(not isinstance(case.get("prompt"), str) or not case["prompt"] for case in cases):
            raise ValueError("duplicate IDs or invalid prompts")
        receipt.update(cases_sha256=manifest["cases_sha256"], case_count=len(cases),
                       artifact_sha256=sha256_file(args.artifact))
        print("Hashing existing Qwen checkpoint", flush=True)
        identity = checkpoint_identity(args.model, guard.check)
        receipt["checkpoint_sha256"] = identity
        checkpoint_bytes = sum((args.model / name).stat().st_size for name in identity if name.endswith(".safetensors"))
        guard.check(extra_ram=checkpoint_bytes + 1_500_000_000,
                    extra_vram=checkpoint_bytes + 1_500_000_000)
        tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
        model = AutoModelForImageTextToText.from_pretrained(args.model, dtype=torch.bfloat16,
                    local_files_only=True, trust_remote_code=False).to("cuda:0").eval().requires_grad_(False)
        torch.set_num_threads(2)
        gate = QwenAbstainGate.from_artifact(args.artifact, model=model, tokenizer=tokenizer,
                                            model_dir=args.model, identity=identity)
        if args.preflight:
            preflight_source = Path(__file__).resolve().parents[1] / "src/wrench_harness/system_one_preflight.py"
            receipt["preflight_source_sha256"] = sha256_file(preflight_source)
            gate = WrenchBinaryRouter(gate)
        receipt["environment"]["gpu"] = torch.cuda.get_device_name(0)
        receipt["backbone_allocated_vram_bytes"] = torch.cuda.memory_allocated(0)
        warm = gate.check_messages([{"role": "user", "content": "Read README.md, maximum 262144 bytes."}])
        if warm.get("model_forwards") != 1:
            raise RuntimeError("warm classifier request failed")
        timings = []
        preflight_timings = []
        model_timings = []
        metrics = defaultdict(lambda: Counter())
        grouped = defaultdict(lambda: Counter())
        failures = []
        with (args.output / "predictions.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
            for index, case in enumerate(cases):
                torch.cuda.synchronize()
                started = time.perf_counter()
                try:
                    result = gate.check_messages([{"role": "user", "content": case["prompt"]}])
                except Exception as exc:
                    result = {"decision": "abstain", "reason": "runtime_error", "error": type(exc).__name__,
                              "model_forwards": 0, "generated_tokens": 0}
                torch.cuda.synchronize()
                elapsed_ms = (time.perf_counter() - started) * 1000
                expected = "not_abstain" if case["label"] == "wrench" else "abstain"
                model_decision = result.get("reason") == "model_decision" and result.get("model_forwards") == 1
                explicit_veto = (args.preflight and result.get("model_forwards") == 0
                                 and result.get("decision") == "abstain"
                                 and str(result.get("reason", "")).startswith("explicit_")
                                 and result.get("authority") == "abstain_only")
                valid = model_decision or explicit_veto
                correct = valid and result.get("decision") == expected
                if not valid:
                    failures.append({"id": case["id"], "reason": result.get("reason"),
                                     "error": result.get("error")})
                else:
                    timings.append(elapsed_ms)
                    (model_timings if model_decision else preflight_timings).append(elapsed_ms)
                category = metrics[case["category"]]
                category["rows"] += 1
                category["correct"] += int(correct)
                category["runtime_errors"] += int(not valid)
                category["false_wrench"] += int(case["label"] == "abstain" and
                                                 result.get("decision") == "not_abstain" and valid)
                category["false_abstain"] += int(case["label"] == "wrench" and
                                                  result.get("decision") == "abstain" and valid)
                grouped[(case["label"], case["pattern_group"])]["rows"] += 1
                grouped[(case["label"], case["pattern_group"])]["correct"] += int(correct)
                record = {"id": case["id"], "label": case["label"], "category": case["category"],
                          "group": case["pattern_group"], "decision": result.get("decision"),
                          "reason": result.get("reason"), "probabilities": result.get("probabilities"),
                          "model_forwards": result.get("model_forwards"), "elapsed_ms": elapsed_ms,
                          "correct": correct}
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                if (index + 1) % 32 == 0:
                    stream.flush()
                    guard.check()
                if (index + 1) % 500 == 0:
                    print(f"Scored {index+1}/{len(cases)} requests", flush=True)
        abstain_categories = [name for name in metrics if name not in {
            "read_file", "read_lines", "literal_search", "git_read_status", "health_read", "patch_draft"}]
        false_wrench = sum(metrics[name]["false_wrench"] for name in abstain_categories)
        false_abstain = sum(metrics[name]["false_abstain"] for name in metrics if name not in abstain_categories)
        abstain_correct = sum(metrics[name]["correct"] for name in abstain_categories)
        wrench_correct = sum(metrics[name]["correct"] for name in metrics if name not in abstain_categories)
        correct = sum(value["correct"] for value in metrics.values())
        abstain_groups = [(value["correct"], value["rows"]) for (label, _), value in grouped.items()
                          if label == "abstain"]
        wrench_groups = [(value["correct"], value["rows"]) for (label, _), value in grouped.items()
                         if label == "wrench"]
        if len(abstain_groups) != 100 or len(wrench_groups) != 60:
            raise ValueError("pattern-group count changed")
        if timings:
            t = torch.tensor(timings)
            latency = {"p50": float(t.median()), "p95": float(t.quantile(.95)),
                       "max": float(t.max()), "samples": len(timings)}
        else:
            latency = None
        receipt.update(status="CLASSIFIER_SUITE_COMPLETE", correct=correct,
                       accuracy=correct/5600, accuracy_wilson95=wilson(correct, 5600),
                       abstain_recall=abstain_correct/5000,
                       abstain_recall_wilson95=wilson(abstain_correct, 5000),
                       abstain_recall_group_bootstrap95=grouped_interval(abstain_groups),
                       wrench_coverage=wrench_correct/600,
                       wrench_coverage_wilson95=wilson(wrench_correct, 600),
                       wrench_coverage_group_bootstrap95=grouped_interval(wrench_groups),
                       balanced_accuracy=(abstain_correct/5000+wrench_correct/600)/2,
                       false_wrench=false_wrench, false_abstain=false_abstain,
                       runtime_errors=len(failures), runtime_failure_examples=failures[:20],
                       latency_ms=latency,
                       preflight_veto_count=len(preflight_timings),
                       model_forward_count=len(model_timings),
                       preflight_latency_ms=(None if not preflight_timings else {
                           "p50": float(torch.tensor(preflight_timings).median()),
                           "p95": float(torch.tensor(preflight_timings).quantile(.95))}),
                       model_latency_ms=(None if not model_timings else {
                           "p50": float(torch.tensor(model_timings).median()),
                           "p95": float(torch.tensor(model_timings).quantile(.95))}),
                       categories={name: dict(value) for name, value in metrics.items()})
        receipt["diagnostic_target_pass"] = (not failures and false_wrench == 0
                and receipt["wrench_coverage"] >= .95 and receipt["balanced_accuracy"] >= .975
                and latency is not None and latency["p95"] < 500)
        if receipt["evaluator_sha256"] != sha256_file(Path(__file__)):
            raise RuntimeError("evaluator source changed during run")
        if args.preflight and receipt["preflight_source_sha256"] != sha256_file(preflight_source):
            raise RuntimeError("preflight source changed during run")
        guard.check()
    except Exception as exc:
        receipt.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        receipt["resource_samples"] = guard.samples
        (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "accuracy", "balanced_accuracy",
                                                   "false_wrench", "false_abstain", "runtime_errors",
                                                   "latency_ms", "diagnostic_target_pass")}, indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-seconds", type=int, default=3600)
    parser.add_argument("--preflight", action="store_true")
    run(parser.parse_args())
