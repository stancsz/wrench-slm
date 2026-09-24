"""Offline coordinator for one bounded E0 request scope.

This module joins existing local preparation, artifact pin, model-version pin,
and terminal outcome references. The resulting envelope is structural,
caller-supplied evidence only. It is not authenticated, production evidence,
or a claim that a task outcome is true.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .artifact_store import ArtifactRequest, ArtifactStore
from .e0_context_pipeline import (
    PreparationResult,
    PreparationStatus,
    verify_preparation_accounting_receipt,
)
from .model_lifecycle import ModelLifecycle, VersionPin
from .outcome_receipt import (
    OutcomeReceipt,
    ReceiptResult,
    ReceiptStatus,
    validate_outcome_receipt,
)
from .prompt_compiler import MAX_SERIALIZED_PROMPT_BYTES, PromptGateReceipt, PromptGateStatus


SCHEMA = "wrench.e0-request-scope.v1"
MAX_ENVELOPE_BYTES = 4096
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_OPAQUE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class RequestScopeError(ValueError):
    """A request scope could not be joined or finalized safely."""


class RequestScopeStatus(str, Enum):
    OPEN = "open"
    READY = "ready"
    FAILED = "failed"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True)
class RequestScopeEnvelope:
    schema: str
    payload_json: str
    sha256: str
    evidence_class: str = "untrusted_local_structural_development_only"


class RequestScopeCoordinator:
    """Create one request scope using existing artifact and model primitives."""

    def __init__(self, artifact_store: ArtifactStore, model_lifecycle: ModelLifecycle):
        if type(artifact_store) is not ArtifactStore or type(model_lifecycle) is not ModelLifecycle:
            raise RequestScopeError("coordinator_dependencies_invalid")
        self._artifact_store = artifact_store
        self._model_lifecycle = model_lifecycle

    def open_scope(self, request_id: str) -> "E0RequestScope":
        if type(request_id) is not str or _OPAQUE_ID.fullmatch(request_id) is None:
            raise RequestScopeError("request_id_invalid")
        return E0RequestScope(self._artifact_store, self._model_lifecycle, request_id)


class E0RequestScope:
    """One in-flight scope; its artifact pins release on every context exit."""

    def __init__(self, artifact_store: ArtifactStore, model_lifecycle: ModelLifecycle, request_id: str):
        self.request_id = request_id
        self._artifact_store = artifact_store
        self._model_lifecycle = model_lifecycle
        self._artifact_request: ArtifactRequest | None = None
        self._version_pin: VersionPin | None = None
        self._preparation: PreparationResult | None = None
        self._preparation_receipt: OutcomeReceipt | None = None
        self._snapshot_sha256: str | None = None
        self._outcome_receipt: OutcomeReceipt | None = None
        self._envelope: RequestScopeEnvelope | None = None
        self.status = RequestScopeStatus.INCOMPLETE
        self._entered = False
        self._closed = False

    @property
    def artifact_request(self) -> ArtifactRequest:
        if not self._entered or self._closed or self._artifact_request is None:
            raise RequestScopeError("request_scope_not_active")
        return self._artifact_request

    @property
    def version_pin(self) -> VersionPin:
        if not self._entered or self._closed or self._version_pin is None:
            raise RequestScopeError("request_scope_not_active")
        return self._version_pin

    def _require_active_artifact_request(self) -> ArtifactRequest:
        request = self._artifact_request
        if (
            not self._entered or self._closed or request is None
            or not request.is_active_for(self._artifact_store)
        ):
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("artifact_request_scope_inactive")
        return request

    @property
    def envelope(self) -> RequestScopeEnvelope | None:
        return self._envelope

    def __enter__(self) -> "E0RequestScope":
        if self._entered or self._closed:
            raise RequestScopeError("request_scope_cannot_be_reentered")
        request = self._artifact_store.request()
        request.__enter__()
        self._artifact_request = request
        try:
            # pin() resolves the active version at this request's start.
            self._version_pin = self._model_lifecycle.pin(self.request_id)
        except Exception as exc:
            request.__exit__(type(exc), exc, exc.__traceback__)
            self._closed = True
            raise
        self._entered = True
        self.status = RequestScopeStatus.OPEN
        return self

    def prepare(self, preparer: Callable[[ArtifactRequest], PreparationResult]) -> PreparationResult:
        """Run caller preparation with this exact active ArtifactRequest."""
        if not self._entered or self._closed or self._preparation is not None:
            raise RequestScopeError("preparation_scope_invalid")
        if not callable(preparer):
            raise RequestScopeError("preparer_invalid")
        request = self._require_active_artifact_request()
        try:
            result = preparer(request)
        except Exception:
            self.status = RequestScopeStatus.FAILED
            raise
        self._require_active_artifact_request()
        self.bind_preparation(result)
        return result

    def bind_preparation(self, result: PreparationResult) -> None:
        """Bind READY preparation and its verified accounting identity."""
        if not self._entered or self._closed or self._preparation is not None:
            raise RequestScopeError("preparation_scope_invalid")
        if type(result) is not PreparationResult or result.status is not PreparationStatus.READY:
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("preparation_not_ready")
        if result.route != "none" or type(result.prompt) not in (str, bytes):
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("preparation_prompt_invalid")
        gate = result.prompt_gate
        if (
            type(gate) is not PromptGateReceipt
            or gate.status is not PromptGateStatus.READY
            or type(gate.prompt_sha256) is not str
            or _SHA256.fullmatch(gate.prompt_sha256) is None
            or type(gate.serialized_bytes) is not int
        ):
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("preparation_prompt_gate_invalid")
        if type(result.prompt) is bytes:
            if len(result.prompt) > MAX_SERIALIZED_PROMPT_BYTES:
                self.status = RequestScopeStatus.INCOMPLETE
                raise RequestScopeError("preparation_prompt_size_invalid")
            prompt_bytes = result.prompt
        else:
            if len(result.prompt) > MAX_SERIALIZED_PROMPT_BYTES:
                self.status = RequestScopeStatus.INCOMPLETE
                raise RequestScopeError("preparation_prompt_size_invalid")
            prompt_bytes = result.prompt.encode("utf-8")
            if len(prompt_bytes) > MAX_SERIALIZED_PROMPT_BYTES:
                self.status = RequestScopeStatus.INCOMPLETE
                raise RequestScopeError("preparation_prompt_size_invalid")
        if (
            len(prompt_bytes) != gate.serialized_bytes
            or hashlib.sha256(prompt_bytes).hexdigest() != gate.prompt_sha256
        ):
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("preparation_prompt_identity_mismatch")
        digest = result.aggregate_sha256
        accounting = result.accounting_receipt
        if type(digest) is not str or _SHA256.fullmatch(digest) is None:
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("preparation_identity_invalid")
        if accounting is None or not verify_preparation_accounting_receipt(accounting, aggregate_sha256=digest):
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("preparation_accounting_invalid")
        receipt_result = result.outcome_receipt
        if (
            type(receipt_result) is not ReceiptResult
            or receipt_result.status is not ReceiptStatus.INCOMPLETE
            or type(receipt_result.receipt) is not OutcomeReceipt
        ):
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("preparation_outcome_receipt_invalid")
        checked = validate_outcome_receipt(receipt_result.receipt)
        if checked.status is not ReceiptStatus.INCOMPLETE or checked.receipt is None:
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("preparation_outcome_receipt_invalid")
        try:
            prepared_payload = json.loads(checked.receipt.payload_json)
        except (TypeError, ValueError, RecursionError) as exc:
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("preparation_outcome_payload_invalid") from exc
        if (
            prepared_payload.get("schema") != "wrench.e0.outcome-receipt.v1"
            or prepared_payload.get("context_receipt_sha256") != digest
            or type(prepared_payload.get("snapshot_sha256")) is not str
            or _SHA256.fullmatch(prepared_payload["snapshot_sha256"]) is None
            or prepared_payload.get("actual_route") != "none"
            or prepared_payload.get("outcome", {}).get("status") != "unknown"
            or prepared_payload.get("completeness") != "incomplete"
        ):
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("preparation_outcome_identity_mismatch")
        self._preparation = result
        self._preparation_receipt = checked.receipt
        self._snapshot_sha256 = prepared_payload["snapshot_sha256"]

    def finish(self, receipt: OutcomeReceipt) -> None:
        """Supply a separate, explicit terminal receipt and check its joins.

        A complete receipt with a failed task outcome remains valid terminal
        evidence. Receipt completeness and task outcome status stay distinct.
        """
        if not self._entered or self._closed or self._outcome_receipt is not None:
            raise RequestScopeError("terminal_receipt_scope_invalid")
        self._require_active_artifact_request()
        if self._preparation is None:
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("preparation_join_missing")
        checked = validate_outcome_receipt(receipt)
        if checked.status is not ReceiptStatus.VALID or checked.receipt is None:
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("terminal_receipt_incomplete_or_invalid")
        try:
            payload = json.loads(checked.receipt.payload_json)
        except (TypeError, ValueError, RecursionError) as exc:
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("terminal_receipt_payload_invalid") from exc
        if payload.get("run_id") != self.request_id:
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("request_run_join_mismatch")
        preparation = self._preparation
        try:
            prepared_payload = json.loads(self._preparation_receipt.payload_json)
        except (AttributeError, TypeError, ValueError, RecursionError) as exc:
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("preparation_outcome_payload_invalid") from exc
        if payload.get("context_receipt_sha256") != preparation.aggregate_sha256:
            self.status = RequestScopeStatus.INCOMPLETE
            raise RequestScopeError("context_receipt_join_mismatch")
        for field in (
            "snapshot_sha256", "selected_evidence_ids", "omitted_evidence_ids",
            "retrieval_misses",
        ):
            if payload.get(field) != prepared_payload.get(field):
                self.status = RequestScopeStatus.INCOMPLETE
                raise RequestScopeError("preparation_outcome_join_mismatch")
        if payload.get("schema") in {"wrench.e0.outcome-receipt.v2", "wrench.e0.outcome-receipt.v3"}:
            accounting = preparation.accounting_receipt
            if payload.get("preparation_accounting_sha256") != accounting.accounting_sha256:
                self.status = RequestScopeStatus.INCOMPLETE
                raise RequestScopeError("preparation_accounting_join_mismatch")
        self._outcome_receipt = checked.receipt

    def __exit__(self, exc_type, exc, traceback) -> None:
        request = self._artifact_request
        artifact_request_active = (
            request is not None and self._entered
            and request.is_active_for(self._artifact_store)
        )
        try:
            if artifact_request_active and not self._closed:
                request.__exit__(exc_type, exc, traceback)
        finally:
            self._closed = True
            self._entered = False
        if exc_type is not None:
            self.status = RequestScopeStatus.FAILED
            self._envelope = None
            return None
        if (not artifact_request_active or self._preparation is None or self._preparation_receipt is None
                or self._outcome_receipt is None or self._version_pin is None):
            if self.status is not RequestScopeStatus.FAILED:
                self.status = RequestScopeStatus.INCOMPLETE
            self._envelope = None
            return None
        try:
            duration = request.pin_scope_duration_ns if request is not None else None
            payload = {
                "schema": SCHEMA,
                "request_id": self.request_id,
                "version_id": self._version_pin.version_id,
                "manifest_sha256": self._version_pin.manifest_sha256,
                "context_receipt_sha256": self._preparation.aggregate_sha256,
                "snapshot_sha256": self._snapshot_sha256,
                "preparation_accounting_sha256": self._preparation.accounting_receipt.accounting_sha256,
                "preparation_outcome_receipt_sha256": self._preparation_receipt.sha256,
                "prompt_sha256": self._preparation.prompt_gate.prompt_sha256,
                "serializer_id": self._preparation.prompt_gate.serializer_id,
                "tokenizer_id": self._preparation.prompt_gate.tokenizer_id,
                "artifact_pin_scope_duration_ns": duration,
                "outcome_receipt_sha256": self._outcome_receipt.sha256,
                "outcome_status": json.loads(self._outcome_receipt.payload_json)["outcome"]["status"],
                "receipt_completeness": "complete",
                "trust": "untrusted_caller_supplied_structural_reference_only",
            }
            raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
            if len(raw) > MAX_ENVELOPE_BYTES:
                raise RequestScopeError("scope_envelope_size_limit")
            self._envelope = RequestScopeEnvelope(SCHEMA, raw.decode("ascii"), hashlib.sha256(raw).hexdigest())
            self.status = (
                RequestScopeStatus.FAILED if payload["outcome_status"] == "failed"
                else RequestScopeStatus.READY
            )
        except Exception:
            self.status = RequestScopeStatus.FAILED
            self._envelope = None
            raise
        return None


__all__ = [
    "E0RequestScope",
    "MAX_ENVELOPE_BYTES",
    "RequestScopeCoordinator",
    "RequestScopeEnvelope",
    "RequestScopeError",
    "RequestScopeStatus",
    "SCHEMA",
]
