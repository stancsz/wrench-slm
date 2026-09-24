"""Bounded no-model composition of the E0 rule route and context preparation.

This module owns both sides of the local route-to-preparation join. It only
prepares exact source paths returned by its own invocation of the snapshot
bound rule route. The receipt is structural accounting, not authenticated
user intent, client dispatch, or downstream call accounting.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping, Sequence

from .artifact_store import ArtifactRequest, ArtifactStore
from .e0_context_pipeline import (
    PreparationAccountingReceipt,
    PreparationResult,
    PreparationStatus,
    SourceIdentity,
    prepare_e0_context,
    verify_preparation_accounting_receipt,
)
from .e0_rule_route import RuleRouteEvidence, RuleRouteResult, RuleRouteStatus, run_e0_rule_route
from .namespace_registry import NamespaceRegistry
from .snapshot import SourceRootBinding, SourceSnapshot


ROUTE_PREPARATION_ACCOUNTING_SCHEMA = "wrench.e0.route-preparation-accounting.v1"
MAX_ROUTE_PREPARATION_RECEIPT_BYTES = 16 * 1024
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_ACTIONS = frozenset({"read_file", "read_lines", "literal_search"})


class RoutePreparationStatus(str, Enum):
    JOINED = "joined"
    ROUTE_NOT_COMPLETED = "route_not_completed"
    EVIDENCE_JOIN_MISMATCH = "evidence_join_mismatch"
    ACCOUNTING_UNAVAILABLE = "accounting_unavailable"


@dataclass(frozen=True)
class RoutePreparationAccountingReceipt:
    schema: str
    snapshot_sha256: str
    accounting_sha256: str
    preparation_sha256: str
    preparation_accounting_sha256: str
    payload_json: str


@dataclass(frozen=True)
class RoutePreparationResult:
    status: RoutePreparationStatus
    route_result: RuleRouteResult
    preparation: PreparationResult | None
    accounting_receipt: RoutePreparationAccountingReceipt | None
    reason: str


def route_and_prepare_e0_context(
    route_prompt: str,
    *,
    root_binding: SourceRootBinding,
    snapshot: SourceSnapshot,
    store: ArtifactStore,
    query: str,
    source_order_start: int,
    context_token_budget: int,
    prompt_token_budget: int,
    namespace_registry: NamespaceRegistry,
    schema_lookups: Sequence[tuple[str, str]],
    base_messages: Sequence[Mapping[str, object]],
    context_position: int,
    message_format: str = "generic",
    serializer: Callable[[Sequence[Mapping[str, object]]], str | bytes],
    tokenizer_counter: Callable[[str | bytes], int],
    serializer_id: str,
    tokenizer_id: str,
    max_candidates: int = 8,
    artifact_request: ArtifactRequest | None = None,
) -> RoutePreparationResult:
    """Run a bounded route, then prepare only its successful exact evidence.

    The function deliberately accepts a route prompt and snapshot inputs, not
    a caller-constructed ``RuleRouteResult`` or a caller-selected path list.
    Only a complete route with nonempty, unique, hash-bearing ``ok`` evidence
    proceeds to preparation. Those paths are all required and preserved.
    """
    route = run_e0_rule_route(
        route_prompt, root_binding=root_binding, snapshot=snapshot
    )
    if (
        type(snapshot) is not SourceSnapshot
        or type(root_binding) is not SourceRootBinding
        or not _valid_completed_route(route)
        or route.snapshot_sha256 != snapshot.snapshot_sha256
    ):
        return RoutePreparationResult(
            RoutePreparationStatus.ROUTE_NOT_COMPLETED,
            route,
            None,
            None,
            route.reason or "route_not_completed",
        )

    route_evidence = route.evidence
    if _evidence_rows(route_evidence) is None:
        return RoutePreparationResult(
            RoutePreparationStatus.ROUTE_NOT_COMPLETED,
            route,
            None,
            None,
            "route_evidence_invalid",
        )
    paths = tuple(item.path for item in route_evidence)
    if len(set(paths)) != len(paths):
        return RoutePreparationResult(
            RoutePreparationStatus.ROUTE_NOT_COMPLETED,
            route,
            None,
            None,
            "route_evidence_paths_duplicate",
        )

    preparation = prepare_e0_context(
        source_root=root_binding,
        snapshot=snapshot,
        paths=paths,
        store=store,
        query=query,
        source_order_start=source_order_start,
        context_token_budget=context_token_budget,
        prompt_token_budget=prompt_token_budget,
        namespace_registry=namespace_registry,
        schema_lookups=schema_lookups,
        base_messages=base_messages,
        context_position=context_position,
        message_format=message_format,
        serializer=serializer,
        tokenizer_counter=tokenizer_counter,
        serializer_id=serializer_id,
        tokenizer_id=tokenizer_id,
        required_source_paths=paths,
        preserve_source_paths=paths,
        max_candidates=max_candidates,
        artifact_request=artifact_request,
    )

    route_hashes = {item.path: item.content_sha256 for item in route_evidence}
    prepared_rows = {
        item.path: item.content_sha256
        for item in preparation.sources
        if item.status == "ok"
    }
    if prepared_rows != route_hashes:
        return RoutePreparationResult(
            RoutePreparationStatus.EVIDENCE_JOIN_MISMATCH,
            route,
            preparation,
            None,
            "prepared_source_hashes_do_not_match_route",
        )
    accounting = preparation.accounting_receipt
    if (
        type(preparation.aggregate_sha256) is not str
        or not _DIGEST.fullmatch(preparation.aggregate_sha256)
        or type(accounting) is not PreparationAccountingReceipt
        or not verify_preparation_accounting_receipt(
            accounting, aggregate_sha256=preparation.aggregate_sha256
        )
    ):
        return RoutePreparationResult(
            RoutePreparationStatus.ACCOUNTING_UNAVAILABLE,
            route,
            preparation,
            None,
            "preparation_accounting_invalid_or_unavailable",
        )

    receipt = _make_receipt(route, route_evidence, preparation)
    if receipt is None:
        return RoutePreparationResult(
            RoutePreparationStatus.ACCOUNTING_UNAVAILABLE,
            route,
            preparation,
            None,
            "route_preparation_receipt_invalid_or_too_large",
        )
    return RoutePreparationResult(
        RoutePreparationStatus.JOINED, route, preparation, receipt, "joined"
    )


def verify_route_preparation_accounting_receipt(
    receipt: RoutePreparationAccountingReceipt,
    *,
    route_result: RuleRouteResult,
    preparation: PreparationResult,
) -> bool:
    """Validate canonical form, digest, and supplied route/preparation joins.

    Inputs remain caller-supplied and unauthenticated. This verifier checks
    structure and accidental mutation only.
    """
    if (
        type(receipt) is not RoutePreparationAccountingReceipt
        or receipt.schema != ROUTE_PREPARATION_ACCOUNTING_SCHEMA
        or type(receipt.payload_json) is not str
        or type(route_result) is not RuleRouteResult
        or type(preparation) is not PreparationResult
        or not _valid_completed_route(route_result)
        or type(preparation.status) is not PreparationStatus
        or type(preparation.aggregate_sha256) is not str
        or not _DIGEST.fullmatch(preparation.aggregate_sha256)
        or type(preparation.accounting_receipt) is not PreparationAccountingReceipt
        or not verify_preparation_accounting_receipt(
            preparation.accounting_receipt,
            aggregate_sha256=preparation.aggregate_sha256,
        )
    ):
        return False
    try:
        payload_bytes = receipt.payload_json.encode("utf-8")
        if len(payload_bytes) > MAX_ROUTE_PREPARATION_RECEIPT_BYTES:
            return False
        payload = json.loads(receipt.payload_json)
        raw = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return False
    if (
        type(payload) is not dict
        or len(raw) > MAX_ROUTE_PREPARATION_RECEIPT_BYTES
        or raw.decode("utf-8") != receipt.payload_json
        or hashlib.sha256(raw).hexdigest() != receipt.accounting_sha256
        or payload.get("schema") != ROUTE_PREPARATION_ACCOUNTING_SCHEMA
        or payload.get("snapshot_sha256") != route_result.snapshot_sha256
        or payload.get("route_status") != route_result.status.value
        or payload.get("route") != route_result.route
        or payload.get("action") != route_result.action
        or payload.get("route_counters") != _route_counters(route_result)
        or payload.get("preparation_sha256") != preparation.aggregate_sha256
        or payload.get("preparation_accounting_sha256")
        != preparation.accounting_receipt.accounting_sha256
        or receipt.snapshot_sha256 != route_result.snapshot_sha256
        or receipt.preparation_sha256 != preparation.aggregate_sha256
        or receipt.preparation_accounting_sha256
        != preparation.accounting_receipt.accounting_sha256
    ):
        return False
    if set(payload) != {
        "schema", "snapshot_sha256", "route_status", "route", "action",
        "route_counters", "route_evidence", "preparation_status",
        "preparation_sha256", "preparation_accounting_sha256", "evidence_join",
    }:
        return False
    expected_evidence = _evidence_rows(route_result.evidence)
    expected_join = _join_rows(route_result.evidence, preparation.sources)
    return (
        expected_evidence is not None
        and expected_join is not None
        and payload.get("route_evidence") == expected_evidence
        and payload.get("evidence_join") == expected_join
        and payload.get("preparation_status") == preparation.status.value
    )


def _make_receipt(
    route: RuleRouteResult,
    route_evidence: tuple,
    preparation: PreparationResult,
) -> RoutePreparationAccountingReceipt | None:
    evidence_rows = _evidence_rows(route_evidence)
    join_rows = _join_rows(route_evidence, preparation.sources)
    accounting = preparation.accounting_receipt
    if evidence_rows is None or join_rows is None or accounting is None:
        return None
    payload = {
        "schema": ROUTE_PREPARATION_ACCOUNTING_SCHEMA,
        "snapshot_sha256": route.snapshot_sha256,
        "route_status": route.status.value,
        "route": route.route,
        "action": route.action,
        "route_counters": _route_counters(route),
        "route_evidence": evidence_rows,
        "preparation_status": preparation.status.value,
        "preparation_sha256": preparation.aggregate_sha256,
        "preparation_accounting_sha256": accounting.accounting_sha256,
        "evidence_join": join_rows,
    }
    try:
        raw = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return None
    if len(raw) > MAX_ROUTE_PREPARATION_RECEIPT_BYTES:
        return None
    digest = hashlib.sha256(raw).hexdigest()
    return RoutePreparationAccountingReceipt(
        ROUTE_PREPARATION_ACCOUNTING_SCHEMA,
        route.snapshot_sha256,
        digest,
        preparation.aggregate_sha256,
        accounting.accounting_sha256,
        raw.decode("utf-8"),
    )


def _route_counters(route: RuleRouteResult) -> dict[str, int]:
    return {
        "exact_read_attempts": route.exact_read_attempts,
        "exact_read_successes": route.exact_read_successes,
        "exact_read_bytes": route.exact_read_bytes,
    }


def _valid_completed_route(route: RuleRouteResult) -> bool:
    return (
        type(route.status) is RuleRouteStatus
        and route.status is RuleRouteStatus.COMPLETED
        and type(route.route) is str
        and route.route == "none"
        and type(route.action) is str
        and route.action in _ALLOWED_ACTIONS
        and type(route.snapshot_sha256) is str
        and _DIGEST.fullmatch(route.snapshot_sha256) is not None
        and type(route.exact_read_attempts) is int
        and type(route.exact_read_successes) is int
        and type(route.exact_read_bytes) is int
        and 1 <= route.exact_read_attempts <= 16
        and route.exact_read_successes == route.exact_read_attempts
        and 0 <= route.exact_read_bytes <= 512 * 1024
        and type(route.evidence) is tuple
        and bool(route.evidence)
        and len(route.evidence) <= 16
        and type(route.unknown_evidence) is tuple
        and not route.unknown_evidence
    )


def _evidence_rows(evidence: tuple) -> list[dict[str, object]] | None:
    if type(evidence) is not tuple or len(evidence) > 16:
        return None
    rows = []
    seen: set[str] = set()
    for item in evidence:
        if (
            type(item) is not RuleRouteEvidence
            or item.status != "ok"
            or type(item.path) is not str
            or not item.path
            or len(item.path) > 1024
            or type(item.content_sha256) is not str
            or not _DIGEST.fullmatch(item.content_sha256)
            or type(item.size_bytes) is not int
            or not 0 <= item.size_bytes <= 256 * 1024
        ):
            return None
        try:
            path_ref = hashlib.sha256(item.path.encode("utf-8")).hexdigest()
        except UnicodeError:
            return None
        if path_ref in seen:
            return None
        seen.add(path_ref)
        rows.append({
            "path_ref_sha256": path_ref,
            "status": item.status,
            "content_sha256": item.content_sha256,
            "size_bytes": item.size_bytes,
        })
    return rows


def _join_rows(route_evidence: tuple, sources: tuple) -> list[dict[str, str]] | None:
    route_rows = _evidence_rows(route_evidence)
    if (
        route_rows is None
        or type(sources) is not tuple
        or len(sources) > 16
        or any(type(source) is not SourceIdentity for source in sources)
        or any(
            type(source.path) is not str
            or not source.path
            or len(source.path) > 1024
            or source.status != "ok"
            or type(source.content_sha256) is not str
            or not _DIGEST.fullmatch(source.content_sha256)
            for source in sources
        )
    ):
        return None
    source_by_path = {source.path: source for source in sources if source.status == "ok"}
    if len(source_by_path) != len(sources) or len(source_by_path) != len(route_evidence):
        return None
    route_by_path = {item.path: item for item in route_evidence}
    if set(source_by_path) != set(route_by_path):
        return None
    rows = []
    for path in sorted(route_by_path):
        route_item = route_by_path[path]
        source = source_by_path[path]
        if source.content_sha256 != route_item.content_sha256:
            return None
        rows.append({
            "path_ref_sha256": hashlib.sha256(path.encode("utf-8")).hexdigest(),
            "route_content_sha256": route_item.content_sha256,
            "preparation_content_sha256": source.content_sha256,
        })
    return rows


__all__ = [
    "MAX_ROUTE_PREPARATION_RECEIPT_BYTES",
    "ROUTE_PREPARATION_ACCOUNTING_SCHEMA",
    "RoutePreparationAccountingReceipt",
    "RoutePreparationResult",
    "RoutePreparationStatus",
    "route_and_prepare_e0_context",
    "verify_route_preparation_accounting_receipt",
]
