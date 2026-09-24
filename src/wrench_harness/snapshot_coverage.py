"""Content-free coverage receipt for an explicitly selected source subset.

This module never walks a repository. Every indexed source is fetched again
through the caller's snapshot and the existing structural-index byte limits.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable

from .snapshot import (
    MAX_SNAPSHOT_FILES,
    RetrievalStatus,
    SourceRootBinding,
    SourceSnapshot,
    _validate_snapshot,
    bind_source_root,
    retrieve_exact,
)
from .snapshot_structure import (
    MAX_AGGREGATE_BYTES,
    MAX_FILE_BYTES,
    MAX_FILES,
    MAX_SYMBOLS,
)
from .toolbelt import parse_source_ast


MAX_RECEIPT_BYTES = 64 * 1024
MAX_PATH_CHARS = 1024
MAX_SYNTAX_ERROR_CHARS = 1024
INVENTORY_PAGE_SIZE = MAX_FILES
MAX_INVENTORY_RECEIPT_BYTES = 64 * 1024


class CoverageFileStatus(str, Enum):
    INDEXED = "indexed"
    SYNTAX_ERROR = "syntax_error"
    UNSUPPORTED = "unsupported"
    MISSING = "missing"
    STALE = "stale"
    LIMIT_EXCEEDED = "limit_exceeded"
    NON_TEXT = "non_text"
    ERROR = "error"


@dataclass(frozen=True)
class SelectedFileCoverage:
    requested_path: str
    source_path: str | None
    source_sha256: str | None
    parser: str | None
    language: str | None
    symbol_count: int | None
    syntax_error: str | None
    status: CoverageFileStatus


@dataclass(frozen=True)
class SnapshotCoverageReceipt:
    schema: str
    snapshot_sha256: str | None
    selected_subset_only: bool
    requested_count: int
    requested_count_complete: bool
    indexed_count: int
    missing_count: int
    stale_count: int
    error_count: int
    unsupported_count: int
    limit_count: int
    exact_read_attempts: int
    exact_read_successes: int
    exact_read_returned_bytes: int
    exact_read_status_counts: tuple[tuple[str, int], ...]
    files: tuple[SelectedFileCoverage, ...]
    receipt_sha256: str


@dataclass(frozen=True)
class SnapshotInventoryPage:
    page_index: int
    entry_count: int
    first_path: str
    last_path: str
    coverage_sha256: str
    page_sha256: str
    status_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class SnapshotInventoryReceipt:
    schema: str
    snapshot_sha256: str
    root_location_sha256: str
    root_identity: str
    supplied_manifest_only: bool
    complete: bool
    entry_count: int
    page_size: int
    pages: tuple[SnapshotInventoryPage, ...]
    page_hash_chain_sha256: str
    status_counts: tuple[tuple[str, int], ...]
    exact_read_attempts: int
    exact_read_successes: int
    exact_read_returned_bytes: int
    exact_read_status_counts: tuple[tuple[str, int], ...]
    receipt_sha256: str


def _display_path(path: object) -> str:
    try:
        raw = os.fspath(path)
    except (TypeError, ValueError, OSError):
        raw = type(path).__name__
    if type(raw) is not str:
        raw = type(path).__name__
    return raw[:MAX_PATH_CHARS].replace("\\", "/")


def _receipt_digest_fields(receipt: SnapshotCoverageReceipt) -> dict[str, object]:
    value = asdict(receipt)
    value.pop("receipt_sha256")
    value["files"] = [
        {
            **asdict(row),
            "status": row.status.value,
        }
        for row in receipt.files
    ]
    value["exact_read_status_counts"] = [list(row) for row in receipt.exact_read_status_counts]
    return value


def _make_receipt(
    *, snapshot_sha256: str | None, requested_count: int, requested_count_complete: bool,
    files: tuple[SelectedFileCoverage, ...], missing_count: int, stale_count: int,
    error_count: int, unsupported_count: int, limit_count: int,
    exact_read_attempts: int, exact_read_successes: int, exact_read_returned_bytes: int,
    exact_read_status_counts: dict[str, int],
) -> SnapshotCoverageReceipt:
    partial = SnapshotCoverageReceipt(
        "wrench.snapshot-selected-coverage.v1", snapshot_sha256, True,
        requested_count, requested_count_complete,
        sum(row.status is CoverageFileStatus.INDEXED for row in files),
        missing_count, stale_count, error_count, unsupported_count, limit_count,
        exact_read_attempts, exact_read_successes, exact_read_returned_bytes,
        tuple(sorted(exact_read_status_counts.items())), files, "0" * 64,
    )
    encoded = json.dumps(
        _receipt_digest_fields(partial), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > MAX_RECEIPT_BYTES:
        raise ValueError("coverage_receipt_output_limit_exceeded")
    digest = hashlib.sha256(encoded).hexdigest()
    return SnapshotCoverageReceipt(
        partial.schema, partial.snapshot_sha256, partial.selected_subset_only,
        partial.requested_count, partial.requested_count_complete, partial.indexed_count,
        partial.missing_count, partial.stale_count, partial.error_count,
        partial.unsupported_count, partial.limit_count, partial.exact_read_attempts,
        partial.exact_read_successes, partial.exact_read_returned_bytes,
        partial.exact_read_status_counts, partial.files, digest,
    )


def build_snapshot_coverage_receipt(
    root: str | os.PathLike[str] | SourceRootBinding,
    snapshot: SourceSnapshot,
    paths: Iterable[str | os.PathLike[str]],
) -> SnapshotCoverageReceipt:
    """Report parser coverage for caller-selected paths in one source snapshot.

    The returned counts cover only ``paths``. A non-Python extension is marked
    unsupported because the existing parser uses a lexical fallback for it;
    that fallback's observed declaration count remains available in the row.
    An oversized or non-finite path set is bounded to MAX_FILES + 1 observed
    values and performs no exact reads.
    """
    if isinstance(paths, (str, bytes)):
        selected: list[object] = []
        selection_valid = False
    else:
        selected = []
        selection_valid = True
        try:
            iterator = iter(paths)
            for _ in range(MAX_FILES + 1):
                try:
                    selected.append(next(iterator))
                except StopIteration:
                    break
        except Exception:
            selection_valid = False

    count_complete = selection_valid and len(selected) <= MAX_FILES
    snapshot_sha256 = snapshot.snapshot_sha256 if _validate_snapshot(snapshot) else None
    status_counts: dict[str, int] = {}
    files: list[SelectedFileCoverage] = []
    missing_count = stale_count = error_count = unsupported_count = limit_count = 0
    attempts = successes = returned_bytes = 0

    if not selection_valid:
        selected_count = len(selected)
        error_count = max(1, selected_count)
        files.extend(
            SelectedFileCoverage(
                _display_path(path), None, None, None, None, None, None,
                CoverageFileStatus.ERROR,
            )
            for path in selected
        )
    elif not selected:
        error_count = 1
        selected_count = 0
    elif len(selected) > MAX_FILES:
        selected_count = len(selected)
        limit_count = selected_count
        for path in selected:
            files.append(SelectedFileCoverage(
                _display_path(path), None, None, None, None, None, None,
                CoverageFileStatus.LIMIT_EXCEEDED,
            ))
    else:
        selected_count = len(selected)
        aggregate_bytes = 0
        exhausted_aggregate = False
        for path in selected:
            requested_path = _display_path(path)
            if exhausted_aggregate:
                limit_count += 1
                files.append(SelectedFileCoverage(
                    requested_path, None, None, None, None, None, None,
                    CoverageFileStatus.LIMIT_EXCEEDED,
                ))
                continue
            attempts += 1
            retrieved = retrieve_exact(root, snapshot, path)
            status_counts[retrieved.status.value] = status_counts.get(retrieved.status.value, 0) + 1
            if type(retrieved.data) is bytes:
                returned_bytes += len(retrieved.data)
                if retrieved.status is RetrievalStatus.OK:
                    successes += 1
            source_path = retrieved.path
            if retrieved.status is RetrievalStatus.MISSING:
                missing_count += 1
                files.append(SelectedFileCoverage(requested_path, source_path, None, None, None, None, None, CoverageFileStatus.MISSING))
                continue
            if retrieved.status is RetrievalStatus.CHANGED:
                stale_count += 1
                files.append(SelectedFileCoverage(requested_path, source_path, None, None, None, None, None, CoverageFileStatus.STALE))
                continue
            if retrieved.status is not RetrievalStatus.OK or type(retrieved.data) is not bytes or source_path is None:
                error_count += 1
                files.append(SelectedFileCoverage(requested_path, source_path, None, None, None, None, None, CoverageFileStatus.ERROR))
                continue
            data = retrieved.data
            source_hash = hashlib.sha256(data).hexdigest()
            if len(data) > MAX_FILE_BYTES:
                limit_count += 1
                files.append(SelectedFileCoverage(requested_path, source_path, source_hash, None, None, None, None, CoverageFileStatus.LIMIT_EXCEEDED))
                continue
            if aggregate_bytes + len(data) > MAX_AGGREGATE_BYTES:
                limit_count += 1
                exhausted_aggregate = True
                files.append(SelectedFileCoverage(requested_path, source_path, source_hash, None, None, None, None, CoverageFileStatus.LIMIT_EXCEEDED))
                continue
            aggregate_bytes += len(data)
            try:
                text = data.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                error_count += 1
                files.append(SelectedFileCoverage(requested_path, source_path, source_hash, None, None, None, None, CoverageFileStatus.NON_TEXT))
                continue
            try:
                parsed = parse_source_ast(source_path, text)
                parser = parsed.get("parser")
                language = parsed.get("language")
                symbols = parsed.get("symbols")
                syntax_error = parsed.get("syntax_error")
                if (
                    type(parser) is not str or type(language) is not str
                    or type(symbols) is not list
                    or (syntax_error is not None and type(syntax_error) is not str)
                ):
                    raise ValueError("parser_result_invalid")
            except (TypeError, ValueError, RecursionError, OverflowError):
                error_count += 1
                files.append(SelectedFileCoverage(requested_path, source_path, source_hash, None, None, None, None, CoverageFileStatus.ERROR))
                continue
            symbol_count = len(symbols)
            if symbol_count > MAX_SYMBOLS:
                limit_count += 1
                file_status = CoverageFileStatus.LIMIT_EXCEEDED
            elif syntax_error:
                file_status = CoverageFileStatus.SYNTAX_ERROR
            elif parser != "python_ast":
                unsupported_count += 1
                file_status = CoverageFileStatus.UNSUPPORTED
            else:
                file_status = CoverageFileStatus.INDEXED
            files.append(SelectedFileCoverage(
                requested_path, source_path, source_hash, parser, language,
                symbol_count, syntax_error[:MAX_SYNTAX_ERROR_CHARS] if syntax_error else None,
                file_status,
            ))

    return _make_receipt(
        snapshot_sha256=snapshot_sha256, requested_count=selected_count,
        requested_count_complete=count_complete, files=tuple(files),
        missing_count=missing_count, stale_count=stale_count, error_count=error_count,
        unsupported_count=unsupported_count, limit_count=limit_count,
        exact_read_attempts=attempts, exact_read_successes=successes,
        exact_read_returned_bytes=returned_bytes,
        exact_read_status_counts=status_counts,
    )


def _inventory_payload(receipt: SnapshotInventoryReceipt) -> dict[str, object]:
    value = asdict(receipt)
    value.pop("receipt_sha256")
    value["pages"] = [
        {
            **asdict(page),
            "status_counts": [list(row) for row in page.status_counts],
        }
        for page in receipt.pages
    ]
    value["status_counts"] = [list(row) for row in receipt.status_counts]
    value["exact_read_status_counts"] = [list(row) for row in receipt.exact_read_status_counts]
    return value


def _canonical_digest(value: object, limit: int) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > limit:
        raise ValueError("coverage_inventory_output_limit_exceeded")
    return hashlib.sha256(encoded).hexdigest()


def build_snapshot_inventory_receipt(
    snapshot: SourceSnapshot,
    root_binding: SourceRootBinding,
) -> SnapshotInventoryReceipt:
    """Account for every entry in one validated snapshot using fixed pages.

    The snapshot's canonical source tuple is the supplied manifest. This does
    not discover or prove completeness against an external filesystem tree.
    The receipt describes only those manifest entries and their bound root.
    """
    if not _validate_snapshot(snapshot):
        raise ValueError("inventory_snapshot_invalid")
    if type(root_binding) is not SourceRootBinding:
        raise ValueError("inventory_root_binding_required")
    try:
        current_binding = bind_source_root(root_binding.configured_root)
    except (OSError, TypeError, ValueError) as exc:
        raise ValueError("inventory_root_binding_unavailable") from exc
    if (
        current_binding.root_location_sha256 != snapshot.root_location_sha256
        or current_binding.root_identity != snapshot.root_identity
        or root_binding.root_location_sha256 != snapshot.root_location_sha256
        or root_binding.root_identity != snapshot.root_identity
    ):
        raise ValueError("inventory_root_binding_mismatch")
    sources = snapshot.sources
    if not sources or len(sources) > MAX_SNAPSHOT_FILES:
        raise ValueError("inventory_manifest_size_invalid")
    paths = tuple(source.path for source in sources)
    if paths != tuple(sorted(paths)) or len(set(paths)) != len(paths):
        raise ValueError("inventory_manifest_not_canonical")

    all_statuses = tuple(sorted(status.value for status in CoverageFileStatus))
    totals = {name: 0 for name in all_statuses}
    pages: list[SnapshotInventoryPage] = []
    attempts = successes = returned_bytes = 0
    read_statuses: dict[str, int] = {}
    chain = "0" * 64
    complete = True
    for page_index, offset in enumerate(range(0, len(sources), INVENTORY_PAGE_SIZE)):
        page_sources = sources[offset:offset + INVENTORY_PAGE_SIZE]
        page_paths = tuple(source.path for source in page_sources)
        coverage = build_snapshot_coverage_receipt(root_binding, snapshot, page_paths)
        if (
            coverage.snapshot_sha256 != snapshot.snapshot_sha256
            or coverage.requested_count_complete is not True
            or coverage.requested_count != len(page_sources)
            or len(coverage.files) != len(page_sources)
            or tuple(row.requested_path for row in coverage.files) != page_paths
        ):
            raise ValueError("inventory_page_manifest_mismatch")
        page_counts = {name: 0 for name in all_statuses}
        for row in coverage.files:
            page_counts[row.status.value] += 1
            totals[row.status.value] += 1
            if row.status is not CoverageFileStatus.INDEXED:
                complete = False
        attempts += coverage.exact_read_attempts
        successes += coverage.exact_read_successes
        returned_bytes += coverage.exact_read_returned_bytes
        for name, count in coverage.exact_read_status_counts:
            read_statuses[name] = read_statuses.get(name, 0) + count
        page_payload = {
            "schema": "wrench.snapshot-inventory-page.v1",
            "snapshot_sha256": snapshot.snapshot_sha256,
            "root_location_sha256": snapshot.root_location_sha256,
            "root_identity": snapshot.root_identity,
            "page_index": page_index,
            "first_path": page_paths[0],
            "last_path": page_paths[-1],
            "entry_count": len(page_sources),
            "coverage_sha256": coverage.receipt_sha256,
            "status_counts": [[name, page_counts[name]] for name in all_statuses],
        }
        page_digest = _canonical_digest(page_payload, MAX_INVENTORY_RECEIPT_BYTES)
        chain = hashlib.sha256(
            json.dumps(
                {"previous": chain, "page_sha256": page_digest},
                sort_keys=True, separators=(",", ":"),
            ).encode("ascii")
        ).hexdigest()
        pages.append(SnapshotInventoryPage(
            page_index, len(page_sources), page_paths[0], page_paths[-1],
            coverage.receipt_sha256, page_digest,
            tuple((name, page_counts[name]) for name in all_statuses),
        ))

    try:
        final_binding = bind_source_root(root_binding.configured_root)
    except (OSError, TypeError, ValueError) as exc:
        raise ValueError("inventory_root_changed_during_read") from exc
    if (
        final_binding.root_location_sha256 != snapshot.root_location_sha256
        or final_binding.root_identity != snapshot.root_identity
    ):
        raise ValueError("inventory_root_changed_during_read")

    partial = SnapshotInventoryReceipt(
        "wrench.snapshot-inventory.v1", snapshot.snapshot_sha256,
        snapshot.root_location_sha256 or "", snapshot.root_identity or "", True,
        complete, len(sources), INVENTORY_PAGE_SIZE, tuple(pages), chain,
        tuple((name, totals[name]) for name in all_statuses), attempts, successes,
        returned_bytes, tuple(sorted(read_statuses.items())), "0" * 64,
    )
    digest = _canonical_digest(_inventory_payload(partial), MAX_INVENTORY_RECEIPT_BYTES)
    return SnapshotInventoryReceipt(
        partial.schema, partial.snapshot_sha256, partial.root_location_sha256,
        partial.root_identity, partial.supplied_manifest_only, partial.complete,
        partial.entry_count, partial.page_size, partial.pages,
        partial.page_hash_chain_sha256, partial.status_counts,
        partial.exact_read_attempts, partial.exact_read_successes,
        partial.exact_read_returned_bytes, partial.exact_read_status_counts, digest,
    )


__all__ = [
    "CoverageFileStatus",
    "MAX_RECEIPT_BYTES",
    "INVENTORY_PAGE_SIZE",
    "MAX_INVENTORY_RECEIPT_BYTES",
    "SelectedFileCoverage",
    "SnapshotInventoryPage",
    "SnapshotInventoryReceipt",
    "SnapshotCoverageReceipt",
    "build_snapshot_inventory_receipt",
    "build_snapshot_coverage_receipt",
]
