"""Measure narrow prompt-only local work on fresh synthetic examples."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import subprocess
import time
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_local_synthetic_challenge as base


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "fixtures" / "local_prompt_only_work_v1.json"
JOB_ID = "W2-LOCAL-PROMPTONLY-SCREEN-20260925-01"
NONCE = "PROMPTONLY-6C31"
EXPECTED_FIXTURE_SHA256 = "525f8cb9639d17633a466129fb7b386ea0cdd33594e4c9a34e10dd6de40ecf9e"
SUPERVISOR = ROOT / "tools" / "run_local_prompt_only_work_with_deadline.py"
HARD_PROCESS_TIMEOUT_SECONDS = 25 * 60
EXPECTED_CASES = {
    "log-type-01", "log-type-02", "log-type-03", "log-type-04", "log-type-05", "log-type-06",
    "config-value-01", "config-value-02", "config-value-03", "config-value-04", "config-value-05", "config-value-06",
    "locate-01", "locate-02", "locate-03", "locate-04", "locate-05", "locate-06",
}
CLASSES = {
    "log_type_mapping": 6,
    "config_value_extraction": 6,
    "snippet_function_localization": 6,
}
SYSTEM_PROMPT = (
    "Answer only from the synthetic text in the user's message. You have no tools and must not claim to have read any other file. "
    "For exception lines use this fixed mapping: TimeoutError=timeout, PermissionError=permission, "
    "TypeError=type, ValueError=value. If more than one mapped exception is present, abstain as ambiguous. "
    "For configuration extraction, answer only when the named key appears exactly once; otherwise abstain as not_present or ambiguous. "
    "For function localization, answer only when exactly one function body reads the named property; otherwise abstain as not_present or ambiguous. "
    "A known answer must cite exact numbered input line(s) as evidence. For function localization cite both the function def line "
    "and the target property access line, in that order; other tasks cite one line. Return exactly one JSON object and no other text. "
    "Known schema: {\"status\":\"known\",\"answer\":\"string\",\"evidence\":[{\"line\":1,\"quote\":\"exact line without its number prefix\"}],\"reason\":null}. "
    "Unknown schema: {\"status\":\"unknown\",\"answer\":null,\"evidence\":null,\"reason\":\"not_present\" or \"ambiguous\"}."
)
ARTIFACT_ROOT = base.DATA_ROOT / "artifacts" / "wrench-local-acceptability"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _repo_head() -> str:
    completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                               text=True, timeout=10, check=True)
    return completed.stdout.strip()


def _write_checkpoint(path: Path, report: dict[str, Any]) -> None:
    budget = _assert_storage_admitted()
    report["storage_budget_last_check"] = {
        key: budget[key] for key in ("status", "actual_bytes", "active_reservations_bytes", "projected_bytes", "headroom_bytes")
    }
    report["by_class"] = _summaries(report["results"])
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise base.ChallengeError("checkpoint_temporary_path_already_exists")
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(rendered)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _assert_storage_admitted() -> dict[str, Any]:
    checker = ROOT / "tools" / "check_wrench_storage_budget.py"
    completed = subprocess.run(
        [sys.executable, str(checker), "status"], cwd=ROOT, capture_output=True,
        text=True, timeout=60, check=True,
    )
    report = json.loads(completed.stdout)
    reservation = f"{JOB_ID}"
    if (report.get("status") != "WITHIN_LIMIT" or report.get("errors") or
            reservation not in report.get("reservations", []) or
            report.get("projected_bytes", report["limit_bytes"]) >= report["limit_bytes"]):
        raise base.ChallengeError("storage_budget_reservation_or_headroom_lost")
    return report


def _summaries(results: list[dict[str, Any]]) -> dict[str, dict[str, int | bool]]:
    output = {}
    for class_name in CLASSES:
        rows = [row for row in results if row.get("class") == class_name]
        completed = sum(row.get("status") == "completed" for row in rows)
        passed = sum(row.get("score", {}).get("case_pass") is True for row in rows)
        output[class_name] = {
            "cases": len(rows),
            "completed": completed,
            "exact_answers": sum(row.get("score", {}).get("answer_exact") is True for row in rows),
            "grounded_evidence": sum(row.get("score", {}).get("evidence_grounded") is True for row in rows),
            "correct_abstentions": sum(row.get("score", {}).get("abstention_correct") is True for row in rows),
            "wrong_or_unresolved": len(rows) - passed,
            "class_pass": bool(rows) and len(rows) == CLASSES[class_name] and passed == len(rows),
        }
    return output


def _record_progress_totals(report: dict[str, Any]) -> None:
    rows = report["results"]
    accounting = [row.get("token_accounting") for row in rows if type(row.get("token_accounting")) is dict]
    report["completed_cases"] = sum(row.get("status") == "completed" for row in rows)
    report["attempted_cases"] = sum(row.get("status") in {"running", "completed", "failed"} for row in rows)
    report["local_tokens"] = {
        "prompt": sum(int(call.get("input_tokens", 0)) for call in accounting),
        "completion": sum(int(call.get("output_tokens") if type(call.get("output_tokens")) is int
                               else call.get("output_tokens_observed_before_failure", 0)) for call in accounting),
    }


def _load_cases() -> tuple[list[dict[str, Any]], str]:
    raw = MANIFEST.read_bytes()
    manifest = json.loads(raw.decode("utf-8"))
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise base.ChallengeError("fixture_hash_mismatch")
    if manifest.get("schema") != "wrench.local_prompt_only_work.v1" or type(manifest.get("cases")) is not list:
        raise base.ChallengeError("fixture_schema_mismatch")
    rows = manifest["cases"]
    ids = [row.get("id") for row in rows]
    if set(ids) != EXPECTED_CASES or len(ids) != len(EXPECTED_CASES):
        raise base.ChallengeError("fixture_case_set_mismatch")
    counts = {name: sum(row.get("class") == name for row in rows) for name in CLASSES}
    if counts != CLASSES:
        raise base.ChallengeError("fixture_class_counts_mismatch")
    for row in rows:
        if set(row) != {"id", "class", "prompt", "expected"}:
            raise base.ChallengeError("fixture_case_fields_mismatch")
        expected = row["expected"]
        if set(expected) != {"status", "answer", "evidence", "reason"}:
            raise base.ChallengeError("fixture_oracle_fields_mismatch")
        if expected["status"] == "known":
            evidence = expected["evidence"]
            expected_evidence_count = 2 if row["class"] == "snippet_function_localization" else 1
            if type(evidence) is not list or len(evidence) != expected_evidence_count:
                raise base.ChallengeError("fixture_known_evidence_invalid")
            for item in evidence:
                if type(item) is not dict or set(item) != {"line", "quote"} or type(item["line"]) is not int or type(item["quote"]) is not str:
                    raise base.ChallengeError("fixture_known_evidence_invalid")
                matching = [line for line in row["prompt"].splitlines() if line.startswith(f"{item['line']}|")]
                if len(matching) != 1 or matching[0][len(str(item["line"])) + 1:] != item["quote"]:
                    raise base.ChallengeError("fixture_source_oracle_mismatch")
            _validate_semantic_oracle(row)
        elif expected["status"] != "unknown" or expected["answer"] is not None or expected["evidence"] is not None or type(expected["reason"]) is not str or expected["reason"] not in {"not_present", "ambiguous"}:
            raise base.ChallengeError("fixture_unknown_oracle_invalid")
        else:
            _validate_semantic_oracle(row)
    return rows, hashlib.sha256(raw).hexdigest()


def _validate_semantic_oracle(row: dict[str, Any]) -> None:
    prompt = row["prompt"]
    expected = row["expected"]
    numbered = []
    for raw_line in prompt.splitlines():
        match = re.fullmatch(r"(\d+)\|(.*)", raw_line)
        if match:
            numbered.append((int(match.group(1)), match.group(2)))
    evidence = expected["evidence"]
    if row["class"] == "log_type_mapping":
        mapping = {"TimeoutError": "timeout", "PermissionError": "permission", "TypeError": "type", "ValueError": "value"}
        matches = [(line_no, line, mapping[name]) for line_no, line in numbered
                   for name in mapping if line.startswith(name + ":")]
        if expected["status"] == "known":
            if len(matches) != 1 or expected["answer"] != matches[0][2] or evidence[0] != {"line": matches[0][0], "quote": matches[0][1]}:
                raise base.ChallengeError("fixture_log_oracle_mismatch")
        elif len(matches) == 0 and expected["reason"] != "not_present" or len(matches) > 1 and expected["reason"] != "ambiguous" or len(matches) == 1:
            raise base.ChallengeError("fixture_log_abstention_mismatch")
    elif row["class"] == "config_value_extraction":
        question = re.search(r"value of `([^`]+)`", prompt)
        if question is None:
            raise base.ChallengeError("fixture_config_query_missing")
        key = question.group(1)
        matches = [(line_no, line, entry.group(2).strip().strip('"\'`')) for line_no, line in numbered
                   for entry in [re.fullmatch(r"\s*([^:=\s]+)\s*[:=]\s*(.*?)\s*", line)]
                   if entry and entry.group(1) == key and entry.group(2)]
        if expected["status"] == "known":
            if len(matches) != 1 or expected["answer"] != matches[0][2] or evidence != [{"line": matches[0][0], "quote": matches[0][1]}]:
                raise base.ChallengeError("fixture_config_oracle_mismatch")
        elif len(matches) == 0 and expected["reason"] != "not_present" or len(matches) > 1 and expected["reason"] != "ambiguous" or len(matches) == 1:
            raise base.ChallengeError("fixture_config_abstention_mismatch")
    elif row["class"] == "snippet_function_localization":
        query = re.search(r"reads `([^`]+)`", prompt)
        if query is None:
            raise base.ChallengeError("fixture_localization_query_missing")
        target = query.group(1)
        current_name = None
        current_def: tuple[int, str] | None = None
        matches: list[tuple[str, int, str, int, str]] = []
        for line_no, line in numbered:
            definition = re.match(r"\s*def\s+([A-Za-z_]\w*)\s*\(", line)
            if definition:
                current_name = definition.group(1)
                current_def = (line_no, line)
            elif target in line and current_name is not None and current_def is not None:
                matches.append((current_name, current_def[0], current_def[1], line_no, line))
        functions = {item[0] for item in matches}
        if expected["status"] == "known":
            match = matches[0] if len(functions) == 1 and matches else None
            wanted_evidence = ([{"line": match[1], "quote": match[2]}, {"line": match[3], "quote": match[4]}] if match else None)
            if match is None or expected["answer"] != match[0] or evidence != wanted_evidence:
                raise base.ChallengeError("fixture_localization_oracle_mismatch")
        elif len(functions) == 0 and expected["reason"] != "not_present" or len(functions) > 1 and expected["reason"] != "ambiguous" or len(functions) == 1:
            raise base.ChallengeError("fixture_localization_abstention_mismatch")
    else:
        raise base.ChallengeError("fixture_class_unrecognized")


def _score(raw: str, expected: dict[str, Any], prompt: str) -> dict[str, Any]:
    try:
        parsed = base._strict_json(raw)
    except base.ChallengeError:
        return {"valid_schema": False, "answer_exact": False, "evidence_grounded": False,
                "abstention_correct": False, "case_pass": False, "failure": "invalid_json"}
    if type(parsed) is not dict or set(parsed) != {"status", "answer", "evidence", "reason"}:
        return {"valid_schema": False, "answer_exact": False, "evidence_grounded": False,
                "abstention_correct": False, "case_pass": False, "failure": "invalid_schema"}
    valid_schema = (
        (parsed.get("status") == "known" and type(parsed.get("answer")) is str and
         type(parsed.get("evidence")) is list and len(parsed["evidence"]) in {1, 2} and
         all(type(item) is dict and set(item) == {"line", "quote"} and type(item.get("line")) is int and type(item.get("quote")) is str for item in parsed["evidence"]) and
         parsed.get("reason") is None)
        or
        (parsed.get("status") == "unknown" and parsed.get("answer") is None and
         parsed.get("evidence") is None and type(parsed.get("reason")) is str and parsed.get("reason") in {"not_present", "ambiguous"})
    )
    answer_exact = parsed == expected
    evidence_grounded = False
    if parsed.get("status") == "known" and type(parsed.get("evidence")) is list:
        evidence_grounded = all(any(
            line.startswith(f"{evidence.get('line')}|") and line[len(str(evidence.get("line"))) + 1:] == evidence.get("quote")
            for line in prompt.splitlines()
        ) for evidence in parsed["evidence"])
    abstention_correct = expected["status"] == "unknown" and answer_exact
    case_pass = valid_schema and answer_exact and (
        evidence_grounded if expected["status"] == "known" else abstention_correct
    )
    return {"valid_schema": valid_schema, "answer_exact": answer_exact,
            "evidence_grounded": evidence_grounded, "abstention_correct": abstention_correct,
            "case_pass": case_pass, "failure": None if case_pass else "oracle_mismatch_or_ungrounded_evidence"}


def measure(model_path: Path, output: Path) -> int:
    if os.environ.get("WRENCH_SCREEN_SUPERVISED") != "1":
        raise base.ChallengeError("must_launch_through_hard_deadline_supervisor")
    output = base._ensure_output_in_data_root(output)
    if output.exists():
        raise FileExistsError("refusing to overwrite existing measurement receipt")
    model_path = base._require_under(model_path, base.WEIGHTS_ROOT, "model_path_must_be_under_approved_weights_root")
    cases, fixture_hash = _load_cases()
    report: dict[str, Any] = {
        "schema": "wrench.local_prompt_only_work_screen.v1",
        "job_id": JOB_ID, "nonce": NONCE,
        "run_status": "starting",
        "fixture_sha256": fixture_hash,
        "repo_head_at_run": _repo_head(),
        "model": {"name": "Qwen/Qwen3.5-0.8B", "revision": base.MODEL_REVISION},
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "supervisor_sha256": hashlib.sha256(SUPERVISOR.read_bytes()).hexdigest(),
        "base_runner_sha256": hashlib.sha256(Path(base.__file__).read_bytes()).hexdigest(),
        "serializer": base.SERIALIZER_ID,
        "settings": {"max_new_tokens": 192, "context_tokens": base.MAX_CONTEXT,
                     "timeout_seconds_per_case": base.MAX_SECONDS_PER_RESPONSE,
                     "hard_process_timeout_seconds": HARD_PROCESS_TIMEOUT_SECONDS,
                     "sampling": "greedy", "batch_size": 1, "retries": 0,
                     "tools_available": 0, "network": "offline_local_files_only", "training": False},
        "initial_resources": None,
        "results": [{"id": row["id"], "class": row["class"], "status": "not_run", "raw_response": None,
                     "token_accounting": None, "score": {"case_pass": False}} for row in cases],
        "frontier_token_savings_percent": None,
        "frontier_usage_pairs": 0,
        "provider_calls": 0,
        "training": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    _write_checkpoint(output, report)
    identity = base.verify_model_snapshot(model_path)
    report["model"].update(identity)
    first_sample = base.resource_snapshot()
    if not base.resource_reserve_ok(first_sample):
        raise base.ResourceReserveFailure("initial_resource_reserve_breached_or_unavailable")
    report["initial_resources"] = first_sample
    report["run_status"] = "runtime_loading"
    _write_checkpoint(output, report)
    last_storage_check = [time.monotonic()]

    def monitored_resources() -> dict[str, Any]:
        now = time.monotonic()
        if now - last_storage_check[0] >= 30:
            _assert_storage_admitted()
            last_storage_check[0] = time.monotonic()
        return base.resource_snapshot()

    model, tokenizer, runtime = base.load_with_resource_watchdog(
        model_path, report, output, monitored_resources,
        checkpoint_guard=_assert_storage_admitted,
    )
    report["runtime"] = runtime
    report["post_load_resources"] = base.resource_snapshot()
    if not base.resource_reserve_ok(report["post_load_resources"]):
        raise base.ResourceReserveFailure("resource_reserve_breached_after_model_load")
    report["run_status"] = "running"
    _write_checkpoint(output, report)
    completed = 0
    for index, case in enumerate(cases):
        sample = base.resource_snapshot()
        if not base.resource_reserve_ok(sample):
            raise base.ResourceReserveFailure("resource_reserve_breached_before_case")
        report["results"][index].update({"status": "running", "resource_before": sample})
        _write_checkpoint(output, report)
        transcript = base.Transcript(tokenizer, [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": case["prompt"]},
        ], resource_check=monitored_resources)
        started = time.monotonic()
        raw_response = None
        try:
            raw_response = transcript.generate(model, max_new_tokens=192)
            after_sample = monitored_resources()
            if not base.resource_reserve_ok(after_sample):
                raise base.ResourceReserveFailure("resource_reserve_breached_after_case")
        except Exception as exc:
            report["results"][index].update({
                "status": "failed", "failure": f"{type(exc).__name__}:{exc}",
                "raw_response": raw_response,
                "token_accounting": transcript.calls[0] if transcript.calls else None,
                "resource_after": base.resource_snapshot(),
            })
            report["run_status"] = "failed"
            report["status"] = "INCOMPLETE"
            _record_progress_totals(report)
            _write_checkpoint(output, report)
            return 2
        result = {
            "id": case["id"], "class": case["class"], "status": "completed",
            "raw_response": raw_response,
            "token_accounting": transcript.calls[0],
            "elapsed_seconds": round(time.monotonic() - started, 4),
            "resource_before": sample, "resource_after": after_sample,
            "score": _score(raw_response, case["expected"], case["prompt"]),
            "prohibited_actions": 0,
        }
        if result["elapsed_seconds"] > base.MAX_SECONDS_PER_RESPONSE:
            result["status"] = "failed"
            result["failure"] = "response_exceeded_60_second_generation_deadline"
            result["score"]["case_pass"] = False
        report["results"][index] = result
        completed += 1
        _write_checkpoint(output, report)
        if result["status"] == "failed":
            report["run_status"] = "failed"
            report["status"] = "FAIL_DIAGNOSTIC"
            _record_progress_totals(report)
            _write_checkpoint(output, report)
            return 2
    report["run_status"] = "completed"
    report["status"] = "PASS_DIAGNOSTIC" if all(row["score"]["case_pass"] for row in report["results"]) else "FAIL_DIAGNOSTIC"
    _record_progress_totals(report)
    _write_checkpoint(output, report)
    return 0 if report["status"] == "PASS_DIAGNOSTIC" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("WRENCH_SCREEN_SUPERVISED") != "1":
        print(json.dumps({"status": "BLOCKED", "reason": "must_launch_through_hard_deadline_supervisor"}))
        return 2
    try:
        return measure(args.model_path, args.output)
    except Exception as exc:
        print(json.dumps({"status": "FAILED_OR_INCOMPLETE", "error_type": type(exc).__name__, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
