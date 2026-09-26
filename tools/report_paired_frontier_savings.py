"""Summarize structurally validated paired frontier-token receipts.

Input is a JSON object with schema ``wrench.paired-frontier-savings-input.v1``,
a frozen ``comparison`` identity, and ``tasks``. Every task declares its
expected snapshot digest and pairs ``baseline`` and ``wrench`` E0 outcome
receipts, each represented as ``payload_json`` plus its SHA-256. Only token-
complete, exact-usage pairs with a nonzero baseline denominator enter token
arithmetic. Receipts may be incomplete solely because costs are unknown; all
other incomplete receipts remain excluded. Failed task outcomes remain in the
totals. This utility reports token arithmetic, not product utility or savings
claims; callers must supply an authorized, preregistered corpus. Per-task rows
use a SHA-256 reference instead of exposing the input task ID.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from wrench_harness.outcome_receipt import OutcomeReceipt, ReceiptStatus, validate_outcome_receipt


SCHEMA = "wrench.paired-frontier-savings-input.v1"
COMPARISON_FIELDS = {"protocol_id", "client_id", "frontier_model_id", "token_convention_id"}
ARMS = ("baseline", "wrench")


class InputError(ValueError):
    pass


def _nonempty_text(value: object) -> bool:
    return type(value) is str and 1 <= len(value) <= 256 and value.strip() == value


def _is_sha256(value: object) -> bool:
    return type(value) is str and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def _read_receipt(value: object, task_id: str, comparison: dict[str, str]) -> tuple[dict[str, Any] | None, str | None]:
    if type(value) is not dict or set(value) != {"comparison", "receipt"}:
        return None, "invalid_arm_record_shape"
    if type(value["comparison"]) is not dict or value["comparison"] != comparison:
        return None, "comparison_identity_mismatch"
    value = value["receipt"]
    if type(value) is not dict or set(value) != {"payload_json", "sha256"}:
        return None, "invalid_receipt_shape"
    if type(value["payload_json"]) is not str or type(value["sha256"]) is not str:
        return None, "invalid_receipt_shape"
    checked = validate_outcome_receipt(OutcomeReceipt(value["payload_json"], value["sha256"]))
    if checked.status is ReceiptStatus.INVALID:
        return None, "invalid_receipt_hash_or_schema"
    try:
        payload = json.loads(value["payload_json"])
    except (ValueError, TypeError):
        return None, "invalid_receipt_hash_or_schema"
    if payload.get("task_id") != task_id:
        return None, "receipt_task_id_mismatch"
    if checked.status is ReceiptStatus.INCOMPLETE:
        accounting = payload.get("accounting")
        if (
            payload.get("missing_fields") != ["costs"]
            or type(accounting) is not dict
            or accounting.get("token_count_status") != "exact"
            or accounting.get("cost_status") != "unknown"
        ):
            return payload, "incomplete_receipt"
    return payload, None


def _exact_frontier_counts(payload: dict[str, Any], token_convention_id: str) -> tuple[int, int] | str:
    accounting = payload["accounting"]
    if accounting["token_count_status"] != "exact":
        return "usage_not_exact"
    counter_id = accounting["frontier_token_counter_id"]
    if counter_id is not None and counter_id != token_convention_id:
        return "token_convention_mismatch"
    input_total = 0
    output_total = 0
    saw_frontier_call = False
    records = [
        (attempt, attempt["usage"])
        for attempt in payload["attempts"]
        if attempt["call_made"] is True
    ] + [
        (call, call["usage"])
        for call in payload["work_calls"]
        if call["route"] in {"frontier", "local"}
    ]
    for record, usage in records:
        if record["route"] != "frontier":
            continue
        saw_frontier_call = True
        if (
            usage["status"] != "exact"
            or type(usage["frontier_input_tokens"]) is not int
            or type(usage["frontier_output_tokens"]) is not int
            or usage["frontier_input_tokens"] < 0
            or usage["frontier_output_tokens"] < 0
            or usage["counter_id"] != token_convention_id
        ):
            return "frontier_call_usage_missing_or_mismatched"
        input_total += usage["frontier_input_tokens"]
        output_total += usage["frontier_output_tokens"]
    if not saw_frontier_call and accounting["frontier_tokens"] != 0:
        return "frontier_total_without_calls"
    if accounting["frontier_tokens"] != input_total + output_total:
        return "frontier_total_reconciliation_mismatch"
    return input_total, output_total


def _successful_pair_exclusion(payloads: dict[str, dict[str, Any]]) -> str | None:
    """Require both arms to complete with independently verified outcomes."""
    ineligible: list[str] = []
    for arm in ARMS:
        payload = payloads[arm]
        outcome = payload["outcome"]
        verifier = payload["verifier"]
        if (
            outcome["status"] != "completed"
            or outcome["provenance"] != "independently_verified"
            or verifier["result"] != "passed"
        ):
            ineligible.append(arm)
    return None if not ineligible else "+".join(ineligible) + "_arm_not_independently_verified_success"


def summarize(document: object) -> dict[str, Any]:
    """Validate supplied receipt pairs and report savings without raw IDs."""
    if type(document) is not dict or set(document) != {"schema", "comparison", "tasks"}:
        raise InputError("input_shape_invalid")
    if document["schema"] != SCHEMA:
        raise InputError("input_schema_unsupported")
    comparison = document["comparison"]
    if type(comparison) is not dict or set(comparison) != COMPARISON_FIELDS:
        raise InputError("comparison_identity_shape_invalid")
    if any(not _nonempty_text(comparison[name]) for name in COMPARISON_FIELDS):
        raise InputError("comparison_identity_invalid")
    tasks = document["tasks"]
    if type(tasks) is not list:
        raise InputError("tasks_must_be_array")
    task_ids: list[str] = []
    for task in tasks:
        if type(task) is not dict or set(task) != {"task_id", "snapshot_sha256", "baseline", "wrench"} or not _nonempty_text(task.get("task_id")):
            raise InputError("task_record_invalid")
        if not _is_sha256(task["snapshot_sha256"]):
            raise InputError("task_snapshot_sha256_invalid")
        task_ids.append(task["task_id"])
    if len(set(task_ids)) != len(task_ids):
        raise InputError("duplicate_task_id")

    excluded: Counter[str] = Counter()
    successful_excluded: Counter[str] = Counter()
    outcome_counts: dict[str, Counter[str]] = {arm: Counter() for arm in ARMS}
    valid_rows: list[tuple[int, int]] = []
    successful_rows: list[tuple[int, int]] = []
    task_rows: list[dict[str, Any]] = []
    sums = {"baseline": 0, "wrench": 0}
    cost_unknown_pair_count = 0
    for task in tasks:
        payloads: dict[str, dict[str, Any] | None] = {}
        errors: list[str] = []
        for arm in ARMS:
            payload, error = _read_receipt(task[arm], task["task_id"], comparison)
            payloads[arm] = payload
            if payload is not None:
                outcome_counts[arm][payload["outcome"]["status"]] += 1
            if error:
                errors.append(error)
        if (
            payloads["baseline"] is not None
            and payloads["wrench"] is not None
            and (
                payloads["baseline"]["snapshot_sha256"] != task["snapshot_sha256"]
                or payloads["wrench"]["snapshot_sha256"] != task["snapshot_sha256"]
            )
        ):
            excluded["task_snapshot_mismatch"] += 1
            successful_excluded["task_snapshot_mismatch"] += 1
            task_rows.append(_excluded_task_row(task["task_id"], "task_snapshot_mismatch"))
            continue
        if errors:
            # One pair is counted once, with a stable priority when both arms fail.
            reason = sorted(errors)[0]
            excluded[reason] += 1
            successful_excluded[reason] += 1
            task_rows.append(_excluded_task_row(task["task_id"], reason))
            continue
        counts: dict[str, tuple[int, int]] = {}
        for arm in ARMS:
            result = _exact_frontier_counts(payloads[arm], comparison["token_convention_id"])
            if type(result) is str:
                errors.append(result)
            else:
                counts[arm] = result
        if errors:
            reason = sorted(errors)[0]
            excluded[reason] += 1
            successful_excluded[reason] += 1
            task_rows.append(_excluded_task_row(task["task_id"], reason))
            continue
        baseline = sum(counts["baseline"])
        wrench = sum(counts["wrench"])
        if baseline == 0:
            excluded["zero_baseline_frontier_tokens"] += 1
            successful_excluded["zero_baseline_frontier_tokens"] += 1
            task_rows.append(_excluded_task_row(task["task_id"], "zero_baseline_frontier_tokens"))
            continue
        valid_rows.append((baseline, wrench))
        successful_exclusion_reason = _successful_pair_exclusion(payloads)
        if successful_exclusion_reason is None:
            successful_rows.append((baseline, wrench))
        else:
            successful_excluded[successful_exclusion_reason] += 1
        if any(payloads[arm]["accounting"]["cost_status"] == "unknown" for arm in ARMS):
            cost_unknown_pair_count += 1
        task_rows.append({
            "task_ref_sha256": hashlib.sha256(task["task_id"].encode("utf-8")).hexdigest(),
            "status": "valid",
            "baseline_frontier_tokens": baseline,
            "wrench_frontier_tokens": wrench,
            "savings_percent": round(100.0 * (1.0 - wrench / baseline), 6),
            "excluded_reason": None,
            "successful_task_eligible": successful_exclusion_reason is None,
            "successful_task_excluded_reason": successful_exclusion_reason,
        })
        sums["baseline"] += baseline
        sums["wrench"] += wrench

    pair_percentages = [100.0 * (1.0 - wrench / baseline) for baseline, wrench in valid_rows]
    successful_pair_percentages = [100.0 * (1.0 - wrench / baseline) for baseline, wrench in successful_rows]
    pair_count = len(valid_rows)
    successful_pair_count = len(successful_rows)
    successful_sums = {
        "baseline": sum(baseline for baseline, _ in successful_rows),
        "wrench": sum(wrench for _, wrench in successful_rows),
    }
    return {
        "schema": "wrench.paired-frontier-savings-report.v3",
        "comparison": dict(comparison),
        "input_task_count": len(tasks),
        "per_task": task_rows,
        "valid_pair_count": pair_count,
        "cost_unknown_valid_pair_count": cost_unknown_pair_count,
        "excluded_pair_count": sum(excluded.values()),
        "excluded_by_reason": dict(sorted(excluded.items())),
        "unresolved_or_excluded_pair_count": sum(excluded.values()),
        "unresolved_or_excluded_by_reason": dict(sorted(excluded.items())),
        "frontier_token_totals": {
            "baseline": sums["baseline"] if pair_count else None,
            "wrench": sums["wrench"] if pair_count else None,
        },
        "average_per_task_savings_percent": (
            round(sum(pair_percentages) / pair_count, 6) if pair_count else None
        ),
        "ratio_of_sums_savings_percent": (
            round(100.0 * (1.0 - sums["wrench"] / sums["baseline"]), 6) if pair_count else None
        ),
        "successful_pair_count": successful_pair_count,
        "excluded_from_successful_pairs_count": sum(successful_excluded.values()),
        "excluded_from_successful_pairs_by_reason": dict(sorted(successful_excluded.items())),
        "successful_frontier_token_totals": {
            "baseline": successful_sums["baseline"] if successful_pair_count else None,
            "wrench": successful_sums["wrench"] if successful_pair_count else None,
        },
        "average_per_successful_task_savings_percent": (
            round(sum(successful_pair_percentages) / successful_pair_count, 6)
            if successful_pair_count else None
        ),
        "ratio_of_sums_successful_task_savings_percent": (
            round(100.0 * (1.0 - successful_sums["wrench"] / successful_sums["baseline"]), 6)
            if successful_pair_count else None
        ),
        "task_outcome_counts_by_arm": {
            arm: dict(sorted(outcome_counts[arm].items())) for arm in ARMS
        },
        "metric_scope": "all exact paired frontier input+output tokens, including failures; diagnostic only",
        "successful_metric_scope": (
            "exact paired frontier input+output tokens where both receipt payloads "
            "declare completed, independently verified outcomes with passed verifiers"
        ),
    }


def _excluded_task_row(task_id: str, reason: str) -> dict[str, Any]:
    return {
        "task_ref_sha256": hashlib.sha256(task_id.encode("utf-8")).hexdigest(),
        "status": "excluded",
        "baseline_frontier_tokens": None,
        "wrench_frontier_tokens": None,
        "savings_percent": None,
        "excluded_reason": reason,
        "successful_task_eligible": False,
        "successful_task_excluded_reason": reason,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="authorized paired receipt JSON")
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.input.read_text(encoding="utf-8"))
        result = summarize(document)
    except (OSError, UnicodeError, json.JSONDecodeError, InputError) as exc:
        print(json.dumps({"schema": "wrench.paired-frontier-savings-report.v3", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
