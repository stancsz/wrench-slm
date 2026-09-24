"""Bounded reference-only E0 outcome receipt contract.

This module validates supplied metadata only. It never reads source or prompt
content, persists receipts, calls a model/provider, or asserts task truth.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


MAX_RECEIPT_BYTES = 64 * 1024
MAX_ATTEMPTS = 64
MAX_REFERENCES = 256
MAX_ID_CHARS = 256
MAX_TEXT_CHARS = 512
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_OPAQUE_V2_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_HEX = frozenset("0123456789abcdef")


class ReceiptStatus(str, Enum):
    VALID = "valid"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


@dataclass(frozen=True)
class OutcomeReceipt:
    """Canonical bounded serialized receipt. The payload contains references only."""

    payload_json: str
    sha256: str


@dataclass(frozen=True)
class ReceiptResult:
    status: ReceiptStatus
    receipt: OutcomeReceipt | None
    errors: tuple[str, ...] = ()


def _is_id(value: object) -> bool:
    return type(value) is str and 1 <= len(value) <= MAX_ID_CHARS and all(ord(ch) >= 0x20 and ord(ch) != 0x7f for ch in value)


def _is_opaque_v2_id(value: object) -> bool:
    """Accept compact identifier syntax for caller-supplied v2 identities."""
    return type(value) is str and _OPAQUE_V2_ID.fullmatch(value) is not None


def _is_digest(value: object, *, optional: bool = False) -> bool:
    return optional and value is None or type(value) is str and len(value) == 64 and all(c in _HEX for c in value)


def _serialized_size(value: object, cap: int) -> int:
    """Bound traversal and exact JSON output size before encoder allocation."""
    nodes = 0
    active: set[int] = set()
    total = 0

    def add(size: int) -> None:
        nonlocal total
        total += size
        if total > cap:
            raise OverflowError("serialized_receipt_too_large")

    def visit(item: object, depth: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > 20000 or depth > 24:
            raise ValueError("receipt_shape_limit")
        if item is None:
            add(4)
        elif type(item) is bool:
            add(4 if item else 5)
        elif type(item) is int:
            if item.bit_length() > 64:
                raise ValueError("integer_out_of_range")
            add(len(str(item)))
        elif type(item) is float:
            if not math.isfinite(item):
                raise ValueError("nonfinite_number")
            add(len(json.dumps(item, allow_nan=False, separators=(",", ":"))))
        elif type(item) is str:
            if len(item) > cap:
                raise OverflowError("serialized_receipt_too_large")
            size = 2
            for char in item:
                point = ord(char)
                if 0xD800 <= point <= 0xDFFF:
                    raise ValueError("invalid_unicode")
                if char in ('"', "\\") or point in (8, 9, 10, 12, 13):
                    size += 2
                elif point < 0x20:
                    size += 6
                elif point <= 0x7f:
                    size += 1
                elif point <= 0x7ff:
                    size += 2
                elif point <= 0xffff:
                    size += 3
                else:
                    size += 4
                if size + total > cap:
                    raise OverflowError("serialized_receipt_too_large")
            add(size)
        elif type(item) in (dict, list, tuple):
            ident = id(item)
            if ident in active:
                raise ValueError("receipt_cycle")
            if len(item) > 4096:
                raise ValueError("receipt_collection_limit")
            active.add(ident)
            try:
                add(2)
                if type(item) is dict:
                    first = True
                    for key, nested in item.items():
                        if type(key) is not str:
                            raise ValueError("receipt_key_must_be_string")
                        if not first:
                            add(1)
                        first = False
                        visit(key, depth + 1)
                        add(1)
                        visit(nested, depth + 1)
                else:
                    first = True
                    for nested in item:
                        if not first:
                            add(1)
                        first = False
                        visit(nested, depth + 1)
            finally:
                active.remove(ident)
        else:
            raise ValueError("receipt_contains_unsupported_type")

    visit(value, 0)
    return total


def _canonical_json(value: dict[str, Any]) -> str:
    # Copy first under bounds, then measure and encode only the owned snapshot.
    # Later caller mutations cannot invalidate the measured object.
    owned = _snapshot_owned(value, MAX_RECEIPT_BYTES)
    _serialized_size(owned, MAX_RECEIPT_BYTES)
    encoded = json.dumps(owned, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(encoded.encode("utf-8")) > MAX_RECEIPT_BYTES:
        raise OverflowError("serialized_receipt_too_large")
    return encoded


def _snapshot_dict_items(value: dict[str, Any]):
    """Iterator seam for fail-closed detection of concurrent dict mutation."""
    return value.items()


def _snapshot_owned(value: object, cap: int) -> object:
    nodes = 0
    string_bytes = 0
    active: set[int] = set()

    def clone(item: object, depth: int) -> object:
        nonlocal nodes, string_bytes
        nodes += 1
        if nodes > 20000 or depth > 24:
            raise ValueError("receipt_shape_limit")
        if item is None or type(item) in (bool, int, float):
            return item
        if type(item) is str:
            if len(item) > cap:
                raise OverflowError("serialized_receipt_too_large")
            for char in item:
                point = ord(char)
                if 0xD800 <= point <= 0xDFFF:
                    raise ValueError("invalid_unicode")
                string_bytes += 1 if point <= 0x7f else 2 if point <= 0x7ff else 3 if point <= 0xffff else 4
                if string_bytes > cap:
                    raise OverflowError("serialized_receipt_too_large")
            return item
        if type(item) not in (dict, list, tuple):
            raise ValueError("receipt_contains_unsupported_type")
        identity = id(item)
        if identity in active:
            raise ValueError("receipt_cycle")
        if len(item) > 4096:
            raise ValueError("receipt_collection_limit")
        active.add(identity)
        try:
            if type(item) is dict:
                owned: dict[str, object] = {}
                try:
                    for key, nested in _snapshot_dict_items(item):
                        if type(key) is not str:
                            raise ValueError("receipt_key_must_be_string")
                        owned[clone(key, depth + 1)] = clone(nested, depth + 1)
                except RuntimeError as exc:
                    raise ValueError("receipt_mapping_mutated_during_snapshot") from exc
                return owned
            items = [clone(nested, depth + 1) for nested in item]
            return tuple(items) if type(item) is tuple else items
        finally:
            active.remove(identity)

    return clone(value, 0)


def _failures(payload: object) -> list[str]:
    errors: list[str] = []
    if type(payload) is not dict:
        return ["payload_must_be_builtin_object"]
    v1_fields = {
        "schema", "task_id", "run_id", "snapshot_sha256", "context_receipt_sha256",
        "selected_evidence_ids", "omitted_evidence_ids", "retrieval_misses", "actual_route",
        "attempts", "work_calls", "verifier", "outcome", "correction_refs", "accounting",
        "completeness", "missing_fields",
    }
    schema = payload.get("schema")
    if schema == "wrench.e0.outcome-receipt.v2":
        required = v1_fields | {
            "session_id", "preparation_accounting_sha256", "post_task_evidence_refs",
        }
    else:
        required = v1_fields
    if _contains_forbidden_key(payload):
        errors.append("forbidden_raw_content_key")
    if set(payload) != required:
        errors.append("top_level_fields_invalid")
        return errors
    if schema not in {"wrench.e0.outcome-receipt.v1", "wrench.e0.outcome-receipt.v2"}:
        errors.append("schema_unsupported")
    is_v2 = schema == "wrench.e0.outcome-receipt.v2"
    for key in ("task_id", "run_id"):
        if not (_is_opaque_v2_id(payload[key]) if is_v2 else _is_id(payload[key])):
            errors.append(f"{key}_invalid")
    for key in ("snapshot_sha256", "context_receipt_sha256"):
        if not _is_digest(payload[key], optional=True):
            errors.append(f"{key}_invalid")
    post_task_ids: set[str] = set()
    if is_v2:
        if payload["session_id"] is not None and not _is_opaque_v2_id(payload["session_id"]):
            errors.append("session_id_invalid")
        if not _is_digest(payload["preparation_accounting_sha256"]):
            errors.append("preparation_accounting_digest_invalid")
        post_task_refs = payload["post_task_evidence_refs"]
        if type(post_task_refs) is not list or len(post_task_refs) > MAX_REFERENCES:
            errors.append("post_task_evidence_refs_invalid")
            post_task_refs = []
        for reference in post_task_refs:
            if type(reference) is not dict or set(reference) != {"evidence_id", "kind", "sha256"}:
                errors.append("post_task_evidence_ref_shape_invalid")
                continue
            evidence_id = reference["evidence_id"]
            if not _is_opaque_v2_id(evidence_id):
                errors.append("post_task_evidence_ref_id_invalid")
            else:
                post_task_ids.add(evidence_id)
            if reference["kind"] not in {"test_result", "diff", "review", "user_report", "other"}:
                errors.append("post_task_evidence_ref_kind_invalid")
            if not _is_digest(reference["sha256"]):
                errors.append("post_task_evidence_ref_digest_invalid")
        if len(post_task_ids) != len(post_task_refs):
            errors.append("post_task_evidence_ref_duplicate_or_invalid_id")

    selected = payload["selected_evidence_ids"]
    omitted = payload["omitted_evidence_ids"]
    if not _id_list(selected, "selected_evidence_ids", errors):
        selected = []
    if not _id_list(omitted, "omitted_evidence_ids", errors):
        omitted = []
    if set(selected) & set(omitted):
        errors.append("selected_omitted_overlap")
    if is_v2 and post_task_ids & (set(selected) | set(omitted)):
        errors.append("context_post_task_evidence_id_overlap")

    misses = payload["retrieval_misses"]
    if type(misses) is not list or len(misses) > MAX_REFERENCES:
        errors.append("retrieval_misses_invalid")
        misses = []
    else:
        miss_ids: set[str] = set()
        for row in misses:
            if type(row) is not dict or set(row) != {"evidence_id", "status"}:
                errors.append("retrieval_miss_shape_invalid")
                continue
            evidence_id, status = row["evidence_id"], row["status"]
            if not _is_id(evidence_id) or status not in {"missing", "stale", "unsafe", "unknown_snapshot", "unknown_source", "evicted"}:
                errors.append("retrieval_miss_value_invalid")
                continue
            if evidence_id not in omitted:
                errors.append("retrieval_miss_not_omitted")
            if evidence_id in miss_ids:
                errors.append("duplicate_retrieval_miss")
            miss_ids.add(evidence_id)

    route = payload["actual_route"]
    if route not in {"none", "local", "frontier", "mixed", "unknown"}:
        errors.append("actual_route_invalid")

    attempts = payload["attempts"]
    attempt_ids: list[str] = []
    if type(attempts) is not list or len(attempts) > MAX_ATTEMPTS:
        errors.append("attempts_invalid")
        attempts = []
    for attempt in attempts:
        expected = {"attempt_id", "route", "result", "retry_of", "fallback", "call_made", "usage"}
        if type(attempt) is not dict or set(attempt) != expected:
            errors.append("attempt_shape_invalid")
            continue
        aid = attempt["attempt_id"]
        if not _is_id(aid):
            errors.append("attempt_id_invalid")
        else:
            attempt_ids.append(aid)
        if attempt["route"] not in {"none", "local", "frontier"} or attempt["result"] not in {"success", "failed", "timeout", "cancelled", "not_run"}:
            errors.append("attempt_enum_invalid")
        if type(attempt["fallback"]) is not bool or type(attempt["call_made"]) is not bool:
            errors.append("attempt_boolean_invalid")
        if attempt["route"] == "none" and attempt["call_made"] is True:
            errors.append("no_model_attempt_claims_call")
        if attempt["fallback"] is True and attempt["call_made"] is not True:
            errors.append("fallback_without_call")
        if attempt["retry_of"] is not None and not _is_id(attempt["retry_of"]):
            errors.append("retry_reference_invalid")
        usage = attempt["usage"]
        if type(usage) is not dict or set(usage) != {
            "status", "counter_id", "local_input_tokens", "local_output_tokens",
            "frontier_input_tokens", "frontier_output_tokens", "local_cost_microunits",
            "frontier_cost_microunits", "cost_status",
        }:
            errors.append("usage_shape_invalid")
            continue
        _validate_usage(usage, errors)
        if attempt["route"] == "local":
            unrelated = ("frontier_input_tokens", "frontier_output_tokens", "frontier_cost_microunits")
        else:
            unrelated = ("local_input_tokens", "local_output_tokens", "local_cost_microunits")
        if attempt["route"] in {"local", "frontier"} and any(usage.get(name) not in (None, 0) for name in unrelated):
            errors.append("attempt_usage_route_mismatch")
        if attempt["call_made"] is False:
            numeric_usage = tuple(f"{route}_{kind}_tokens" for route in ("local", "frontier") for kind in ("input", "output")) + (
                "local_cost_microunits", "frontier_cost_microunits",
            )
            if any(usage.get(name) not in (None, 0) for name in numeric_usage):
                errors.append("no_call_has_positive_usage")
    if len(set(attempt_ids)) != len(attempt_ids):
        errors.append("duplicate_attempt_id")
    known_attempts = set(attempt_ids)
    attempt_position = {attempt_id: index for index, attempt_id in enumerate(attempt_ids)}
    attempt_by_id = {
        attempt["attempt_id"]: attempt
        for attempt in attempts if type(attempt) is dict and _is_id(attempt.get("attempt_id"))
    }
    for index, attempt in enumerate(attempts):
        if type(attempt) is dict and attempt.get("retry_of") is not None and attempt.get("retry_of") not in known_attempts:
            errors.append("retry_reference_unknown")
        if type(attempt) is dict and attempt.get("retry_of") == attempt.get("attempt_id"):
            errors.append("retry_self_reference")
        if type(attempt) is dict and attempt.get("retry_of") is not None:
            target_id = attempt.get("retry_of")
            target = attempt_position.get(target_id, index) if _is_id(target_id) else index
            target_row = attempt_by_id.get(target_id) if _is_id(target_id) else None
            if target >= index or attempt.get("call_made") is not True or target_row is None or target_row.get("call_made") is not True:
                errors.append("retry_order_or_call_mismatch")

    work_calls = payload["work_calls"]
    work_ids: list[str] = []
    if type(work_calls) is not list or len(work_calls) > MAX_REFERENCES:
        errors.append("work_calls_invalid")
        work_calls = []
    for work in work_calls:
        if type(work) is not dict or set(work) != {"call_id", "kind", "route", "result", "usage"}:
            errors.append("work_call_shape_invalid")
            continue
        if not _is_id(work["call_id"]):
            errors.append("work_call_id_invalid")
        else:
            work_ids.append(work["call_id"])
        if work["kind"] not in {"verifier", "tool"}:
            errors.append("work_call_kind_invalid")
        if work["route"] not in {"none", "local", "frontier"}:
            errors.append("work_call_route_invalid")
        if work["result"] not in {"success", "failed", "timeout", "cancelled", "not_run", "passed", "inconclusive"}:
            errors.append("work_call_result_invalid")
        usage = work["usage"]
        if type(usage) is not dict or set(usage) != {
            "status", "counter_id", "local_input_tokens", "local_output_tokens",
            "frontier_input_tokens", "frontier_output_tokens", "local_cost_microunits",
            "frontier_cost_microunits", "cost_status",
        }:
            errors.append("work_call_usage_shape_invalid")
            continue
        _validate_usage(usage, errors)
        if work["route"] == "none" and usage.get("status") != "not_applicable":
            errors.append("non_model_work_usage_must_be_not_applicable")
        if work["route"] == "none" and usage.get("cost_status") == "known" and any(
            usage.get(k) != 0 for k in ("local_cost_microunits", "frontier_cost_microunits")
        ):
            errors.append("non_model_work_cost_must_be_zero_or_unknown")
        if work["route"] == "local" and any(usage.get(k) not in (None, 0) for k in ("frontier_input_tokens", "frontier_output_tokens", "frontier_cost_microunits")):
            errors.append("work_call_usage_route_mismatch")
        if work["route"] == "frontier" and any(usage.get(k) not in (None, 0) for k in ("local_input_tokens", "local_output_tokens", "local_cost_microunits")):
            errors.append("work_call_usage_route_mismatch")
    if len(set(work_ids)) != len(work_ids) or set(work_ids) & set(attempt_ids):
        errors.append("duplicate_call_id")

    calls = {"local": 0, "frontier": 0}
    retry_count = 0
    fallback_count = 0
    for attempt in attempts:
        if type(attempt) is dict and attempt.get("route") in calls:
            if attempt.get("call_made") is True:
                calls[attempt["route"]] += 1
            if attempt.get("retry_of") is not None:
                retry_count += 1
            if attempt.get("fallback") is True and attempt.get("call_made") is True:
                fallback_count += 1
    for work in work_calls:
        if type(work) is dict and work.get("route") in calls:
            calls[work["route"]] += 1
    if route == "none" and (calls["local"] or calls["frontier"]):
        errors.append("no_model_route_has_model_call")
    if route == "local" and (calls["frontier"] or not calls["local"]):
        errors.append("actual_route_call_mismatch")
    if route == "frontier" and (calls["local"] or not calls["frontier"]):
        errors.append("actual_route_call_mismatch")
    if route == "mixed" and not (calls["local"] and calls["frontier"]):
        errors.append("actual_route_call_mismatch")
    if route == "unknown" and (calls["local"] or calls["frontier"]):
        errors.append("unknown_route_has_attributed_call")

    evidence_scope = post_task_ids if is_v2 else set(selected)
    verifier = payload["verifier"]
    if type(verifier) is not dict or set(verifier) != {"identity", "result", "evidence_ids"}:
        errors.append("verifier_shape_invalid")
        verifier = {"identity": None, "result": "unknown", "evidence_ids": []}
    else:
        if verifier["identity"] is not None and not (
            _is_opaque_v2_id(verifier["identity"]) if is_v2 else _is_id(verifier["identity"])
        ):
            errors.append("verifier_identity_invalid")
        if verifier["result"] not in {"passed", "failed", "inconclusive", "not_run", "unknown"}:
            errors.append("verifier_result_invalid")
        if not _id_list(verifier["evidence_ids"], "verifier_evidence_ids", errors):
            verifier["evidence_ids"] = []
        elif any(eid not in evidence_scope for eid in verifier["evidence_ids"]):
            errors.append("verifier_evidence_not_post_task" if is_v2 else "verifier_evidence_not_selected")

    outcome = payload["outcome"]
    if type(outcome) is not dict or set(outcome) != {"status", "provenance", "evidence_ids"}:
        errors.append("outcome_shape_invalid")
        outcome = {"status": "unknown", "provenance": "unknown", "evidence_ids": []}
    else:
        if outcome["status"] not in {"completed", "failed", "partial", "unknown"}:
            errors.append("outcome_status_invalid")
        if outcome["provenance"] not in {"user_reported", "independently_verified", "unknown"}:
            errors.append("outcome_provenance_invalid")
        if not _id_list(outcome["evidence_ids"], "outcome_evidence_ids", errors):
            outcome["evidence_ids"] = []
        elif any(eid not in evidence_scope for eid in outcome["evidence_ids"]):
            errors.append("outcome_evidence_not_post_task" if is_v2 else "outcome_evidence_not_selected")
        if outcome["provenance"] == "independently_verified" and (
            verifier["result"] not in {"passed", "failed", "inconclusive"} or not verifier["identity"]
            or not verifier["evidence_ids"] or not outcome["evidence_ids"]
        ):
            errors.append("independent_outcome_lacks_verification_evidence")
        if outcome["provenance"] == "independently_verified":
            expected_outcome = {"passed": "completed", "failed": "failed", "inconclusive": "partial"}.get(verifier["result"])
            if expected_outcome is None or outcome["status"] != expected_outcome:
                errors.append("independent_outcome_verifier_status_mismatch")

    corrections = payload["correction_refs"]
    if not _id_list(corrections, "correction_refs", errors):
        corrections = []

    accounting = payload["accounting"]
    if type(accounting) is not dict or set(accounting) != {
        "local_model_calls", "frontier_model_calls", "retries", "fallback_calls",
        "verifier_calls", "tool_calls", "local_tokens", "frontier_tokens",
        "local_token_counter_id", "frontier_token_counter_id", "token_count_status", "local_cost_microunits",
        "frontier_cost_microunits", "cost_status",
    }:
        errors.append("accounting_shape_invalid")
    else:
        for name in ("local_model_calls", "frontier_model_calls", "retries", "fallback_calls", "verifier_calls", "tool_calls"):
            if not _count(accounting[name]):
                errors.append(f"accounting_{name}_invalid")
        if accounting["local_model_calls"] != calls["local"] or accounting["frontier_model_calls"] != calls["frontier"]:
            errors.append("accounting_call_totals_mismatch")
        if accounting["retries"] != retry_count or accounting["fallback_calls"] != fallback_count:
            errors.append("accounting_attempt_totals_mismatch")
        if accounting["verifier_calls"] != sum(1 for row in work_calls if type(row) is dict and row.get("kind") == "verifier"):
            errors.append("accounting_verifier_calls_mismatch")
        if accounting["tool_calls"] != sum(1 for row in work_calls if type(row) is dict and row.get("kind") == "tool"):
            errors.append("accounting_tool_calls_mismatch")
        if accounting["token_count_status"] not in {"exact", "estimated", "unknown", "not_applicable"}:
            errors.append("token_count_status_invalid")
        for route_name in ("local", "frontier"):
            identity = accounting[f"{route_name}_token_counter_id"]
            if identity is not None and not _is_id(identity):
                errors.append(f"{route_name}_token_counter_identity_invalid")
        model_calls = [
            (record, record["usage"])
            for record in attempts if type(record) is dict and record.get("call_made") is True and type(record.get("usage")) is dict
        ] + [
            (record, record["usage"])
            for record in work_calls if type(record) is dict and record.get("route") in {"local", "frontier"} and type(record.get("usage")) is dict
        ]
        for route_name in ("local", "frontier"):
            route_usages = [
                usage for record, usage in model_calls
                if record.get("route") == route_name
            ]
            route_counters = {
                usage.get("counter_id") for usage in route_usages
                if usage.get("status") in {"exact", "estimated"} and _is_id(usage.get("counter_id"))
            }
            if len(route_counters) > 1 or route_counters and accounting[f"{route_name}_token_counter_id"] not in route_counters:
                errors.append(f"{route_name}_token_counter_identity_mismatch")
            if route_usages and accounting["token_count_status"] in {"exact", "estimated"} and any(s.get("status") not in {"exact", "estimated"} for s in route_usages):
                errors.append(f"{route_name}_token_usage_not_reconciled")
            if not route_usages and accounting[f"{route_name}_token_counter_id"] is not None:
                errors.append(f"{route_name}_token_counter_without_calls")
        if accounting["token_count_status"] == "unknown" and (accounting["local_token_counter_id"] is not None or accounting["frontier_token_counter_id"] is not None or accounting["local_tokens"] is not None or accounting["frontier_tokens"] is not None):
            errors.append("unknown_token_usage_must_remain_null")
        if accounting["token_count_status"] == "not_applicable" and (accounting["local_token_counter_id"] is not None or accounting["frontier_token_counter_id"] is not None or accounting["local_tokens"] != 0 or accounting["frontier_tokens"] != 0 or calls["local"] or calls["frontier"]):
            errors.append("not_applicable_token_usage_mismatch")
        for name in ("local_tokens", "frontier_tokens", "local_cost_microunits", "frontier_cost_microunits"):
            if accounting[name] is not None and not _count(accounting[name]):
                errors.append(f"accounting_{name}_invalid")
        if accounting["cost_status"] not in {"known", "unknown"}:
            errors.append("cost_status_invalid")
        if accounting["cost_status"] == "unknown" and (accounting["local_cost_microunits"] is not None or accounting["frontier_cost_microunits"] is not None):
            errors.append("unknown_cost_must_remain_null")
        if accounting["cost_status"] == "known" and (accounting["local_cost_microunits"] is None or accounting["frontier_cost_microunits"] is None):
            errors.append("known_cost_missing_amount")
        if route == "none" and accounting["token_count_status"] != "not_applicable" and not (accounting["token_count_status"] == "exact" and accounting["local_tokens"] == 0 and accounting["frontier_tokens"] == 0):
            errors.append("no_model_usage_must_be_explicit_zero")
        if model_calls and accounting["token_count_status"] in {"exact", "estimated"}:
            token_statuses = [usage["status"] for _, usage in model_calls]
            if any(s not in {"exact", "estimated"} for s in token_statuses):
                errors.append("accounting_token_status_not_reconciled")
            else:
                if accounting["token_count_status"] == "exact" and any(s != "exact" for s in token_statuses):
                    errors.append("accounting_token_status_mismatch")
                local_total = sum(usage[f"local_{side}_tokens"] or 0 for _, usage in model_calls for side in ("input", "output"))
                frontier_total = sum(usage[f"frontier_{side}_tokens"] or 0 for _, usage in model_calls for side in ("input", "output"))
                if accounting["local_tokens"] != local_total or accounting["frontier_tokens"] != frontier_total:
                    errors.append("accounting_token_totals_mismatch")
        if model_calls and accounting["token_count_status"] == "unknown" and not any(usage.get("status") == "unknown" for _, usage in model_calls):
            errors.append("accounting_unknown_tokens_not_reconciled")
        if accounting["cost_status"] == "known":
            known_cost_attempts = [usage for _, usage in model_calls if usage.get("cost_status") == "known"]
            if len(known_cost_attempts) != len(model_calls):
                errors.append("accounting_cost_status_not_reconciled")
            else:
                local_cost = sum(usage["local_cost_microunits"] or 0 for usage in known_cost_attempts)
                frontier_cost = sum(usage["frontier_cost_microunits"] or 0 for usage in known_cost_attempts)
                if accounting["local_cost_microunits"] != local_cost or accounting["frontier_cost_microunits"] != frontier_cost:
                    errors.append("accounting_cost_totals_mismatch")
        elif accounting["cost_status"] == "unknown" and model_calls and not any(
            usage.get("cost_status") == "unknown" for _, usage in model_calls
        ):
            errors.append("accounting_unknown_cost_not_reconciled")

    completeness = payload["completeness"]
    missing = payload["missing_fields"]
    if completeness not in {"complete", "incomplete"} or not _string_list(missing, "missing_fields", errors, max_count=64):
        errors.append("completeness_invalid")
    elif (completeness == "complete") != (len(missing) == 0):
        errors.append("completeness_missing_fields_mismatch")
    elif len(set(missing)) != len(missing):
        errors.append("duplicate_missing_field")
    elif any(item not in {
        "snapshot_sha256", "context_receipt_sha256", "selected_evidence_ids", "omitted_evidence_ids",
        "retrieval_misses", "actual_route", "attempts", "work_calls", "verifier", "outcome",
        "correction_refs", "accounting", "usage", "costs", "session_id",
    } for item in missing):
        errors.append("missing_field_name_unknown")
    derived_missing: set[str] = set()
    if payload["snapshot_sha256"] is None:
        derived_missing.add("snapshot_sha256")
    if payload["context_receipt_sha256"] is None:
        derived_missing.add("context_receipt_sha256")
    if is_v2 and payload["session_id"] is None:
        derived_missing.add("session_id")
    if route == "unknown":
        derived_missing.add("actual_route")
    if outcome.get("status") == "unknown" or outcome.get("provenance") == "unknown":
        derived_missing.add("outcome")
    if type(accounting) is dict and accounting.get("token_count_status") == "unknown":
        derived_missing.add("usage")
    if type(accounting) is dict and accounting.get("cost_status") == "unknown":
        derived_missing.add("costs")
    missing_set = {item for item in missing if type(item) is str} if type(missing) is list else set()
    if derived_missing and (completeness != "incomplete" or not derived_missing.issubset(missing_set)):
        errors.append("incomplete_receipt_missing_field_list_inconsistent")
    if completeness == "complete":
        if payload["snapshot_sha256"] is None:
            errors.append("complete_receipt_missing_snapshot_identity")
        if payload["context_receipt_sha256"] is None:
            errors.append("complete_receipt_missing_context_identity")
        if is_v2 and payload["session_id"] is None:
            errors.append("complete_receipt_missing_session_identity")
        if route == "unknown":
            errors.append("complete_receipt_route_unknown")
        if outcome.get("status") == "unknown" or outcome.get("provenance") == "unknown":
            errors.append("complete_receipt_outcome_unknown")

    reference_total = (
        len(selected) + len(omitted) + len(misses) + len(corrections) + len(work_calls)
        + len(verifier.get("evidence_ids", [])) + len(outcome.get("evidence_ids", []))
        + sum(1 for attempt in attempts if type(attempt) is dict and attempt.get("retry_of") is not None)
        + len(post_task_ids)
    )
    if reference_total > MAX_REFERENCES:
        errors.append("aggregate_reference_limit_exceeded")
    verifier_rows = [row for row in work_calls if type(row) is dict and row.get("kind") == "verifier"]
    if verifier["result"] in {"passed", "failed", "inconclusive"}:
        if not verifier_rows or not any(row.get("result") == verifier["result"] for row in verifier_rows):
            errors.append("verifier_result_without_matching_call")
    elif verifier_rows:
        errors.append("verifier_call_result_mismatch")

    return errors


def _contains_forbidden_key(value: object) -> bool:
    forbidden = {"content", "source", "source_text", "prompt", "prompt_text", "raw_text", "hidden_reasoning", "reasoning", "chain_of_thought"}
    stack = [value]
    nodes = 0
    while stack:
        item = stack.pop()
        nodes += 1
        if nodes > 20000:
            return True
        if type(item) is dict:
            for key, nested in item.items():
                if type(key) is str and key.casefold() in forbidden:
                    return True
                if type(nested) in (dict, list):
                    stack.append(nested)
        elif type(item) is list:
            stack.extend(nested for nested in item if type(nested) in (dict, list))
    return False


def _id_list(value: object, label: str, errors: list[str]) -> bool:
    if type(value) is not list or len(value) > MAX_REFERENCES:
        errors.append(f"{label}_invalid")
        return False
    if any(not _is_id(item) for item in value):
        errors.append(f"{label}_item_invalid")
        return False
    if len(set(value)) != len(value):
        errors.append(f"{label}_duplicate")
        return False
    return True


def _string_list(value: object, label: str, errors: list[str], *, max_count: int) -> bool:
    if type(value) is not list or len(value) > max_count or any(not _is_id(item) for item in value):
        errors.append(f"{label}_invalid")
        return False
    return True


def _count(value: object) -> bool:
    return type(value) is int and 0 <= value <= 2**63 - 1


def _validate_usage(usage: dict[str, Any], errors: list[str]) -> None:
    if usage["status"] not in {"exact", "estimated", "unknown", "not_applicable"}:
        errors.append("attempt_usage_status_invalid")
    if usage["cost_status"] not in {"known", "unknown"}:
        errors.append("attempt_cost_status_invalid")
    if usage["counter_id"] is not None and not _is_id(usage["counter_id"]):
        errors.append("attempt_counter_id_invalid")
    token_fields = ("local_input_tokens", "local_output_tokens", "frontier_input_tokens", "frontier_output_tokens")
    cost_fields = ("local_cost_microunits", "frontier_cost_microunits")
    for name in token_fields + cost_fields:
        if usage[name] is not None and not _count(usage[name]):
            errors.append(f"attempt_{name}_invalid")
    if usage["status"] in {"exact", "estimated"} and not _is_id(usage["counter_id"]):
        errors.append("attempt_counter_identity_missing")
    if usage["status"] == "unknown" and (usage["counter_id"] is not None or any(usage[name] is not None for name in token_fields)):
        errors.append("attempt_unknown_usage_must_remain_null")
    if usage["status"] == "not_applicable" and any(usage[name] not in (None, 0) for name in token_fields):
        errors.append("attempt_not_applicable_tokens_mismatch")
    if usage["cost_status"] == "unknown" and any(usage[name] is not None for name in cost_fields):
        errors.append("attempt_unknown_cost_must_remain_null")
    if usage["cost_status"] == "known" and any(usage[name] is None for name in cost_fields):
        errors.append("attempt_known_cost_missing_amount")


def validate_outcome_receipt(receipt: object) -> ReceiptResult:
    if type(receipt) is not OutcomeReceipt:
        return ReceiptResult(ReceiptStatus.INVALID, None, ("receipt_type_invalid",))
    if type(receipt.payload_json) is not str or len(receipt.payload_json) > MAX_RECEIPT_BYTES or len(receipt.payload_json.encode("utf-8", errors="surrogatepass")) > MAX_RECEIPT_BYTES:
        return ReceiptResult(ReceiptStatus.INVALID, None, ("serialized_receipt_too_large_or_invalid",))
    if not _is_digest(receipt.sha256):
        return ReceiptResult(ReceiptStatus.INVALID, None, ("receipt_digest_invalid",))
    try:
        payload = json.loads(receipt.payload_json)
        if type(payload) is not dict:
            raise ValueError("root_not_object")
        canonical = _canonical_json(payload)
    except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError, RuntimeError) as exc:
        return ReceiptResult(ReceiptStatus.INVALID, None, (f"serialized_payload_invalid:{type(exc).__name__}",))
    if canonical != receipt.payload_json or hashlib.sha256(canonical.encode("utf-8")).hexdigest() != receipt.sha256:
        return ReceiptResult(ReceiptStatus.INVALID, None, ("receipt_hash_or_canonical_form_mismatch",))
    try:
        errors = _failures(payload)
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        return ReceiptResult(ReceiptStatus.INVALID, None, (f"receipt_validation_malformed_value:{type(exc).__name__}",))
    if errors:
        return ReceiptResult(ReceiptStatus.INVALID, None, tuple(sorted(set(errors))))
    status = ReceiptStatus.INCOMPLETE if payload["completeness"] == "incomplete" else ReceiptStatus.VALID
    return ReceiptResult(status, receipt)


def build_outcome_receipt(payload: object) -> ReceiptResult:
    """Build a canonical receipt from metadata; malformed input fails closed."""
    if type(payload) is not dict:
        return ReceiptResult(ReceiptStatus.INVALID, None, ("payload_must_be_builtin_object",))
    try:
        canonical = _canonical_json(payload)
    except (ValueError, TypeError, OverflowError, UnicodeError, RecursionError, RuntimeError) as exc:
        return ReceiptResult(ReceiptStatus.INVALID, None, (f"payload_serialization_invalid:{type(exc).__name__}",))
    receipt = OutcomeReceipt(canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest())
    return validate_outcome_receipt(receipt)


__all__ = [
    "MAX_ATTEMPTS", "MAX_RECEIPT_BYTES", "MAX_REFERENCES", "MAX_ID_CHARS",
    "OutcomeReceipt", "ReceiptResult", "ReceiptStatus", "build_outcome_receipt",
    "validate_outcome_receipt",
]
