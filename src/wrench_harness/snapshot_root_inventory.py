"""Bounded, policy-scoped root inventory for caller-owned snapshots.

A complete receipt means every reachable entry inside each declared scope was
observed under this policy. Exclusions are counted. It is not an atomic tree
snapshot and says nothing about paths outside the declared scopes.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

from .snapshot import (
    MAX_SNAPSHOT_BYTES,
    MAX_SNAPSHOT_FILES,
    MAX_SOURCE_BYTES,
    MAX_SOURCE_PATH_CHARS,
    SnapshotAdmissionError,
    SourceRootBinding,
    SourceSnapshot,
    _has_reparse_attribute,
    _normalize_relative_path,
    _prepare_root_path,
    _read_stable_source,
    _root_location_sha256,
    bind_source_root,
    create_snapshot,
)

SCHEMA = "wrench.source-root-inventory.v1"
MAX_INVENTORY_ENTRIES = 512
MAX_INVENTORY_DEPTH = 32
MAX_POLICY_ITEMS = 64
MAX_POLICY_BYTES = 16 * 1024
MAX_OUTPUT_BYTES = 512 * 1024
MAX_ERROR_ROWS = 256
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ROOT_IDENTITY_RE = re.compile(
    r"^(?:posix:(?:0|[1-9][0-9]*):(?:0|[1-9][0-9]*)|win:[0-9a-f]{16}:[0-9a-f]{32})$"
)
_TRUNCATION_REASONS = {
    "depth_limit", "entry_limit", "error_rows", "output_limit",
    "snapshot_byte_limit", "snapshot_file_limit",
}


@dataclass(frozen=True)
class RootInventoryPolicy:
    """Explicit directory scopes and path-prefix exclusions relative to root."""

    scopes: tuple[str, ...]
    exclusions: tuple[str, ...] = ()
    max_entries: int = MAX_INVENTORY_ENTRIES
    max_depth: int = MAX_INVENTORY_DEPTH


@dataclass(frozen=True)
class InventoryRecord:
    path: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class InventoryError:
    path: str
    code: str


@dataclass(frozen=True)
class RootInventoryReceipt:
    schema: str
    normalized_root: str
    root_location_sha256: str
    root_identity: str
    policy: RootInventoryPolicy
    records: tuple[InventoryRecord, ...]
    entries_seen: int
    excluded_entries: int
    errors: tuple[InventoryError, ...]
    truncated_by: tuple[str, ...]
    complete: bool
    manifest_sha256: str
    receipt_sha256: str
    output_bytes: int


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")


def _policy_payload(policy: RootInventoryPolicy) -> dict[str, object]:
    return {
        "scopes": list(policy.scopes),
        "exclusions": list(policy.exclusions),
        "max_entries": policy.max_entries,
        "max_depth": policy.max_depth,
    }


def _record_payload(record: InventoryRecord) -> dict[str, object]:
    return {"path": record.path, "size_bytes": record.size_bytes, "sha256": record.sha256}


def _manifest_payload(
    normalized_root: str,
    root_location_sha256: str,
    root_identity: str,
    policy: RootInventoryPolicy,
    records: tuple[InventoryRecord, ...],
) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "normalized_root": normalized_root,
        "root_location_sha256": root_location_sha256,
        "root_identity": root_identity,
        "policy": _policy_payload(policy),
        "records": [_record_payload(record) for record in records],
    }


def _receipt_payload(
    normalized_root: str,
    root_location_sha256: str,
    root_identity: str,
    policy: RootInventoryPolicy,
    records: tuple[InventoryRecord, ...],
    entries_seen: int,
    excluded_entries: int,
    errors: tuple[InventoryError, ...],
    truncated_by: tuple[str, ...],
    complete: bool,
    manifest_sha256: str,
    output_bytes: int,
) -> dict[str, object]:
    return {
        **_manifest_payload(normalized_root, root_location_sha256, root_identity, policy, records),
        "entries_seen": entries_seen,
        "excluded_entries": excluded_entries,
        "errors": [{"path": row.path, "code": row.code} for row in errors],
        "truncated_by": list(truncated_by),
        "complete": complete,
        "manifest_sha256": manifest_sha256,
        "output_bytes": output_bytes,
    }


def _normalize_policy(policy: RootInventoryPolicy) -> RootInventoryPolicy:
    if type(policy) is not RootInventoryPolicy:
        raise SnapshotAdmissionError("invalid_inventory_policy")
    if (
        not isinstance(policy.scopes, tuple)
        or not 1 <= len(policy.scopes) <= MAX_POLICY_ITEMS
        or not isinstance(policy.exclusions, tuple)
        or len(policy.exclusions) > MAX_POLICY_ITEMS
        or type(policy.max_entries) is not int
        or not 1 <= policy.max_entries <= MAX_INVENTORY_ENTRIES
        or type(policy.max_depth) is not int
        or not 0 <= policy.max_depth <= MAX_INVENTORY_DEPTH
    ):
        raise SnapshotAdmissionError("inventory_policy_limit_exceeded")

    def normalize(value: str, *, allow_root: bool) -> str:
        if type(value) is not str:
            raise SnapshotAdmissionError("invalid_inventory_path")
        if allow_root and value in ("", "."):
            return "."
        return _normalize_relative_path(value)

    scopes = tuple(sorted(normalize(path, allow_root=True) for path in policy.scopes))
    exclusions = tuple(sorted(normalize(path, allow_root=False) for path in policy.exclusions))
    if (
        len({_path_key(path) for path in scopes}) != len(scopes)
        or len({_path_key(path) for path in exclusions}) != len(exclusions)
    ):
        raise SnapshotAdmissionError("duplicate_inventory_policy_path")
    # Overlapping scopes make accounting ambiguous, so require disjoint roots.
    for index, scope in enumerate(scopes):
        for other in scopes[index + 1 :]:
            if _path_within(other, scope) or _path_within(scope, other):
                raise SnapshotAdmissionError("overlapping_inventory_scopes")
    if any(_path_within(scope, exclusion) for scope in scopes for exclusion in exclusions):
        raise SnapshotAdmissionError("inventory_exclusion_covers_scope")
    normalized = RootInventoryPolicy(scopes, exclusions, policy.max_entries, policy.max_depth)
    if len(_canonical(_policy_payload(normalized))) > MAX_POLICY_BYTES:
        raise SnapshotAdmissionError("inventory_policy_metadata_limit_exceeded")
    return normalized


def _path_key(path: str) -> str:
    return path.casefold() if os.name == "nt" else path


def _path_within(path: str, directory: str, *, allow_equal: bool = True) -> bool:
    path_key = _path_key(path)
    directory_key = _path_key(directory)
    if directory == ".":
        return allow_equal or path != "."
    return (allow_equal and path_key == directory_key) or path_key.startswith(directory_key + "/")


def _is_excluded(path: str, exclusions: tuple[str, ...]) -> bool:
    return any(_path_within(path, excluded) for excluded in exclusions)


def _safe_directory(root: Path, relative: str) -> tuple[Path, os.stat_result]:
    current = root
    info = root.lstat()
    if stat.S_ISLNK(info.st_mode) or _has_reparse_attribute(info) or not stat.S_ISDIR(info.st_mode):
        raise SnapshotAdmissionError("root_must_be_real_directory")
    if relative != ".":
        for component in relative.split("/"):
            current = current / component
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode) or _has_reparse_attribute(info):
                raise SnapshotAdmissionError("reparse_point_forbidden")
            if not stat.S_ISDIR(info.st_mode):
                raise SnapshotAdmissionError("scope_not_directory")
    return current, info


def inventory_source_root(
    root: str | os.PathLike[str] | SourceRootBinding,
    policy: RootInventoryPolicy,
) -> RootInventoryReceipt:
    """Enumerate bounded entries under explicit disjoint scopes.

    Directory enumeration is path-based and can race with external writers.
    Every file is subsequently read through the snapshot module's stable,
    root-bound reader. Any observed traversal/read error or resource cap makes
    the receipt incomplete.
    """
    normalized_policy = _normalize_policy(policy)
    binding = root if type(root) is SourceRootBinding else bind_source_root(root)
    # create_snapshot performs its own strict binding validation; enforce it
    # up front here without resolving the caller's configured lexical path.
    if type(binding) is not SourceRootBinding:
        raise SnapshotAdmissionError("invalid_root_binding")
    root_path = _prepare_root_path(binding.configured_root)
    location_digest = _root_location_sha256(binding.configured_root)
    normalized_root = str(root_path)
    records: list[InventoryRecord] = []
    errors: list[InventoryError] = []
    truncated: set[str] = set()
    entries_seen = 0
    excluded = 0
    total_bytes = 0
    stop = False

    def error(path: str, code: str) -> None:
        if len(errors) < MAX_ERROR_ROWS:
            errors.append(InventoryError(path, code))
        else:
            truncated.add("error_rows")

    def walk(directory: str, depth: int) -> None:
        nonlocal entries_seen, excluded, total_bytes, stop
        if stop:
            return
        if depth > normalized_policy.max_depth:
            truncated.add("depth_limit")
            error(directory, "depth_limit")
            return
        try:
            directory_path, before = _safe_directory(root_path, directory)
            with os.scandir(directory_path) as iterator:
                rows: list[os.DirEntry[str]] = []
                capacity = normalized_policy.max_entries - entries_seen
                directory_overflow = False
                for entry in iterator:
                    rows.append(entry)
                    if len(rows) > capacity:
                        rows.pop()
                        truncated.add("entry_limit")
                        directory_overflow = True
                        break
                rows.sort(key=lambda item: item.name)
            try:
                after = directory_path.lstat()
                if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino) or stat.S_ISLNK(after.st_mode) or _has_reparse_attribute(after):
                    error(directory, "directory_changed_during_walk")
                    return
            except OSError:
                error(directory, "directory_metadata_failed")
                return
        except FileNotFoundError:
            error(directory, "directory_missing")
            return
        except OSError:
            error(directory, "directory_read_failed")
            return
        for entry in rows:
            if stop:
                break
            if entries_seen >= normalized_policy.max_entries:
                truncated.add("entry_limit")
                stop = True
                break
            relative = entry.name if directory == "." else f"{directory}/{entry.name}"
            try:
                relative = _normalize_relative_path(relative)
                entries_seen += 1
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode) or _has_reparse_attribute(info):
                    error(relative, "reparse_point_forbidden")
                    continue
                if _is_excluded(relative, normalized_policy.exclusions):
                    excluded += 1
                    # Excluded directories are opaque by caller policy; count
                    # only the encountered directory itself.
                    continue
                mode = info.st_mode
                if stat.S_ISDIR(mode):
                    walk(relative, depth + 1)
                elif stat.S_ISREG(mode):
                    if len(records) >= MAX_SNAPSHOT_FILES:
                        truncated.add("snapshot_file_limit")
                        stop = True
                        break
                    if info.st_size < 0 or info.st_size > MAX_SOURCE_BYTES:
                        error(relative, "source_size_limit")
                        continue
                    if total_bytes + info.st_size > MAX_SNAPSHOT_BYTES:
                        truncated.add("snapshot_byte_limit")
                        stop = True
                        break
                    try:
                        data, observed, observed_root = _read_stable_source(
                            root_path, relative, binding.root_identity
                        )
                    except (OSError, SnapshotAdmissionError):
                        error(relative, "source_read_or_identity_failed")
                        continue
                    if observed_root != binding.root_identity or len(data) != observed.st_size:
                        error(relative, "source_changed_during_inventory")
                        continue
                    if total_bytes + len(data) > MAX_SNAPSHOT_BYTES:
                        truncated.add("snapshot_byte_limit")
                        stop = True
                        break
                    total_bytes += len(data)
                    records.append(InventoryRecord(relative, len(data), hashlib.sha256(data).hexdigest()))
                else:
                    error(relative, "non_regular_entry")
            except (OSError, SnapshotAdmissionError, ValueError):
                error(relative, "entry_metadata_or_path_failed")
        if directory_overflow and not stop:
            stop = True

    for scope in normalized_policy.scopes:
        if stop:
            break
        walk(scope, 0)

    # Detect a replaced root after the walk. This does not make enumeration a
    # filesystem transaction; it catches ordinary root replacement races.
    try:
        current = bind_source_root(binding.configured_root)
        if current.root_identity != binding.root_identity or current.root_location_sha256 != binding.root_location_sha256:
            error(".", "root_changed_during_inventory")
    except (OSError, SnapshotAdmissionError):
        error(".", "root_revalidation_failed")

    records_tuple = tuple(sorted(records, key=lambda row: row.path))
    errors_tuple = tuple(sorted(errors, key=lambda row: (row.path, row.code)))
    truncated_tuple = tuple(sorted(truncated))
    complete = not errors_tuple and not truncated_tuple
    manifest_data = _canonical(
        _manifest_payload(normalized_root, location_digest, binding.root_identity, normalized_policy, records_tuple)
    )
    manifest_digest = hashlib.sha256(manifest_data).hexdigest()
    receipt_data = _canonical(
        _receipt_payload(
            normalized_root,
            location_digest,
            binding.root_identity,
            normalized_policy,
            records_tuple,
            entries_seen,
            excluded,
            errors_tuple,
            truncated_tuple,
            complete,
            manifest_digest,
            0,
        )
    )
    if len(receipt_data) > MAX_OUTPUT_BYTES:
        truncated_tuple = tuple(sorted(set(truncated_tuple) | {"output_limit"}))
        complete = False
        receipt_data = _canonical(
            _receipt_payload(
                normalized_root, location_digest, binding.root_identity, normalized_policy,
                records_tuple, entries_seen, excluded, errors_tuple, truncated_tuple,
                complete, manifest_digest, 0,
            )
        )
        if len(receipt_data) > MAX_OUTPUT_BYTES:
            raise SnapshotAdmissionError("inventory_output_limit_exceeded")
    output_bytes = len(receipt_data)
    receipt_digest = hashlib.sha256(receipt_data).hexdigest()
    return RootInventoryReceipt(
        SCHEMA, normalized_root, location_digest, binding.root_identity, normalized_policy,
        records_tuple, entries_seen, excluded, errors_tuple, truncated_tuple,
        complete, manifest_digest, receipt_digest, output_bytes,
    )


def validate_root_inventory_receipt(receipt: object) -> bool:
    """Check canonical receipt and manifest digests plus declared hard limits."""
    if type(receipt) is not RootInventoryReceipt or receipt.schema != SCHEMA:
        return False
    if (
        type(receipt.normalized_root) is not str
        or not receipt.normalized_root
        or not Path(receipt.normalized_root).is_absolute()
        or type(receipt.root_location_sha256) is not str
        or _SHA256_RE.fullmatch(receipt.root_location_sha256) is None
        or type(receipt.root_identity) is not str
        or _ROOT_IDENTITY_RE.fullmatch(receipt.root_identity) is None
        or not isinstance(receipt.records, tuple)
        or len(receipt.records) > MAX_SNAPSHOT_FILES
        or type(receipt.entries_seen) is not int
        or not 0 <= receipt.entries_seen <= MAX_INVENTORY_ENTRIES
        or type(receipt.excluded_entries) is not int
        or not 0 <= receipt.excluded_entries <= receipt.entries_seen
        or len(receipt.records) + receipt.excluded_entries > receipt.entries_seen
        or not isinstance(receipt.errors, tuple)
        or len(receipt.errors) > MAX_ERROR_ROWS
        or not isinstance(receipt.truncated_by, tuple)
        or any(type(reason) is not str for reason in receipt.truncated_by)
        or receipt.truncated_by != tuple(sorted(set(receipt.truncated_by)))
        or any(reason not in _TRUNCATION_REASONS for reason in receipt.truncated_by)
        or type(receipt.complete) is not bool
        or type(receipt.output_bytes) is not int
        or not 0 <= receipt.output_bytes <= MAX_OUTPUT_BYTES
    ):
        return False
    try:
        policy = _normalize_policy(receipt.policy)
        if policy != receipt.policy:
            return False
        records = receipt.records
        if records != tuple(sorted(records, key=lambda row: row.path)):
            return False
        seen: set[str] = set()
        total = 0
        for row in records:
            if type(row) is not InventoryRecord or _normalize_relative_path(row.path) != row.path:
                return False
            scope_memberships = sum(
                _path_within(row.path, scope, allow_equal=False) for scope in policy.scopes
            )
            if scope_memberships != 1 or _is_excluded(row.path, policy.exclusions):
                return False
            path_key = row.path.casefold() if os.name == "nt" else row.path
            if path_key in seen or type(row.size_bytes) is not int or not 0 <= row.size_bytes <= MAX_SOURCE_BYTES:
                return False
            if type(row.sha256) is not str or _SHA256_RE.fullmatch(row.sha256) is None:
                return False
            seen.add(path_key)
            total += row.size_bytes
        if total > MAX_SNAPSHOT_BYTES:
            return False
        errors = receipt.errors
        if any(
            type(row) is not InventoryError
            or type(row.path) is not str
            or len(row.path) > MAX_SOURCE_PATH_CHARS
            or (row.path != "." and _normalize_relative_path(row.path) != row.path)
            or type(row.code) is not str
            or not 1 <= len(row.code) <= 64
            for row in errors
        ):
            return False
        if errors != tuple(sorted(errors, key=lambda row: (row.path, row.code))):
            return False
        if receipt.complete != (not errors and not receipt.truncated_by):
            return False
        manifest_data = _canonical(
            _manifest_payload(receipt.normalized_root, receipt.root_location_sha256,
                              receipt.root_identity, policy, records)
        )
        manifest_digest = hashlib.sha256(manifest_data).hexdigest()
        if manifest_digest != receipt.manifest_sha256:
            return False
        payload = _canonical(
            _receipt_payload(
                receipt.normalized_root, receipt.root_location_sha256, receipt.root_identity,
                policy, records, receipt.entries_seen, receipt.excluded_entries, errors,
                receipt.truncated_by, receipt.complete, receipt.manifest_sha256, 0,
            )
        )
        if len(payload) != receipt.output_bytes or len(payload) > MAX_OUTPUT_BYTES:
            return False
        # output_bytes is intentionally fixed-point metadata and included as 0
        # in the canonical bytes for a stable receipt hash.
        return hashlib.sha256(payload).hexdigest() == receipt.receipt_sha256
    except Exception:
        return False


def create_snapshot_from_inventory(
    root: str | os.PathLike[str] | SourceRootBinding,
    receipt: RootInventoryReceipt,
) -> SourceSnapshot:
    """Re-enumerate the policy scope, then admit its matching snapshot.

    The fresh inventory closes omission-by-manifest gaps at admission. The
    directory walk and subsequent snapshot read are not one atomic filesystem
    transaction; concurrent writers can still race the interval.
    """
    if not validate_root_inventory_receipt(receipt) or not receipt.complete:
        raise SnapshotAdmissionError("incomplete_or_invalid_root_inventory")
    binding = root if type(root) is SourceRootBinding else bind_source_root(root)
    if (
        str(_prepare_root_path(binding.configured_root)) != receipt.normalized_root
        or binding.root_location_sha256 != receipt.root_location_sha256
        or binding.root_identity != receipt.root_identity
    ):
        raise SnapshotAdmissionError("root_inventory_binding_mismatch")
    fresh_receipt = inventory_source_root(binding, receipt.policy)
    if not fresh_receipt.complete or fresh_receipt != receipt:
        raise SnapshotAdmissionError("root_inventory_changed_since_receipt")
    snapshot = create_snapshot(binding, (row.path for row in receipt.records))
    if tuple(
        InventoryRecord(row.path, row.size_bytes, row.sha256) for row in snapshot.sources
    ) != receipt.records:
        raise SnapshotAdmissionError("root_inventory_manifest_changed")
    return snapshot


__all__ = [
    "InventoryError",
    "InventoryRecord",
    "MAX_INVENTORY_DEPTH",
    "MAX_INVENTORY_ENTRIES",
    "MAX_OUTPUT_BYTES",
    "RootInventoryPolicy",
    "RootInventoryReceipt",
    "create_snapshot_from_inventory",
    "inventory_source_root",
    "validate_root_inventory_receipt",
]
