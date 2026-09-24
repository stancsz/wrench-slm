"""Join one E0 preparation to caller-supplied post-run outcome evidence.

This module validates bounded references and receipt joins only. It does not
observe client activity, authenticate caller claims, persist data, or establish
consent, verifier independence, or task truth.
"""

from __future__ import annotations

import json

from .e0_context_pipeline import (
    PreparationResult,
    PreparationStatus,
    verify_preparation_accounting_receipt,
)
from .outcome_receipt import (
    ReceiptResult,
    ReceiptStatus,
    build_outcome_receipt,
    validate_outcome_receipt,
)
from .opencode_context import OpenCodePreparationJoin


_POSTRUN_FIELDS = {
    "task_id", "run_id", "session_id", "actual_route", "attempts", "work_calls",
    "post_task_evidence_refs", "verifier", "outcome", "correction_refs",
    "accounting", "completeness", "missing_fields",
}


def finalize_preparation_outcome(
    preparation: PreparationResult,
    postrun: object,
) -> ReceiptResult:
    """Bind a ready preparation and its accounting receipt to a post-run record.

    ``postrun`` is reference-only metadata conforming to the v3 outcome receipt
    fields. The final receipt copies snapshot and context evidence identities
    from the preparation output and binds the preparation-accounting digest.
    Caller-supplied attempts, verifier results, and outcome claims remain
    untrusted metadata; this function does not authenticate or execute them.
    """
    if type(preparation) is not PreparationResult or preparation.status is not PreparationStatus.READY:
        return _invalid("preparation_not_ready")
    if type(postrun) is not dict or len(postrun) != len(_POSTRUN_FIELDS) or set(postrun) != _POSTRUN_FIELDS:
        return _invalid("postrun_fields_invalid")
    if type(preparation.aggregate_sha256) is not str:
        return _invalid("preparation_identity_missing")
    if preparation.outcome_receipt is None or preparation.outcome_receipt.receipt is None:
        return _invalid("preparation_outcome_receipt_missing")
    prepared = validate_outcome_receipt(preparation.outcome_receipt.receipt)
    if prepared.status is not ReceiptStatus.INCOMPLETE or prepared.receipt is None:
        return _invalid("preparation_outcome_receipt_invalid")
    try:
        prepared_payload = json.loads(prepared.receipt.payload_json)
    except (TypeError, ValueError, RecursionError):
        return _invalid("preparation_outcome_payload_invalid")
    if (
        prepared_payload.get("schema") != "wrench.e0.outcome-receipt.v1"
        or prepared_payload.get("context_receipt_sha256") != preparation.aggregate_sha256
        or prepared_payload.get("actual_route") != "none"
        or prepared_payload.get("outcome", {}).get("status") != "unknown"
    ):
        return _invalid("preparation_outcome_identity_mismatch")
    accounting = preparation.accounting_receipt
    if accounting is None or not verify_preparation_accounting_receipt(
        accounting, aggregate_sha256=preparation.aggregate_sha256
    ):
        return _invalid("preparation_accounting_invalid")

    payload = {
        "schema": "wrench.e0.outcome-receipt.v3",
        "task_id": postrun["task_id"],
        "run_id": postrun["run_id"],
        "session_id": postrun["session_id"],
        "snapshot_sha256": prepared_payload["snapshot_sha256"],
        "context_receipt_sha256": preparation.aggregate_sha256,
        "preparation_accounting_sha256": accounting.accounting_sha256,
        "selected_evidence_ids": prepared_payload["selected_evidence_ids"],
        "omitted_evidence_ids": prepared_payload["omitted_evidence_ids"],
        "retrieval_misses": prepared_payload["retrieval_misses"],
        "actual_route": postrun["actual_route"],
        "attempts": postrun["attempts"],
        "work_calls": postrun["work_calls"],
        "post_task_evidence_refs": postrun["post_task_evidence_refs"],
        "verifier": postrun["verifier"],
        "outcome": postrun["outcome"],
        "correction_refs": postrun["correction_refs"],
        "accounting": postrun["accounting"],
        "completeness": postrun["completeness"],
        "missing_fields": postrun["missing_fields"],
    }
    return build_outcome_receipt(payload)


def finalize_opencode_preparation_outcome(
    join: OpenCodePreparationJoin,
    postrun: object,
) -> ReceiptResult:
    """Bind caller-supplied post-run metadata to an OpenCode session join.

    This adds a structural session-ID equality check before delegating to the
    generic receipt finalizer. It does not authenticate either value or observe
    OpenCode/provider activity.
    """
    if (
        type(join) is not OpenCodePreparationJoin
        or type(join.session_id) is not str
        or not join.session_id
    ):
        return _invalid("opencode_join_invalid")
    if type(postrun) is not dict:
        return _invalid("postrun_fields_invalid")
    if postrun.get("session_id") != join.session_id:
        return _invalid("opencode_session_id_mismatch")
    result = finalize_preparation_outcome(join.preparation, postrun)
    if result.receipt is None:
        return result
    try:
        payload = json.loads(result.receipt.payload_json)
    except (TypeError, ValueError, RecursionError):
        return _invalid("opencode_outcome_receipt_invalid")
    if payload.get("snapshot_sha256") != join.snapshot_sha256:
        return _invalid("opencode_snapshot_sha256_mismatch")
    return result


def _invalid(error: str) -> ReceiptResult:
    return ReceiptResult(ReceiptStatus.INVALID, None, (error,))


__all__ = [
    "finalize_opencode_preparation_outcome",
    "finalize_preparation_outcome",
]
