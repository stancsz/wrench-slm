"""Convert bounded per-attempt usage ledgers into existing E0 receipts.

This offline adapter does not authenticate or collect telemetry. Its output is
still caller-supplied evidence and must be passed to the paired-savings
reporter, which owns receipt validation, exclusions, and savings arithmetic.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .outcome_receipt import (
    ReceiptStatus,
    build_outcome_receipt,
    validate_outcome_receipt,
)


LEDGER_SCHEMA = "wrench.frontier-attempt-ledger.v1"
PAIRED_INPUT_SCHEMA = "wrench.paired-frontier-savings-input.v1"
COMPARISON_FIELDS = frozenset({
    "protocol_id", "client_id", "frontier_model_id", "token_convention_id",
})
MAX_TASKS = 256
MAX_ATTEMPTS = 64
MAX_DOCUMENT_BYTES = 1024 * 1024
MAX_AUDIT_BYTES = 256 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class LedgerError(ValueError):
    """The supplied ledger cannot be safely converted."""


@dataclass(frozen=True)
class BridgeResult:
    """Reporter input plus per-arm audit statuses for this conversion."""

    paired_input: dict[str, Any]
    arm_audit: tuple[dict[str, str], ...]


def _is_id(value: object) -> bool:
    return type(value) is str and _ID.fullmatch(value) is not None


def _is_digest(value: object) -> bool:
    return type(value) is str and _SHA256.fullmatch(value) is not None


def _require_text(value: object, label: str) -> str:
    if not _is_id(value):
        raise LedgerError(f"{label}_invalid")
    return value


def _unknown_usage() -> dict[str, object]:
    return {
        "status": "unknown", "counter_id": None,
        "local_input_tokens": None, "local_output_tokens": None,
        "frontier_input_tokens": None, "frontier_output_tokens": None,
        "local_cost_microunits": None, "frontier_cost_microunits": None,
        "cost_status": "unknown",
    }


def _exact_frontier_usage(row: dict[str, object], convention: str) -> dict[str, object] | None:
    if set(row) != {
        "call_id", "status", "counter_id", "input_tokens", "output_tokens",
        "cost_status", "cost_microunits",
    }:
        return None
    input_count, output_count = row["input_tokens"], row["output_tokens"]
    cost = row["cost_microunits"]
    if (
        row["status"] != "exact"
        or row["counter_id"] != convention
        or type(input_count) is not int or input_count < 0
        or type(output_count) is not int or output_count < 0
        or row["cost_status"] != "known"
        or type(cost) is not int or cost < 0
    ):
        return None
    return {
        "status": "exact", "counter_id": convention,
        "local_input_tokens": 0, "local_output_tokens": 0,
        "frontier_input_tokens": input_count, "frontier_output_tokens": output_count,
        "local_cost_microunits": 0, "frontier_cost_microunits": cost,
        "cost_status": "known",
    }


def _arm_receipt(
    task_id: str,
    snapshot_sha256: str,
    comparison: dict[str, str],
    arm_name: str,
    arm: object,
) -> tuple[dict[str, object], dict[str, str]]:
    if type(arm) is not dict or set(arm) != {
        "route", "local_model_calls", "tool_calls", "verifier_calls",
        "run_id", "context_receipt_sha256", "outcome_status", "attempts", "usage_rows",
    }:
        raise LedgerError(f"{arm_name}_arm_shape_invalid")
    if arm["route"] != "frontier":
        raise LedgerError(f"{arm_name}_route_must_be_frontier_only")
    for category in ("local_model_calls", "tool_calls", "verifier_calls"):
        if type(arm[category]) is not int or arm[category] != 0:
            raise LedgerError(f"{arm_name}_{category}_must_be_explicit_zero")
    run_id = _require_text(arm["run_id"], f"{arm_name}_run_id")
    context_hash = arm["context_receipt_sha256"]
    if not _is_digest(context_hash):
        raise LedgerError(f"{arm_name}_context_receipt_sha256_invalid")
    outcome_status = arm["outcome_status"]
    if outcome_status not in {"completed", "failed", "partial"}:
        raise LedgerError(f"{arm_name}_outcome_status_invalid")

    attempts = arm["attempts"]
    usage_rows = arm["usage_rows"]
    if type(attempts) is not list or not 1 <= len(attempts) <= MAX_ATTEMPTS:
        raise LedgerError(f"{arm_name}_attempts_invalid")
    if type(usage_rows) is not list or len(usage_rows) > MAX_ATTEMPTS:
        raise LedgerError(f"{arm_name}_usage_rows_invalid")

    attempt_ids: list[str] = []
    normalized_attempts: list[dict[str, object]] = []
    for row in attempts:
        if type(row) is not dict or set(row) != {
            "attempt_id", "route", "result", "retry_of", "fallback",
        }:
            raise LedgerError(f"{arm_name}_attempt_row_invalid")
        attempt_id = _require_text(row["attempt_id"], f"{arm_name}_attempt_id")
        if row["route"] != "frontier":
            raise LedgerError(f"{arm_name}_attempt_route_must_be_frontier_only")
        if row["result"] not in {"success", "failed", "timeout", "cancelled"}:
            raise LedgerError(f"{arm_name}_attempt_result_invalid")
        retry_of = row["retry_of"]
        if retry_of is not None and not _is_id(retry_of):
            raise LedgerError(f"{arm_name}_retry_reference_invalid")
        if row["fallback"] is not False:
            raise LedgerError(f"{arm_name}_fallback_unsupported")
        attempt_ids.append(attempt_id)
        normalized_attempts.append({
            "attempt_id": attempt_id, "route": "frontier", "result": row["result"],
            "retry_of": retry_of, "fallback": row["fallback"], "call_made": True,
        })
    if len(set(attempt_ids)) != len(attempt_ids):
        raise LedgerError(f"{arm_name}_duplicate_attempt_id")

    usage_by_id: dict[str, dict[str, object]] = {}
    duplicate_usage = False
    malformed_usage = False
    for row in usage_rows:
        if type(row) is not dict or not _is_id(row.get("call_id")):
            malformed_usage = True
            continue
        call_id = row["call_id"]
        if call_id in usage_by_id:
            duplicate_usage = True
            continue
        usage_by_id[call_id] = row
    unmatched_ids = set(usage_by_id) - set(attempt_ids)
    missing_ids = set(attempt_ids) - set(usage_by_id)
    invalid_ids: set[str] = set()
    normalized_usage: dict[str, dict[str, object]] = {}
    for attempt_id in attempt_ids:
        row = usage_by_id.get(attempt_id)
        if row is None:
            continue
        exact = _exact_frontier_usage(row, comparison["token_convention_id"])
        if exact is None:
            invalid_ids.add(attempt_id)
        else:
            normalized_usage[attempt_id] = exact

    taints = []
    if duplicate_usage:
        taints.append("duplicate_usage_call_id")
    if unmatched_ids:
        taints.append("unmatched_usage_call_id")
    if malformed_usage:
        taints.append("malformed_usage_row")
    if missing_ids:
        taints.append("missing_usage_row")
    if invalid_ids:
        taints.append("non_exact_or_mismatched_usage")
    # Any incomplete arm becomes wholly unknown. Do not let a partial or
    # ambiguous telemetry join leave apparently reconciled totals behind.
    if taints:
        normalized_usage.clear()
        invalid_ids.update(attempt_ids)

    complete = not taints
    receipt_attempts = []
    total_input = total_output = total_cost = 0
    all_costs_known = True
    for attempt in normalized_attempts:
        attempt_id = attempt["attempt_id"]
        usage = normalized_usage.get(attempt_id, _unknown_usage())
        if usage["status"] == "exact":
            total_input += usage["frontier_input_tokens"] or 0
            total_output += usage["frontier_output_tokens"] or 0
            if usage["cost_status"] == "known":
                total_cost += usage["frontier_cost_microunits"] or 0
            else:
                all_costs_known = False
        else:
            all_costs_known = False
        receipt_attempts.append({**attempt, "usage": usage})

    accounting_exact = complete
    payload: dict[str, object] = {
        "schema": "wrench.e0.outcome-receipt.v1",
        "task_id": task_id,
        "run_id": run_id,
        "snapshot_sha256": snapshot_sha256,
        "context_receipt_sha256": context_hash,
        "selected_evidence_ids": [], "omitted_evidence_ids": [], "retrieval_misses": [],
        "actual_route": "frontier",
        "attempts": receipt_attempts, "work_calls": [],
        "verifier": {"identity": None, "result": "unknown", "evidence_ids": []},
        "outcome": {"status": outcome_status, "provenance": "user_reported", "evidence_ids": []},
        "correction_refs": [],
        "accounting": {
            "local_model_calls": 0, "frontier_model_calls": len(receipt_attempts),
            "retries": sum(row["retry_of"] is not None for row in receipt_attempts),
            "fallback_calls": sum(row["fallback"] is True for row in receipt_attempts),
            "verifier_calls": 0, "tool_calls": 0,
            "local_tokens": 0 if accounting_exact else None,
            "frontier_tokens": total_input + total_output if accounting_exact else None,
            "local_token_counter_id": None,
            "frontier_token_counter_id": (
                comparison["token_convention_id"]
                if accounting_exact or normalized_usage else None
            ),
            "token_count_status": "exact" if accounting_exact else "unknown",
            "local_cost_microunits": 0 if complete else None,
            "frontier_cost_microunits": total_cost if complete and all_costs_known else None,
            "cost_status": "known" if complete and all_costs_known else "unknown",
        },
        "completeness": "complete" if complete else "incomplete",
        "missing_fields": [] if complete else ["usage", "costs"],
    }
    result = build_outcome_receipt(payload)
    if result.status is ReceiptStatus.INVALID or result.receipt is None:
        raise LedgerError(f"{arm_name}_outcome_receipt_invalid:{','.join(result.errors)}")
    checked = validate_outcome_receipt(result.receipt)
    if checked.status is not (ReceiptStatus.VALID if complete else ReceiptStatus.INCOMPLETE):
        raise LedgerError(f"{arm_name}_outcome_receipt_validation_mismatch")
    record = {
        "comparison": dict(comparison),
        "receipt": {"payload_json": result.receipt.payload_json, "sha256": result.receipt.sha256},
    }
    return record, {"task_id": task_id, "arm": arm_name, "status": "complete" if complete else "incomplete", "reasons": ",".join(taints)}


def bridge(document: object) -> BridgeResult:
    """Convert a bounded attempt ledger to input accepted by the existing reporter."""
    if type(document) is not dict or set(document) != {"schema", "comparison", "tasks"}:
        raise LedgerError("ledger_shape_invalid")
    if document["schema"] != LEDGER_SCHEMA:
        raise LedgerError("ledger_schema_unsupported")
    comparison_value = document["comparison"]
    if type(comparison_value) is not dict or set(comparison_value) != COMPARISON_FIELDS:
        raise LedgerError("comparison_identity_shape_invalid")
    comparison = {key: _require_text(comparison_value[key], f"comparison_{key}") for key in sorted(COMPARISON_FIELDS)}
    tasks = document["tasks"]
    if type(tasks) is not list or len(tasks) > MAX_TASKS:
        raise LedgerError("task_count_invalid")
    seen_tasks: set[str] = set()
    paired_tasks = []
    audit = []
    for task in tasks:
        if type(task) is not dict or set(task) != {"task_id", "snapshot_sha256", "baseline", "wrench"}:
            raise LedgerError("task_record_invalid")
        task_id = _require_text(task["task_id"], "task_id")
        if task_id in seen_tasks:
            raise LedgerError("duplicate_task_id")
        seen_tasks.add(task_id)
        snapshot = task["snapshot_sha256"]
        if not _is_digest(snapshot):
            raise LedgerError("task_snapshot_sha256_invalid")
        baseline, baseline_audit = _arm_receipt(task_id, snapshot, comparison, "baseline", task["baseline"])
        wrench, wrench_audit = _arm_receipt(task_id, snapshot, comparison, "wrench", task["wrench"])
        paired_tasks.append({
            "task_id": task_id, "snapshot_sha256": snapshot,
            "baseline": baseline, "wrench": wrench,
        })
        audit.extend((baseline_audit, wrench_audit))
    return BridgeResult(
        {"schema": PAIRED_INPUT_SCHEMA, "comparison": comparison, "tasks": paired_tasks},
        tuple(audit),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path, help="offline exact per-attempt ledger JSON")
    args = parser.parse_args(argv)
    try:
        with args.ledger.open("rb") as stream:
            raw = stream.read(MAX_DOCUMENT_BYTES + 1)
        if len(raw) > MAX_DOCUMENT_BYTES:
            raise LedgerError("ledger_byte_limit_exceeded")
        document = json.loads(raw.decode("utf-8"))
        result = bridge(document)
    except (OSError, UnicodeError, json.JSONDecodeError, LedgerError) as exc:
        print(json.dumps({"schema": PAIRED_INPUT_SCHEMA, "error": str(exc)}, sort_keys=True))
        return 2
    paired_json = json.dumps(result.paired_input, sort_keys=True, separators=(",", ":"), allow_nan=False)
    audit_json = json.dumps({
        "schema": "wrench.frontier-attempt-ledger-bridge-audit.v1",
        "arms": list(result.arm_audit),
    }, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(audit_json.encode("utf-8")) > MAX_AUDIT_BYTES:
        print(json.dumps({"schema": PAIRED_INPUT_SCHEMA, "error": "audit_output_byte_limit_exceeded"}, sort_keys=True))
        return 2
    print(paired_json)
    print(audit_json, file=sys.stderr)
    return 0


__all__ = ["BridgeResult", "LEDGER_SCHEMA", "LedgerError", "bridge", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
