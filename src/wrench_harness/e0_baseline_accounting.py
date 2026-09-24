"""Content-free E0 baseline join for one supplied snapshot manifest.

Inventory completeness is limited to the entries present in the supplied
root-bound snapshot manifest. This receipt does not discover omitted enrolled
paths or prove whole-filesystem coverage. It joins synthetic fixture evidence
only; it grants no runtime dispatch authority and establishes no provider
accounting or exact tokenizer parity. Manifest accounted/unaccounted counts
refer only to the supplied snapshot manifest. The structural candidate count
and selected-order digest do not expose context-candidate omission counts.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Mapping

from .e0_offline_request_composition import (
    OfflineCompositionReceipt,
    SYNTHETIC_SERIALIZER_ID,
    SYNTHETIC_TOKENIZER_ID,
    _fixture_serializer_for_projection,
    _fixture_tokenizer,
    _receipt_payload as _composition_payload,
    verify_offline_e0_composition_receipt,
)
from .opencode_hook_projection import project_opencode_context_hook
from .opencode_project_snapshot import OpenCodeProjectSnapshot
from .opencode_request_boundary import MAX_REQUEST_BYTES, LoweredRequest, StreamEnd
from .snapshot import SourceRootBinding, SourceSnapshot, _validate_snapshot, bind_source_root
from .snapshot_coverage import (
    CoverageFileStatus,
    INVENTORY_PAGE_SIZE,
    SnapshotInventoryReceipt,
    build_snapshot_inventory_receipt,
    _inventory_payload,
)


_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA = "wrench.e0.baseline-accounting.v3"
_MAX_RECEIPT_BYTES = 16 * 1024
_READ_STATUS_NAMES = frozenset({"ok", "unknown_snapshot", "unknown_source", "missing", "changed", "unsafe"})
_OMISSION_REASONS = frozenset({
    "active_token_budget", "not_selected", "preserved_unit_exceeds_active_budget",
    "unit_exceeds_active_budget", "missing", "stale", "unsafe", "unknown_snapshot",
    "unknown_source", "evicted", "limit_exceeded", "non_text",
})
_MISS_STATUSES = frozenset({
    "missing", "stale", "unsafe", "unknown_snapshot", "unknown_source",
    "evicted", "limit_exceeded", "non_text",
})


@dataclass(frozen=True)
class E0BaselineAccountingReceipt:
    """Content-free counts and hashes from the offline synthetic baseline."""

    schema: str
    provenance: str
    snapshot_sha256: str
    root_location_sha256: str
    root_identity: str
    inventory_receipt_sha256: str
    inventory_entry_count: int
    inventory_status_counts: tuple[tuple[str, int], ...]
    inventory_complete: bool
    exact_read_attempts: int
    exact_read_successes: int
    exact_read_returned_bytes: int
    exact_read_status_counts: tuple[tuple[str, int], ...]
    accounted_snapshot_manifest_entries: int
    unaccounted_snapshot_manifest_entries: int
    enrolled_omission_count: None
    preparation_sha256: str
    preparation_outcome_receipt_sha256: str
    preparation_outcome_receipt_validation_status: str
    preparation_outcome_status: str
    preparation_status: str
    route_preparation_sha256: str | None
    insertion_receipt_sha256: str | None
    semantic_projection_sha256: str | None
    context_candidate_count: int
    context_selected_candidate_order_sha256: str | None
    context_selected_evidence_count: int
    context_omitted_evidence_count: int
    context_omission_reason_counts: tuple[tuple[str, int], ...]
    context_retrieval_miss_count: int
    context_retrieval_miss_status_counts: tuple[tuple[str, int], ...]
    accounting_state: str
    synthetic_serializer_id: str
    synthetic_envelope_sha256: str | None
    synthetic_envelope_bytes: int | None
    synthetic_envelope_chars: int | None
    synthetic_tokenizer_id: str
    exact_token_gate: str
    synthetic_token_count: int | None
    lowered_request_body_sha256: str | None
    lowered_request_body_bytes: int | None
    terminal_outcome: str | None
    composition_receipt_sha256: str
    receipt_sha256: str


def _canonical(value: object) -> bytes:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(encoded) > _MAX_RECEIPT_BYTES:
        raise ValueError("baseline_accounting_receipt_limit_exceeded")
    return encoded


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _is_int(value: object) -> bool:
    return type(value) is int


def _payload(receipt: E0BaselineAccountingReceipt) -> dict[str, object]:
    payload = asdict(receipt)
    payload.pop("receipt_sha256")
    payload["inventory_status_counts"] = [list(row) for row in receipt.inventory_status_counts]
    payload["exact_read_status_counts"] = [list(row) for row in receipt.exact_read_status_counts]
    payload["context_omission_reason_counts"] = [list(row) for row in receipt.context_omission_reason_counts]
    payload["context_retrieval_miss_status_counts"] = [list(row) for row in receipt.context_retrieval_miss_status_counts]
    return payload


def _valid_inventory(snapshot: SourceSnapshot, inventory: SnapshotInventoryReceipt) -> bool:
    if type(inventory) is not SnapshotInventoryReceipt:
        return False
    try:
        inventory_bytes = json.dumps(_inventory_payload(inventory), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(inventory_bytes) > 64 * 1024 or _sha256(inventory_bytes) != inventory.receipt_sha256:
            return False
        names = tuple(sorted(status.value for status in CoverageFileStatus))
        if (
            inventory.schema != "wrench.snapshot-inventory.v1"
            or inventory.snapshot_sha256 != snapshot.snapshot_sha256
            or inventory.root_location_sha256 != snapshot.root_location_sha256
            or inventory.root_identity != snapshot.root_identity
            or inventory.supplied_manifest_only is not True
            or not _is_int(inventory.entry_count)
            or inventory.entry_count < 1
            or inventory.entry_count != len(snapshot.sources)
            or not _is_int(inventory.page_size)
            or inventory.page_size <= 0
            or inventory.page_size != INVENTORY_PAGE_SIZE
            or tuple(name for name, _ in inventory.status_counts) != names
            or any(type(count) is not int or count < 0 for _, count in inventory.status_counts)
            or sum(count for _, count in inventory.status_counts) != inventory.entry_count
            or type(inventory.complete) is not bool
            or inventory.complete is not (dict(inventory.status_counts).get(CoverageFileStatus.INDEXED.value) == inventory.entry_count)
            or not _is_int(inventory.exact_read_attempts)
            or not _is_int(inventory.exact_read_successes)
            or not _is_int(inventory.exact_read_returned_bytes)
            or inventory.exact_read_attempts != inventory.entry_count
            or inventory.exact_read_successes != dict(inventory.exact_read_status_counts).get("ok", 0)
            or not 0 <= inventory.exact_read_returned_bytes <= 4 * 1024 * 1024
            or tuple(name for name, _ in inventory.exact_read_status_counts) != tuple(sorted(dict(inventory.exact_read_status_counts)))
            or any(name not in _READ_STATUS_NAMES or type(count) is not int or count < 0 for name, count in inventory.exact_read_status_counts)
            or sum(count for _, count in inventory.exact_read_status_counts) != inventory.exact_read_attempts
            or len(inventory.pages) != (inventory.entry_count + inventory.page_size - 1) // inventory.page_size
        ):
            return False
        chain = "0" * 64
        page_status_totals = {name: 0 for name in names}
        sources = snapshot.sources
        for page_index, page in enumerate(inventory.pages):
            offset = page_index * inventory.page_size
            paths = tuple(source.path for source in sources[offset:offset + inventory.page_size])
            page_counts = dict(page.status_counts)
            if (
                not _is_int(page.page_index)
                or not _is_int(page.entry_count)
                or page.page_index != page_index
                or page.entry_count != len(paths)
                or page.first_path != paths[0]
                or page.last_path != paths[-1]
                or tuple(name for name, _ in page.status_counts) != names
                or sum(page_counts.values()) != page.entry_count
                or not _DIGEST.fullmatch(page.coverage_sha256)
            ):
                return False
            for name, count in page.status_counts:
                if type(count) is not int or count < 0:
                    return False
                page_status_totals[name] += count
            page_payload = {
                "schema": "wrench.snapshot-inventory-page.v1",
                "snapshot_sha256": snapshot.snapshot_sha256,
                "root_location_sha256": snapshot.root_location_sha256,
                "root_identity": snapshot.root_identity,
                "page_index": page_index,
                "first_path": page.first_path,
                "last_path": page.last_path,
                "entry_count": page.entry_count,
                "coverage_sha256": page.coverage_sha256,
                "status_counts": [list(row) for row in page.status_counts],
            }
            if _sha256(_canonical(page_payload)) != page.page_sha256:
                return False
            chain = _sha256(json.dumps({"previous": chain, "page_sha256": page.page_sha256}, sort_keys=True, separators=(",", ":")).encode("ascii"))
        if page_status_totals != dict(inventory.status_counts) or chain != inventory.page_hash_chain_sha256:
            return False
        return True
    except (AttributeError, TypeError, ValueError, UnicodeError, RecursionError):
        return False


def _incomplete_inventory_matches_misses(
    miss_status_counts: tuple[tuple[str, int], ...],
    exact_read_status_counts: tuple[tuple[str, int], ...],
    inventory_status_counts: tuple[tuple[str, int], ...],
) -> bool:
    """Join source-miss aggregates to the fresh exact-read and coverage bins."""
    exact_mapping = {
        "stale": "changed", "missing": "missing", "unsafe": "unsafe",
        "unknown_snapshot": "unknown_snapshot", "unknown_source": "unknown_source",
    }
    coverage_mapping = {
        "stale": CoverageFileStatus.STALE.value,
        "missing": CoverageFileStatus.MISSING.value,
        "unsafe": CoverageFileStatus.ERROR.value,
        "unknown_snapshot": CoverageFileStatus.ERROR.value,
        "unknown_source": CoverageFileStatus.ERROR.value,
        "non_text": CoverageFileStatus.NON_TEXT.value,
        "limit_exceeded": CoverageFileStatus.LIMIT_EXCEEDED.value,
    }
    exact_counts = dict(exact_read_status_counts)
    coverage_counts = dict(inventory_status_counts)
    expected_exact: dict[str, int] = {}
    expected_coverage: dict[str, int] = {}
    for miss_status, count in miss_status_counts:
        exact_status = exact_mapping.get(miss_status)
        if exact_status is not None:
            expected_exact[exact_status] = expected_exact.get(exact_status, 0) + count
        coverage_status = coverage_mapping.get(miss_status)
        if coverage_status is not None:
            expected_coverage[coverage_status] = expected_coverage.get(coverage_status, 0) + count
    return all(exact_counts.get(name, 0) >= count for name, count in expected_exact.items()) and all(
        coverage_counts.get(name, 0) >= count for name, count in expected_coverage.items()
    )


def build_e0_baseline_accounting_receipt(
    project_snapshot: OpenCodeProjectSnapshot,
    inventory: SnapshotInventoryReceipt,
    composition_receipt: OfflineCompositionReceipt,
    finalized_composition_receipt: OfflineCompositionReceipt,
    post_insertion_event: Mapping[str, object] | None,
    lowered_request: LoweredRequest | None,
) -> E0BaselineAccountingReceipt:
    """Join root-bound inventory and complete synthetic fixture composition.

    ``enrolled_omission_count`` is deliberately null: the snapshot API accepts
    an explicitly selected finite path set and carries no full enrolled-path
    manifest into this accounting boundary.
    """
    if (
        type(project_snapshot) is not OpenCodeProjectSnapshot
        or type(composition_receipt) is not OfflineCompositionReceipt
        or type(finalized_composition_receipt) is not OfflineCompositionReceipt
        or type(project_snapshot.binding) is not SourceRootBinding
        or project_snapshot.snapshot is None
        or not _validate_snapshot(project_snapshot.snapshot)
    ):
        raise ValueError("baseline_accounting_input_invalid")
    snapshot = project_snapshot.snapshot
    try:
        current_binding = bind_source_root(project_snapshot.binding.configured_root)
        fresh_inventory = build_snapshot_inventory_receipt(snapshot, project_snapshot.binding)
    except (OSError, TypeError, ValueError):
        raise ValueError("baseline_accounting_source_freshness_invalid") from None
    if (
        composition_receipt.accounting_state == "incomplete_preparation"
        and finalized_composition_receipt.accounting_state == "incomplete_preparation"
    ):
        if (
            current_binding.root_location_sha256 != snapshot.root_location_sha256
            or current_binding.root_identity != snapshot.root_identity
            or project_snapshot.binding.root_location_sha256 != snapshot.root_location_sha256
            or project_snapshot.binding.root_identity != snapshot.root_identity
            or set(project_snapshot.selected_paths) != {source.path for source in snapshot.sources}
            or not _valid_inventory(snapshot, inventory)
            or fresh_inventory != inventory
            or inventory.complete is not False
            or dict(inventory.status_counts).get(CoverageFileStatus.INDEXED.value, 0) >= inventory.entry_count
            or not verify_offline_e0_composition_receipt(composition_receipt)
            or not verify_offline_e0_composition_receipt(finalized_composition_receipt)
            or _composition_payload(composition_receipt, terminal_outcome=None)
            != _composition_payload(finalized_composition_receipt, terminal_outcome=None)
            or composition_receipt.snapshot_sha256 != snapshot.snapshot_sha256
            or composition_receipt.preparation_status != "source_misses"
            or composition_receipt.preparation_outcome_status != "incomplete"
            or not _incomplete_inventory_matches_misses(
                composition_receipt.retrieval_miss_status_counts,
                inventory.exact_read_status_counts,
                inventory.status_counts,
            )
            or lowered_request is not None
            or post_insertion_event is not None
        ):
            raise ValueError("baseline_accounting_incomplete_join_invalid")
        partial = E0BaselineAccountingReceipt(
            schema=_SCHEMA,
            provenance="synthetic_fixture_supplied_manifest_only",
            snapshot_sha256=snapshot.snapshot_sha256,
            root_location_sha256=snapshot.root_location_sha256 or "",
            root_identity=snapshot.root_identity or "",
            inventory_receipt_sha256=inventory.receipt_sha256,
            inventory_entry_count=inventory.entry_count,
            inventory_status_counts=inventory.status_counts,
            inventory_complete=False,
            exact_read_attempts=inventory.exact_read_attempts,
            exact_read_successes=inventory.exact_read_successes,
            exact_read_returned_bytes=inventory.exact_read_returned_bytes,
            exact_read_status_counts=inventory.exact_read_status_counts,
            accounted_snapshot_manifest_entries=inventory.exact_read_successes,
            unaccounted_snapshot_manifest_entries=inventory.entry_count - inventory.exact_read_successes,
            enrolled_omission_count=None,
            preparation_sha256=composition_receipt.preparation_sha256,
            preparation_outcome_receipt_sha256=composition_receipt.preparation_outcome_receipt_sha256,
            preparation_outcome_receipt_validation_status=composition_receipt.preparation_outcome_receipt_validation_status,
            preparation_outcome_status=composition_receipt.preparation_outcome_status,
            preparation_status=composition_receipt.preparation_status,
            route_preparation_sha256=None,
            insertion_receipt_sha256=None,
            semantic_projection_sha256=None,
            context_candidate_count=composition_receipt.candidate_count,
            context_selected_candidate_order_sha256=None,
            context_selected_evidence_count=composition_receipt.selected_evidence_count,
            context_omitted_evidence_count=composition_receipt.omitted_evidence_count,
            context_omission_reason_counts=composition_receipt.omission_reason_counts,
            context_retrieval_miss_count=composition_receipt.retrieval_miss_count,
            context_retrieval_miss_status_counts=composition_receipt.retrieval_miss_status_counts,
            accounting_state="incomplete_preparation",
            synthetic_serializer_id=SYNTHETIC_SERIALIZER_ID,
            synthetic_envelope_sha256=None,
            synthetic_envelope_bytes=None,
            synthetic_envelope_chars=None,
            synthetic_tokenizer_id=SYNTHETIC_TOKENIZER_ID,
            exact_token_gate="exact_gate_unavailable",
            synthetic_token_count=None,
            lowered_request_body_sha256=None,
            lowered_request_body_bytes=None,
            terminal_outcome=None,
            composition_receipt_sha256=composition_receipt.receipt_sha256,
            receipt_sha256="0" * 64,
        )
        digest = _sha256(_canonical(_payload(partial)))
        return E0BaselineAccountingReceipt(**{**asdict(partial), "receipt_sha256": digest})
    if (
        current_binding.root_location_sha256 != snapshot.root_location_sha256
        or current_binding.root_identity != snapshot.root_identity
        or project_snapshot.binding.root_location_sha256 != snapshot.root_location_sha256
        or project_snapshot.binding.root_identity != snapshot.root_identity
        or set(project_snapshot.selected_paths) != {source.path for source in snapshot.sources}
        or not _valid_inventory(snapshot, inventory)
        or fresh_inventory != inventory
        or inventory.complete is not True
        or composition_receipt.accounting_state != "complete"
        or not verify_offline_e0_composition_receipt(composition_receipt)
        or composition_receipt.terminal_outcome is not None
        or not verify_offline_e0_composition_receipt(finalized_composition_receipt)
        or finalized_composition_receipt.terminal_outcome not in {end.value for end in StreamEnd}
        or composition_receipt.snapshot_sha256 != snapshot.snapshot_sha256
        or finalized_composition_receipt.snapshot_sha256 != snapshot.snapshot_sha256
    ):
        if type(lowered_request) is not LoweredRequest or not isinstance(post_insertion_event, Mapping):
            raise ValueError("baseline_accounting_input_invalid")
        raise ValueError("baseline_accounting_identity_or_inventory_invalid")
    before_payload = _composition_payload(composition_receipt, terminal_outcome=None)
    after_payload = _composition_payload(finalized_composition_receipt, terminal_outcome=finalized_composition_receipt.terminal_outcome)
    if any(before_payload[key] != after_payload[key] for key in before_payload if key != "terminal_outcome"):
        raise ValueError("baseline_accounting_terminal_join_invalid")
    if lowered_request.method != "POST" or lowered_request.url != "/v1/chat/completions" or type(lowered_request.body) is not bytes:
        raise ValueError("baseline_accounting_lowered_request_invalid")
    if _sha256(lowered_request.body) != composition_receipt.request_body_sha256:
        raise ValueError("baseline_accounting_lowered_body_mismatch")

    projected = project_opencode_context_hook(dict(post_insertion_event))
    if projected.status.value != "ready" or projected.projection is None:
        raise ValueError("baseline_accounting_projection_invalid")
    projection = projected.projection
    if projection.projection_sha256 != composition_receipt.semantic_projection_sha256:
        raise ValueError("baseline_accounting_projection_join_invalid")
    semantic_payload = json.loads(projection.payload_json)
    serializer = _fixture_serializer_for_projection(semantic_payload)
    synthetic_envelope = serializer(semantic_payload["messages"])
    envelope_bytes = synthetic_envelope.encode("utf-8")
    if _sha256(lowered_request.body) != composition_receipt.request_body_sha256:
        raise ValueError("baseline_accounting_body_join_invalid")

    statuses = tuple(inventory.status_counts)
    if (
        sum(count for _, count in statuses) != inventory.entry_count
        or inventory.exact_read_attempts != inventory.entry_count
        or inventory.exact_read_successes != inventory.entry_count
        or inventory.exact_read_status_counts != (("ok", inventory.entry_count),)
    ):
        raise ValueError("baseline_accounting_unaccounted_inventory")
    partial = E0BaselineAccountingReceipt(
        schema=_SCHEMA,
        provenance="synthetic_fixture_supplied_manifest_only",
        snapshot_sha256=snapshot.snapshot_sha256,
        root_location_sha256=snapshot.root_location_sha256 or "",
        root_identity=snapshot.root_identity or "",
        inventory_receipt_sha256=inventory.receipt_sha256,
        inventory_entry_count=inventory.entry_count,
        inventory_status_counts=statuses,
        inventory_complete=True,
        exact_read_attempts=inventory.exact_read_attempts,
        exact_read_successes=inventory.exact_read_successes,
        exact_read_returned_bytes=inventory.exact_read_returned_bytes,
        exact_read_status_counts=inventory.exact_read_status_counts,
        accounted_snapshot_manifest_entries=inventory.entry_count,
        unaccounted_snapshot_manifest_entries=0,
        enrolled_omission_count=None,
        preparation_sha256=composition_receipt.preparation_sha256,
        preparation_outcome_receipt_sha256=composition_receipt.preparation_outcome_receipt_sha256,
        preparation_outcome_receipt_validation_status=composition_receipt.preparation_outcome_receipt_validation_status,
        preparation_outcome_status=composition_receipt.preparation_outcome_status,
        preparation_status=composition_receipt.preparation_status,
        route_preparation_sha256=composition_receipt.route_preparation_sha256,
        insertion_receipt_sha256=composition_receipt.insertion_receipt_sha256,
        semantic_projection_sha256=projection.projection_sha256,
        context_candidate_count=composition_receipt.candidate_count,
        context_selected_candidate_order_sha256=composition_receipt.selected_candidate_order_sha256,
        context_selected_evidence_count=composition_receipt.selected_evidence_count,
        context_omitted_evidence_count=composition_receipt.omitted_evidence_count,
        context_omission_reason_counts=composition_receipt.omission_reason_counts,
        context_retrieval_miss_count=composition_receipt.retrieval_miss_count,
        context_retrieval_miss_status_counts=composition_receipt.retrieval_miss_status_counts,
        accounting_state="complete",
        synthetic_serializer_id=SYNTHETIC_SERIALIZER_ID,
        synthetic_envelope_sha256=_sha256(envelope_bytes),
        synthetic_envelope_bytes=len(envelope_bytes),
        synthetic_envelope_chars=len(synthetic_envelope),
        synthetic_tokenizer_id=SYNTHETIC_TOKENIZER_ID,
        exact_token_gate="exact_gate_unavailable",
        synthetic_token_count=_fixture_tokenizer(synthetic_envelope),
        lowered_request_body_sha256=_sha256(lowered_request.body),
        lowered_request_body_bytes=len(lowered_request.body),
        terminal_outcome=finalized_composition_receipt.terminal_outcome,
        composition_receipt_sha256=finalized_composition_receipt.receipt_sha256,
        receipt_sha256="0" * 64,
    )
    digest = _sha256(_canonical(_payload(partial)))
    return E0BaselineAccountingReceipt(**{**asdict(partial), "receipt_sha256": digest})


def verify_e0_baseline_accounting_receipt(receipt: E0BaselineAccountingReceipt) -> bool:
    """Verify content-free complete and incomplete receipt variants separately."""
    if type(receipt) is not E0BaselineAccountingReceipt:
        return False
    try:
        names = tuple(sorted(status.value for status in CoverageFileStatus))
        if (
            receipt.schema != _SCHEMA
            or receipt.provenance != "synthetic_fixture_supplied_manifest_only"
            or type(receipt.inventory_complete) is not bool
            or not _is_int(receipt.inventory_entry_count) or not 1 <= receipt.inventory_entry_count <= 256
            or not _is_int(receipt.context_candidate_count) or not 0 <= receipt.context_candidate_count <= 10_000
            or receipt.enrolled_omission_count is not None
            or receipt.synthetic_serializer_id != SYNTHETIC_SERIALIZER_ID
            or receipt.synthetic_tokenizer_id != SYNTHETIC_TOKENIZER_ID
            or receipt.exact_token_gate != "exact_gate_unavailable"
            or receipt.preparation_outcome_receipt_validation_status != "valid"
            or receipt.preparation_outcome_status != "incomplete"
            or tuple(name for name, _ in receipt.inventory_status_counts) != names
            or any(not _is_int(value) or value < 0 for _, value in receipt.inventory_status_counts)
            or sum(value for _, value in receipt.inventory_status_counts) != receipt.inventory_entry_count
            or receipt.accounted_snapshot_manifest_entries + receipt.unaccounted_snapshot_manifest_entries != receipt.inventory_entry_count
            or receipt.exact_read_attempts != receipt.inventory_entry_count
            or not _is_int(receipt.inventory_entry_count)
            or not _is_int(receipt.exact_read_attempts)
            or not _is_int(receipt.exact_read_successes)
            or not _is_int(receipt.accounted_snapshot_manifest_entries)
            or not _is_int(receipt.unaccounted_snapshot_manifest_entries)
            or not _is_int(receipt.exact_read_returned_bytes)
            or not 0 <= receipt.exact_read_returned_bytes <= 4 * 1024 * 1024
            or tuple(name for name, _ in receipt.exact_read_status_counts) != tuple(sorted(dict(receipt.exact_read_status_counts)))
            or any(name not in _READ_STATUS_NAMES or type(value) is not int or value < 0 for name, value in receipt.exact_read_status_counts)
            or sum(value for _, value in receipt.exact_read_status_counts) != receipt.exact_read_attempts
            or dict(receipt.exact_read_status_counts).get("ok", 0) != receipt.exact_read_successes
            or type(receipt.root_identity) is not str
            or not receipt.root_identity
            or not _is_int(receipt.context_selected_evidence_count) or receipt.context_selected_evidence_count < 0
            or not _is_int(receipt.context_omitted_evidence_count) or receipt.context_omitted_evidence_count < 0
            or not _is_int(receipt.context_retrieval_miss_count) or receipt.context_retrieval_miss_count < 0
            or tuple(name for name, _ in receipt.context_omission_reason_counts) != tuple(sorted(dict(receipt.context_omission_reason_counts)))
            or tuple(name for name, _ in receipt.context_retrieval_miss_status_counts) != tuple(sorted(dict(receipt.context_retrieval_miss_status_counts)))
            or any(type(name) is not str or not name or type(value) is not int or value < 0 for name, value in (*receipt.context_omission_reason_counts, *receipt.context_retrieval_miss_status_counts))
            or any(name not in _OMISSION_REASONS for name, _ in receipt.context_omission_reason_counts)
            or any(name not in _MISS_STATUSES for name, _ in receipt.context_retrieval_miss_status_counts)
            or sum(value for _, value in receipt.context_omission_reason_counts) != receipt.context_omitted_evidence_count
            or sum(value for _, value in receipt.context_retrieval_miss_status_counts) != receipt.context_retrieval_miss_count
            or (receipt.route_preparation_sha256 is not None and not _DIGEST.fullmatch(receipt.route_preparation_sha256))
        ):
            return False
        common_digests = (
            receipt.snapshot_sha256, receipt.root_location_sha256, receipt.inventory_receipt_sha256,
            receipt.preparation_sha256, receipt.preparation_outcome_receipt_sha256,
            receipt.composition_receipt_sha256,
        )
        if not all(type(value) is str and _DIGEST.fullmatch(value) for value in common_digests):
            return False
        if _sha256(_canonical(_payload(receipt))) != receipt.receipt_sha256:
            return False
        if receipt.accounting_state == "incomplete_preparation":
            return (
                receipt.inventory_complete is False
                and dict(receipt.inventory_status_counts).get(CoverageFileStatus.INDEXED.value, 0) < receipt.inventory_entry_count
                and receipt.accounted_snapshot_manifest_entries == receipt.exact_read_successes
                and receipt.unaccounted_snapshot_manifest_entries == receipt.inventory_entry_count - receipt.exact_read_successes
                and receipt.preparation_status == "source_misses"
                and receipt.preparation_outcome_status == "incomplete"
                and receipt.context_retrieval_miss_count > 0
                and _incomplete_inventory_matches_misses(
                    receipt.context_retrieval_miss_status_counts,
                    receipt.exact_read_status_counts,
                    receipt.inventory_status_counts,
                )
                and receipt.context_selected_candidate_order_sha256 is None
                and receipt.route_preparation_sha256 is None
                and receipt.insertion_receipt_sha256 is None
                and receipt.semantic_projection_sha256 is None
                and receipt.synthetic_envelope_sha256 is None
                and receipt.synthetic_envelope_bytes is None
                and receipt.synthetic_envelope_chars is None
                and receipt.synthetic_token_count is None
                and receipt.lowered_request_body_sha256 is None
                and receipt.lowered_request_body_bytes is None
                and receipt.terminal_outcome is None
            )
        if receipt.accounting_state != "complete":
            return False
        return (
            receipt.inventory_complete is True
            and receipt.exact_read_successes == receipt.inventory_entry_count
            and receipt.accounted_snapshot_manifest_entries == receipt.inventory_entry_count
            and receipt.unaccounted_snapshot_manifest_entries == 0
            and dict(receipt.inventory_status_counts).get(CoverageFileStatus.INDEXED.value, 0) == receipt.inventory_entry_count
            and _is_int(receipt.context_candidate_count) and receipt.context_candidate_count >= 1
            and receipt.preparation_status == "ready"
            and receipt.terminal_outcome in {end.value for end in StreamEnd}
            and all(_DIGEST.fullmatch(value) for value in (
                receipt.insertion_receipt_sha256, receipt.semantic_projection_sha256,
                receipt.context_selected_candidate_order_sha256, receipt.synthetic_envelope_sha256,
                receipt.lowered_request_body_sha256,
            ))
            and _is_int(receipt.synthetic_envelope_bytes) and receipt.synthetic_envelope_bytes >= 1
            and _is_int(receipt.synthetic_envelope_chars) and receipt.synthetic_envelope_chars >= 1
            and _is_int(receipt.synthetic_token_count) and receipt.synthetic_token_count == receipt.synthetic_envelope_chars
            and _is_int(receipt.lowered_request_body_bytes) and 1 <= receipt.lowered_request_body_bytes <= MAX_REQUEST_BYTES
        )
    except (AttributeError, TypeError, ValueError, UnicodeError, RecursionError):
        return False


__all__ = ["E0BaselineAccountingReceipt", "build_e0_baseline_accounting_receipt", "verify_e0_baseline_accounting_receipt"]
