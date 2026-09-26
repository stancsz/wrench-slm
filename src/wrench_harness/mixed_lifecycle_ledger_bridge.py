"""Convert caller-supplied mixed-route ledgers to paired E0 receipt input.

This is an offline format adapter only. It cannot authenticate telemetry,
outcomes, task consent, or caller claims. Every result carries an explicit
``caller_supplied_untrusted`` audit marker.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .outcome_receipt import (
    MAX_ATTEMPTS as RECEIPT_MAX_ATTEMPTS,
    MAX_REFERENCES,
    ReceiptStatus,
    build_outcome_receipt,
    validate_outcome_receipt,
)


LEDGER_SCHEMA = "wrench.mixed-lifecycle-ledger.v1"
PAIRED_INPUT_SCHEMA = "wrench.paired-frontier-savings-input.v1"
COMPARISON_FIELDS = frozenset({
    "protocol_id", "client_id", "frontier_model_id", "token_convention_id",
})
MAX_TASKS = 256
MAX_ATTEMPTS = RECEIPT_MAX_ATTEMPTS
MAX_WORK_CALLS = MAX_REFERENCES
MAX_DOCUMENT_BYTES = 1024 * 1024
MAX_AUDIT_BYTES = 256 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_COUNT_MAX = 2**63 - 1


class LedgerError(ValueError):
    """The supplied mixed-route ledger cannot be safely converted."""


@dataclass(frozen=True)
class BridgeResult:
    paired_input: dict[str, Any]
    arm_audit: tuple[dict[str, str], ...]


def _is_id(value: object) -> bool:
    return type(value) is str and _ID.fullmatch(value) is not None


def _is_digest(value: object) -> bool:
    return type(value) is str and _SHA256.fullmatch(value) is not None


def _is_choice(value: object, choices: set[str] | frozenset[str]) -> bool:
    return type(value) is str and value in choices


def _bounded_json_size(value: object, limit: int) -> int:
    """Bound compact UTF-8 JSON bytes without first materializing the input."""
    active: set[int] = set()
    nodes = 0

    def add(total: int, amount: int) -> int:
        total += amount
        if total > limit:
            raise LedgerError("ledger_byte_limit_exceeded")
        return total

    def string_bytes(text: str) -> int:
        size = 2
        for char in text:
            code = ord(char)
            if char in {'"', "\\"}:
                size = add(size, 2)
            elif code < 0x20:
                size = add(size, 6)
            elif 0xD800 <= code <= 0xDFFF:
                raise LedgerError("ledger_not_json_serializable")
            else:
                size = add(size, len(char.encode("utf-8")))
        return size

    def visit(item: object, depth: int) -> int:
        nonlocal nodes
        nodes += 1
        if nodes > 100_000 or depth > 64:
            raise LedgerError("ledger_complexity_limit_exceeded")
        if item is None:
            return 4
        if type(item) is bool:
            return 4 if item else 5
        if type(item) is str:
            return string_bytes(item)
        if type(item) is int:
            if item.bit_length() > limit * 3:
                raise LedgerError("ledger_byte_limit_exceeded")
            try:
                return len(str(item))
            except (ValueError, OverflowError) as exc:
                raise LedgerError("ledger_not_json_serializable") from exc
        if type(item) is float:
            if item != item or item in (float("inf"), float("-inf")):
                raise LedgerError("ledger_not_json_serializable")
            return len(repr(item))
        if type(item) in (list, dict):
            identity = id(item)
            if identity in active:
                raise LedgerError("ledger_not_json_serializable")
            active.add(identity)
            try:
                if type(item) is list:
                    total = 2
                    for index, child in enumerate(item):
                        if index:
                            total = add(total, 1)
                        total = add(total, visit(child, depth + 1))
                    return total
                total = 2
                for index, (key, child) in enumerate(item.items()):
                    if type(key) is not str:
                        raise LedgerError("ledger_not_json_serializable")
                    if index:
                        total = add(total, 1)
                    total = add(total, string_bytes(key))
                    total = add(total, 1)
                    total = add(total, visit(child, depth + 1))
                return total
            finally:
                active.remove(identity)
        raise LedgerError("ledger_not_json_serializable")

    return visit(value, 0)


def _id(value: object, label: str) -> str:
    if not _is_id(value):
        raise LedgerError(f"{label}_invalid")
    return value


def _count(value: object) -> bool:
    return type(value) is int and 0 <= value <= _COUNT_MAX


def _unknown_usage() -> dict[str, object]:
    return {
        "status": "unknown", "counter_id": None,
        "local_input_tokens": None, "local_output_tokens": None,
        "frontier_input_tokens": None, "frontier_output_tokens": None,
        "local_cost_microunits": None, "frontier_cost_microunits": None,
        "cost_status": "unknown",
    }


def _not_applicable_usage() -> dict[str, object]:
    return {
        "status": "not_applicable", "counter_id": None,
        "local_input_tokens": 0, "local_output_tokens": 0,
        "frontier_input_tokens": 0, "frontier_output_tokens": 0,
        "local_cost_microunits": None, "frontier_cost_microunits": None,
        "cost_status": "unknown",
    }


def _normalize_usage(
    row: object, call_id: str, route: str, comparison: dict[str, str],
) -> tuple[dict[str, object] | None, str | None, str | None]:
    """Return normalized usage, token-taint reason, cost-taint reason."""
    fields = {
        "call_id", "route", "status", "counter_id", "input_tokens",
        "output_tokens", "cost_status", "cost_microunits",
    }
    if type(row) is not dict or set(row) != fields:
        return None, "usage_row_shape_invalid", "usage_row_shape_invalid"
    if row["call_id"] != call_id:
        return None, "usage_call_id_mismatch", "usage_call_id_mismatch"
    if row["route"] != route or not _is_choice(route, {"local", "frontier"}):
        return None, "usage_route_mismatch", "usage_route_mismatch"

    status = row["status"]
    counter_id = row["counter_id"]
    input_count, output_count = row["input_tokens"], row["output_tokens"]
    token_reason = None
    if _is_choice(status, {"exact", "estimated"}):
        if not _is_id(counter_id) or not _count(input_count) or not _count(output_count):
            token_reason = "token_usage_value_invalid"
        elif route == "frontier" and counter_id != comparison["token_convention_id"]:
            token_reason = "frontier_counter_mismatch"
    elif status == "unknown":
        if counter_id is not None or input_count is not None or output_count is not None:
            token_reason = "unknown_usage_must_be_null"
    else:
        token_reason = "token_usage_status_invalid"

    cost_status, cost = row["cost_status"], row["cost_microunits"]
    cost_reason = None
    if not ((cost_status == "known" and _count(cost)) or (cost_status == "unknown" and cost is None)):
        cost_reason = "cost_usage_invalid"

    if token_reason:
        return None, token_reason, cost_reason
    if status == "unknown":
        normalized = _unknown_usage()
        return normalized, None, cost_reason
    normalized = {
        "status": status,
        "counter_id": counter_id,
        "local_input_tokens": input_count if route == "local" else 0,
        "local_output_tokens": output_count if route == "local" else 0,
        "frontier_input_tokens": input_count if route == "frontier" else 0,
        "frontier_output_tokens": output_count if route == "frontier" else 0,
        "local_cost_microunits": cost if route == "local" else 0,
        "frontier_cost_microunits": cost if route == "frontier" else 0,
        "cost_status": cost_status if not cost_reason else "unknown",
    }
    if cost_reason or cost_status == "unknown":
        normalized["local_cost_microunits"] = None
        normalized["frontier_cost_microunits"] = None
    return normalized, None, cost_reason


def _require_refs(value: object, label: str, *, limit: int = MAX_REFERENCES) -> list[str]:
    if type(value) is not list or len(value) > limit or any(not _is_id(item) for item in value):
        raise LedgerError(f"{label}_invalid")
    if len(set(value)) != len(value):
        raise LedgerError(f"{label}_duplicate")
    return list(value)


def _arm_receipt(
    task_id: str, snapshot: str, comparison: dict[str, str], arm_name: str,
    arm: object,
) -> tuple[dict[str, object], dict[str, str]]:
    required = {
        "run_id", "session_id", "route", "context_receipt_sha256",
        "preparation_accounting_sha256", "selected_evidence_ids",
        "omitted_evidence_ids", "retrieval_misses", "post_task_evidence_refs",
        "correction_refs", "verifier", "outcome", "attempts", "work_calls",
        "usage_rows",
    }
    if type(arm) is not dict or set(arm) != required:
        raise LedgerError(f"{arm_name}_arm_shape_invalid")
    if not _is_choice(arm["route"], {"none", "local", "frontier", "mixed"}):
        raise LedgerError(f"{arm_name}_declared_route_invalid")
    run_id = _id(arm["run_id"], f"{arm_name}_run_id")
    session_id = arm["session_id"]
    if session_id is not None:
        session_id = _id(session_id, f"{arm_name}_session_id")
    for field in ("context_receipt_sha256", "preparation_accounting_sha256"):
        if not _is_digest(arm[field]):
            raise LedgerError(f"{arm_name}_{field}_invalid")

    selected = _require_refs(arm["selected_evidence_ids"], f"{arm_name}_selected_evidence_ids")
    omitted = _require_refs(arm["omitted_evidence_ids"], f"{arm_name}_omitted_evidence_ids")
    corrections = _require_refs(arm["correction_refs"], f"{arm_name}_correction_refs")
    if set(selected) & set(omitted):
        raise LedgerError(f"{arm_name}_selected_omitted_overlap")

    misses = arm["retrieval_misses"]
    if type(misses) is not list or len(misses) > MAX_REFERENCES:
        raise LedgerError(f"{arm_name}_retrieval_misses_invalid")
    miss_rows = []
    miss_ids: set[str] = set()
    for row in misses:
        if type(row) is not dict or set(row) != {"evidence_id", "status"}:
            raise LedgerError(f"{arm_name}_retrieval_miss_invalid")
        evidence_id = _id(row["evidence_id"], f"{arm_name}_retrieval_miss_id")
        if evidence_id not in omitted or evidence_id in miss_ids or not _is_choice(row["status"], {
            "missing", "stale", "unsafe", "unknown_snapshot", "unknown_source", "evicted",
        }):
            raise LedgerError(f"{arm_name}_retrieval_miss_value_invalid")
        miss_ids.add(evidence_id)
        miss_rows.append({"evidence_id": evidence_id, "status": row["status"]})

    post_refs = arm["post_task_evidence_refs"]
    if type(post_refs) is not list or len(post_refs) > MAX_REFERENCES:
        raise LedgerError(f"{arm_name}_post_task_evidence_refs_invalid")
    normalized_post_refs = []
    evidence_ids: set[str] = set()
    for row in post_refs:
        if type(row) is not dict or set(row) != {"evidence_id", "kind", "sha256"}:
            raise LedgerError(f"{arm_name}_post_task_evidence_ref_invalid")
        eid = _id(row["evidence_id"], f"{arm_name}_post_task_evidence_id")
        if eid in evidence_ids or not _is_choice(row["kind"], {"test_result", "diff", "review", "user_report", "other"}) or not _is_digest(row["sha256"]):
            raise LedgerError(f"{arm_name}_post_task_evidence_ref_value_invalid")
        evidence_ids.add(eid)
        normalized_post_refs.append(dict(row))
    if evidence_ids & (set(selected) | set(omitted)):
        raise LedgerError(f"{arm_name}_evidence_scope_overlap")

    verifier = arm["verifier"]
    outcome = arm["outcome"]
    if type(verifier) is not dict or set(verifier) != {"identity", "result", "evidence_ids"}:
        raise LedgerError(f"{arm_name}_verifier_shape_invalid")
    if verifier["identity"] is not None:
        _id(verifier["identity"], f"{arm_name}_verifier_identity")
    if not _is_choice(verifier["result"], {"passed", "failed", "inconclusive", "not_run", "unknown"}):
        raise LedgerError(f"{arm_name}_verifier_result_invalid")
    verifier_ids = _require_refs(verifier["evidence_ids"], f"{arm_name}_verifier_evidence_ids")
    if any(eid not in evidence_ids for eid in verifier_ids):
        raise LedgerError(f"{arm_name}_verifier_evidence_out_of_scope")
    if type(outcome) is not dict or set(outcome) != {"status", "provenance", "evidence_ids"}:
        raise LedgerError(f"{arm_name}_outcome_shape_invalid")
    if not _is_choice(outcome["status"], {"completed", "failed", "partial", "unknown"}) or not _is_choice(outcome["provenance"], {"user_reported", "independently_verified", "unknown"}):
        raise LedgerError(f"{arm_name}_outcome_value_invalid")
    outcome_ids = _require_refs(outcome["evidence_ids"], f"{arm_name}_outcome_evidence_ids")
    if any(eid not in evidence_ids for eid in outcome_ids):
        raise LedgerError(f"{arm_name}_outcome_evidence_out_of_scope")
    # The adapter receives caller-authored claims only. Preserve the declared
    # verifier metadata for audit, but never let this bridge elevate it into
    # verified-success eligibility for the paired reporter.
    normalized_outcome_provenance = outcome["provenance"]
    if normalized_outcome_provenance == "independently_verified":
        normalized_outcome_provenance = "user_reported"

    attempts = arm["attempts"]
    work_calls = arm["work_calls"]
    usage_rows = arm["usage_rows"]
    if type(attempts) is not list or len(attempts) > MAX_ATTEMPTS:
        raise LedgerError(f"{arm_name}_attempts_invalid")
    if type(work_calls) is not list or len(work_calls) > MAX_WORK_CALLS:
        raise LedgerError(f"{arm_name}_work_calls_invalid")
    if type(usage_rows) is not list or len(usage_rows) > MAX_ATTEMPTS + MAX_WORK_CALLS:
        raise LedgerError(f"{arm_name}_usage_rows_invalid")

    normalized_attempts: list[dict[str, object]] = []
    attempts_by_id: dict[str, dict[str, object]] = {}
    all_ids: set[str] = set()
    for raw in attempts:
        fields = {"attempt_id", "route", "result", "retry_of", "fallback", "call_made"}
        if type(raw) is not dict or set(raw) != fields:
            raise LedgerError(f"{arm_name}_attempt_row_invalid")
        aid = _id(raw["attempt_id"], f"{arm_name}_attempt_id")
        if aid in all_ids:
            raise LedgerError(f"{arm_name}_duplicate_call_id")
        if not _is_choice(raw["route"], {"none", "local", "frontier"}) or not _is_choice(raw["result"], {"success", "failed", "timeout", "cancelled", "not_run"}) or type(raw["fallback"]) is not bool or type(raw["call_made"]) is not bool:
            raise LedgerError(f"{arm_name}_attempt_value_invalid")
        if raw["route"] == "none" and raw["call_made"] or raw["route"] in {"local", "frontier"} and not raw["call_made"]:
            raise LedgerError(f"{arm_name}_attempt_call_route_mismatch")
        if raw["fallback"] and (not raw["call_made"] or raw["route"] == "none"):
            raise LedgerError(f"{arm_name}_fallback_without_model_call")
        retry_of = raw["retry_of"]
        if retry_of is not None:
            _id(retry_of, f"{arm_name}_retry_reference")
        row = {**raw, "attempt_id": aid}
        all_ids.add(aid)
        attempts_by_id[aid] = row
        normalized_attempts.append(row)
    for index, row in enumerate(normalized_attempts):
        retry_of = row["retry_of"]
        if retry_of is not None and (retry_of not in attempts_by_id or retry_of == row["attempt_id"] or retry_of not in {prior["attempt_id"] for prior in normalized_attempts[:index]} or not attempts_by_id[retry_of]["call_made"]):
            raise LedgerError(f"{arm_name}_retry_reference_invalid")

    normalized_work: list[dict[str, object]] = []
    for raw in work_calls:
        fields = {"call_id", "kind", "route", "result"}
        if type(raw) is not dict or set(raw) != fields:
            raise LedgerError(f"{arm_name}_work_call_row_invalid")
        cid = _id(raw["call_id"], f"{arm_name}_work_call_id")
        if cid in all_ids:
            raise LedgerError(f"{arm_name}_duplicate_call_id")
        if not _is_choice(raw["kind"], {"tool", "verifier"}) or not _is_choice(raw["route"], {"none", "local", "frontier"}) or not _is_choice(raw["result"], {"success", "failed", "timeout", "cancelled", "not_run", "passed", "inconclusive"}):
            raise LedgerError(f"{arm_name}_work_call_value_invalid")
        if raw["result"] == "not_run" and raw["route"] in {"local", "frontier"}:
            raise LedgerError(f"{arm_name}_work_call_not_run_with_model_route")
        all_ids.add(cid)
        normalized_work.append({**raw, "call_id": cid})

    # Join only one usage row per actual model call. Any ambiguous or partial
    # join taints every token count on this arm, never a partial sum.
    expected = {
        row["attempt_id"]: row["route"] for row in normalized_attempts if row["call_made"]
    }
    expected.update({row["call_id"]: row["route"] for row in normalized_work if row["route"] in {"local", "frontier"}})
    observed_routes = {route for route in expected.values()}
    derived_route = "mixed" if len(observed_routes) == 2 else next(iter(observed_routes), "none")
    if arm["route"] != derived_route:
        raise LedgerError(f"{arm_name}_declared_route_mismatch")
    usage_by_id: dict[str, object] = {}
    reasons: list[str] = []
    token_taint_reasons: list[str] = []
    for raw in usage_rows:
        if type(raw) is not dict or not _is_id(raw.get("call_id")):
            reasons.append("usage_row_shape_invalid")
            token_taint_reasons.append("usage_row_shape_invalid")
            continue
        cid = raw["call_id"]
        if cid in usage_by_id:
            reasons.append("duplicate_usage_call_id")
            token_taint_reasons.append("duplicate_usage_call_id")
        else:
            usage_by_id[cid] = raw
    if set(usage_by_id) - set(expected):
        reasons.append("unmatched_usage_call_id")
        token_taint_reasons.append("unmatched_usage_call_id")
    if set(expected) - set(usage_by_id):
        reasons.append("missing_usage_row")
        token_taint_reasons.append("missing_usage_row")
    if not expected and usage_by_id:
        raise LedgerError(f"{arm_name}_usage_rows_without_model_calls")

    normalized_usage: dict[str, dict[str, object]] = {}
    counter_by_route: dict[str, set[str]] = {"local": set(), "frontier": set()}
    cost_unknown = False
    for cid, route in expected.items():
        if cid not in usage_by_id:
            continue
        usage, token_error, cost_error = _normalize_usage(usage_by_id[cid], cid, route, comparison)
        if token_error:
            reasons.append(token_error)
            token_taint_reasons.append(token_error)
        if cost_error:
            reasons.append(cost_error)
            cost_unknown = True
        if usage is not None:
            normalized_usage[cid] = usage
            if usage["status"] in {"exact", "estimated"}:
                counter_by_route[route].add(usage["counter_id"])
            if usage["cost_status"] == "unknown":
                cost_unknown = True
    if any(len(values) > 1 for values in counter_by_route.values()):
        reasons.append("route_counter_identity_conflict")
        token_taint_reasons.append("route_counter_identity_conflict")
    if counter_by_route["frontier"] and counter_by_route["frontier"] != {comparison["token_convention_id"]}:
        reasons.append("frontier_counter_mismatch")
        token_taint_reasons.append("frontier_counter_mismatch")

    token_tainted = bool(token_taint_reasons)
    if any(
        raw.get("status") == "unknown" for raw in usage_by_id.values() if type(raw) is dict
    ):
        reasons.append("explicit_unknown_usage")
        token_taint_reasons.append("explicit_unknown_usage")
        token_tainted = True
    # A route identity conflict is also all-or-nothing. Costs remain known only
    # if every expected model call had a valid known cost.
    if len(normalized_usage) != len(expected):
        cost_unknown = True
    if not expected:
        cost_unknown = False
    if token_tainted:
        normalized_usage = {cid: _unknown_usage() for cid in expected}
        # If telemetry cannot join, route totals are not meaningful. Leave all
        # costs unknown too rather than retaining an apparently reconciled sum.
        cost_unknown = bool(expected)

    receipt_attempts = []
    for row in normalized_attempts:
        if row["call_made"]:
            usage = normalized_usage.get(row["attempt_id"], _unknown_usage())
        else:
            usage = _not_applicable_usage()
        receipt_attempts.append({**row, "usage": usage})
    receipt_work = []
    for row in normalized_work:
        if row["route"] in {"local", "frontier"}:
            usage = normalized_usage.get(row["call_id"], _unknown_usage())
        else:
            usage = _not_applicable_usage()
        receipt_work.append({**row, "usage": usage})

    all_model_rows = [
        (row["route"], row["usage"])
        for row in receipt_attempts if row["call_made"]
    ] + [
        (row["route"], row["usage"])
        for row in receipt_work if row["route"] in {"local", "frontier"}
    ]
    actual_routes = {route for route, _ in all_model_rows}
    actual_route = "mixed" if len(actual_routes) == 2 else next(iter(actual_routes), "none")
    token_statuses = {usage["status"] for _, usage in all_model_rows}
    token_status = (
        "unknown" if token_tainted or "unknown" in token_statuses else
        "estimated" if "estimated" in token_statuses else
        "exact" if all_model_rows else "not_applicable"
    )
    local_counters = counter_by_route["local"]
    frontier_counters = counter_by_route["frontier"]
    if token_status == "unknown":
        local_counter = frontier_counter = None
        local_tokens = frontier_tokens = None
    else:
        local_counter = next(iter(local_counters), None)
        frontier_counter = next(iter(frontier_counters), None)
        local_tokens = sum((usage.get("local_input_tokens") or 0) + (usage.get("local_output_tokens") or 0) for _, usage in all_model_rows)
        frontier_tokens = sum((usage.get("frontier_input_tokens") or 0) + (usage.get("frontier_output_tokens") or 0) for _, usage in all_model_rows)

    local_cost_known = frontier_cost_known = True
    local_cost = frontier_cost = 0
    for _, usage in all_model_rows:
        if usage["cost_status"] != "known":
            local_cost_known = frontier_cost_known = False
        else:
            local_cost += usage["local_cost_microunits"] or 0
            frontier_cost += usage["frontier_cost_microunits"] or 0
    cost_status = "known" if local_cost_known and frontier_cost_known else "unknown"
    if cost_status == "unknown":
        local_cost_value = frontier_cost_value = None
    else:
        local_cost_value, frontier_cost_value = local_cost, frontier_cost

    token_complete = token_status in {"exact", "estimated", "not_applicable"}
    complete = token_complete and cost_status == "known" and outcome["status"] != "unknown" and outcome["provenance"] != "unknown" and session_id is not None
    missing = []
    if session_id is None:
        missing.append("session_id")
    if outcome["status"] == "unknown" or outcome["provenance"] == "unknown":
        missing.append("outcome")
    if token_status == "unknown":
        missing.append("usage")
    if cost_status == "unknown":
        missing.append("costs")
    payload: dict[str, object] = {
        "schema": "wrench.e0.outcome-receipt.v3",
        "task_id": task_id, "run_id": run_id,
        "session_id": session_id,
        "snapshot_sha256": snapshot,
        "context_receipt_sha256": arm["context_receipt_sha256"],
        "preparation_accounting_sha256": arm["preparation_accounting_sha256"],
        "post_task_evidence_refs": normalized_post_refs,
        "selected_evidence_ids": selected,
        "omitted_evidence_ids": omitted,
        "retrieval_misses": miss_rows,
        "actual_route": actual_route,
        "attempts": receipt_attempts,
        "work_calls": receipt_work,
        "verifier": {"identity": verifier["identity"], "result": verifier["result"], "evidence_ids": verifier_ids},
        "outcome": {"status": outcome["status"], "provenance": normalized_outcome_provenance, "evidence_ids": outcome_ids},
        "correction_refs": corrections,
        "accounting": {
            "local_model_calls": sum(route == "local" for route, _ in all_model_rows),
            "frontier_model_calls": sum(route == "frontier" for route, _ in all_model_rows),
            "retries": sum(row["retry_of"] is not None for row in receipt_attempts),
            "fallback_calls": sum(row["fallback"] is True and row["call_made"] is True for row in receipt_attempts),
            "verifier_calls": sum(row["kind"] == "verifier" for row in receipt_work),
            "tool_calls": sum(row["kind"] == "tool" for row in receipt_work),
            "local_tokens": local_tokens, "frontier_tokens": frontier_tokens,
            "local_token_counter_id": local_counter, "frontier_token_counter_id": frontier_counter,
            "token_count_status": token_status,
            "local_cost_microunits": local_cost_value,
            "frontier_cost_microunits": frontier_cost_value,
            "cost_status": cost_status,
        },
        "completeness": "complete" if complete else "incomplete",
        "missing_fields": missing,
    }
    built = build_outcome_receipt(payload)
    if built.status is ReceiptStatus.INVALID or built.receipt is None:
        raise LedgerError(f"{arm_name}_outcome_receipt_invalid:{','.join(built.errors)}")
    checked = validate_outcome_receipt(built.receipt)
    if checked.status is not (ReceiptStatus.VALID if complete else ReceiptStatus.INCOMPLETE):
        raise LedgerError(f"{arm_name}_receipt_validation_mismatch")
    record = {
        "comparison": dict(comparison),
        "receipt": {"payload_json": built.receipt.payload_json, "sha256": built.receipt.sha256},
    }
    audit_reasons = sorted(set(reasons))
    if outcome["provenance"] == "independently_verified":
        audit_reasons.append("claimed_independent_verification_downgraded_untrusted")
    if cost_status == "unknown" and "cost_unknown" not in audit_reasons:
        audit_reasons.append("cost_unknown")
    status = "complete" if complete else "token_complete_cost_unknown" if token_complete and cost_status == "unknown" else "incomplete"
    return record, {
        "task_id": task_id, "arm": arm_name, "status": status,
        "reasons": ",".join(audit_reasons),
        "evidence_trust": "caller_supplied_untrusted",
    }


def bridge(document: object) -> BridgeResult:
    """Convert a bounded mixed lifecycle ledger to paired reporter input."""
    try:
        _bounded_json_size(document, MAX_DOCUMENT_BYTES)
        encoded = json.dumps(document, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except LedgerError:
        raise
    except (TypeError, ValueError, OverflowError, RecursionError, UnicodeError) as exc:
        raise LedgerError("ledger_not_json_serializable") from exc
    if len(encoded) > MAX_DOCUMENT_BYTES:
        raise LedgerError("ledger_byte_limit_exceeded")
    if type(document) is not dict or set(document) != {"schema", "comparison", "tasks"}:
        raise LedgerError("ledger_shape_invalid")
    if document["schema"] != LEDGER_SCHEMA:
        raise LedgerError("ledger_schema_unsupported")
    comparison_value = document["comparison"]
    if type(comparison_value) is not dict or set(comparison_value) != COMPARISON_FIELDS:
        raise LedgerError("comparison_identity_shape_invalid")
    comparison = {key: _id(comparison_value[key], f"comparison_{key}") for key in sorted(COMPARISON_FIELDS)}
    tasks = document["tasks"]
    if type(tasks) is not list or len(tasks) > MAX_TASKS:
        raise LedgerError("task_count_invalid")
    seen: set[str] = set()
    paired_tasks = []
    audit = []
    for task in tasks:
        if type(task) is not dict or set(task) != {"task_id", "snapshot_sha256", "baseline", "wrench"}:
            raise LedgerError("task_record_invalid")
        task_id = _id(task["task_id"], "task_id")
        if task_id in seen:
            raise LedgerError("duplicate_task_id")
        seen.add(task_id)
        snapshot = task["snapshot_sha256"]
        if not _is_digest(snapshot):
            raise LedgerError("task_snapshot_sha256_invalid")
        baseline, baseline_audit = _arm_receipt(task_id, snapshot, comparison, "baseline", task["baseline"])
        wrench, wrench_audit = _arm_receipt(task_id, snapshot, comparison, "wrench", task["wrench"])
        paired_tasks.append({"task_id": task_id, "snapshot_sha256": snapshot, "baseline": baseline, "wrench": wrench})
        audit.extend((baseline_audit, wrench_audit))
    audit_bytes = len(json.dumps(audit, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    if audit_bytes > MAX_AUDIT_BYTES:
        raise LedgerError("audit_output_byte_limit_exceeded")
    return BridgeResult({"schema": PAIRED_INPUT_SCHEMA, "comparison": comparison, "tasks": paired_tasks}, tuple(audit))


__all__ = ["BridgeResult", "LEDGER_SCHEMA", "LedgerError", "bridge"]
