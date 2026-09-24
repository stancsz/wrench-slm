"""Bounded discovery metadata with deferred immutable operation schemas.

Visibility from this registry is descriptive only. It confers no permission
and provides no operation execution, routing, shell, provider, or model API.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any


MAX_NAMESPACES = 64
MAX_OPERATIONS_PER_NAMESPACE = 128
MAX_TOTAL_OPERATIONS = 512
MAX_IDENTIFIER_CHARS = 128
MAX_SUMMARY_BYTES = 512
MAX_SCHEMA_BYTES = 32 * 1024
MAX_TOTAL_SCHEMA_BYTES = 256 * 1024
MAX_SCHEMA_DEPTH = 64
MAX_SCHEMA_NODES = 10_000


class NamespaceRegistryError(ValueError):
    """Invalid or over-limit caller-supplied registry data."""


class SchemaLookupStatus(str, Enum):
    OK = "ok"
    UNKNOWN_NAMESPACE = "unknown_namespace"
    UNKNOWN_OPERATION = "unknown_operation"


@dataclass(frozen=True)
class OperationDescriptor:
    operation_id: str
    summary: str
    schema: Mapping[str, Any]


@dataclass(frozen=True)
class NamespaceDescriptor:
    namespace_id: str
    summary: str
    operations: tuple[OperationDescriptor, ...]


@dataclass(frozen=True)
class OperationSummary:
    operation_id: str
    summary: str


@dataclass(frozen=True)
class NamespaceSummary:
    namespace_id: str
    summary: str
    operations: tuple[OperationSummary, ...]


@dataclass(frozen=True)
class SchemaLookup:
    status: SchemaLookupStatus
    namespace_id: str
    operation_id: str
    schema: Mapping[str, Any] | None = None
    sha256: str | None = None


def _validate_label(value: object, label: str, limit: int) -> str:
    if not isinstance(value, str) or not value or len(value) > limit:
        raise NamespaceRegistryError(f"invalid_{label}")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise NamespaceRegistryError(f"invalid_{label}_encoding") from exc
    if label == "summary" and len(encoded) > MAX_SUMMARY_BYTES:
        raise NamespaceRegistryError("summary_byte_limit_exceeded")
    if label == "identifier" and any(ord(char) < 0x20 for char in value):
        raise NamespaceRegistryError("invalid_identifier")
    return value


def _copy_json(value: object) -> object:
    """Validate JSON-shaped input, copying it within depth/node bounds."""
    nodes = 0
    string_bytes = 0
    active: set[int] = set()

    def visit(item: object, depth: int) -> object:
        nonlocal nodes, string_bytes
        nodes += 1
        if nodes > MAX_SCHEMA_NODES:
            raise NamespaceRegistryError("schema_node_limit_exceeded")
        if depth > MAX_SCHEMA_DEPTH:
            raise NamespaceRegistryError("schema_depth_limit_exceeded")
        if item is None or type(item) in (bool, int):
            return item
        if type(item) is float:
            if not math.isfinite(item):
                raise NamespaceRegistryError("schema_nonfinite_number")
            return item
        if type(item) is str:
            # UTF-8 byte length cannot be smaller than character count, so
            # reject large strings before allocating an encoded copy.
            if len(item) > MAX_SCHEMA_BYTES:
                raise NamespaceRegistryError("schema_byte_limit_exceeded")
            try:
                encoded_size = len(item.encode("utf-8"))
                string_bytes += encoded_size
                if string_bytes > MAX_SCHEMA_BYTES:
                    raise NamespaceRegistryError("schema_byte_limit_exceeded")
            except UnicodeEncodeError as exc:
                raise NamespaceRegistryError("schema_invalid_string_encoding") from exc
            return item
        if type(item) in (dict, list, tuple):
            identity = id(item)
            if identity in active:
                raise NamespaceRegistryError("schema_cycle_forbidden")
            # Built-in containers have bounded, constant-time length checks.
            # A dict needs at least one node per key and one per value, so
            # reject oversized objects before traversing any of their entries.
            remaining_nodes = MAX_SCHEMA_NODES - nodes
            minimum_nodes = 2 * len(item) if type(item) is dict else len(item)
            if minimum_nodes > remaining_nodes:
                raise NamespaceRegistryError("schema_node_limit_exceeded")
            active.add(identity)
            try:
                if type(item) is dict:
                    copied: dict[str, object] = {}
                    for key, nested in item.items():
                        if type(key) is not str:
                            raise NamespaceRegistryError("schema_keys_must_be_strings")
                        visit(key, depth + 1)
                        copied[key] = visit(nested, depth + 1)
                    return copied
                return [visit(nested, depth + 1) for nested in item]
            finally:
                active.remove(identity)
        raise NamespaceRegistryError("schema_contains_non_json_value")

    return visit(value, 0)


def _canonical_bytes(schema: Mapping[str, Any]) -> bytes:
    try:
        encoder = json.JSONEncoder(
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        chunks: list[str] = []
        total = 0
        for chunk in encoder.iterencode(schema):
            encoded_len = len(chunk.encode("utf-8"))
            total += encoded_len
            if total > MAX_SCHEMA_BYTES:
                raise NamespaceRegistryError("schema_byte_limit_exceeded")
            chunks.append(chunk)
        return "".join(chunks).encode("utf-8")
    except NamespaceRegistryError:
        raise
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise NamespaceRegistryError("invalid_operation_schema") from exc


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(nested) for key, nested in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(nested) for nested in value)
    return value


class NamespaceRegistry:
    """Finite immutable namespace metadata and deferred operation schemas."""

    def __init__(self, namespaces: Iterable[NamespaceDescriptor]):
        if isinstance(namespaces, (str, bytes)):
            raise NamespaceRegistryError("namespaces_must_be_iterable")
        try:
            descriptors = []
            iterator = iter(namespaces)
            for _ in range(MAX_NAMESPACES + 1):
                try:
                    descriptors.append(next(iterator))
                except StopIteration:
                    break
        except (TypeError, RuntimeError) as exc:
            raise NamespaceRegistryError("invalid_namespace_iterable") from exc
        if len(descriptors) > MAX_NAMESPACES:
            raise NamespaceRegistryError("namespace_count_limit_exceeded")

        registry: dict[str, tuple[str, dict[str, tuple[str, Mapping[str, Any], str]]]] = {}
        total_ops = 0
        total_schema_bytes = 0
        for descriptor in descriptors:
            if not isinstance(descriptor, NamespaceDescriptor):
                raise NamespaceRegistryError("invalid_namespace_descriptor")
            namespace_id = _validate_label(descriptor.namespace_id, "identifier", MAX_IDENTIFIER_CHARS)
            summary = _validate_label(descriptor.summary, "summary", MAX_SUMMARY_BYTES)
            if namespace_id in registry:
                raise NamespaceRegistryError("duplicate_namespace_id")
            if not isinstance(descriptor.operations, tuple):
                raise NamespaceRegistryError("operations_must_be_finite_tuple")
            if len(descriptor.operations) > MAX_OPERATIONS_PER_NAMESPACE:
                raise NamespaceRegistryError("operation_count_limit_exceeded")
            operations: dict[str, tuple[str, Mapping[str, Any], str]] = {}
            for operation in descriptor.operations:
                if not isinstance(operation, OperationDescriptor):
                    raise NamespaceRegistryError("invalid_operation_descriptor")
                operation_id = _validate_label(operation.operation_id, "identifier", MAX_IDENTIFIER_CHARS)
                operation_summary = _validate_label(operation.summary, "summary", MAX_SUMMARY_BYTES)
                if operation_id in operations:
                    raise NamespaceRegistryError("duplicate_operation_id")
                if type(operation.schema) is not dict:
                    raise NamespaceRegistryError("schema_must_be_object")
                copied = _copy_json(operation.schema)
                if not isinstance(copied, dict):
                    raise NamespaceRegistryError("schema_must_be_object")
                canonical = _canonical_bytes(copied)
                total_schema_bytes += len(canonical)
                if total_schema_bytes > MAX_TOTAL_SCHEMA_BYTES:
                    raise NamespaceRegistryError("aggregate_schema_byte_limit_exceeded")
                operations[operation_id] = (
                    operation_summary,
                    _freeze(copied),  # type: ignore[arg-type]
                    hashlib.sha256(canonical).hexdigest(),
                )
                total_ops += 1
                if total_ops > MAX_TOTAL_OPERATIONS:
                    raise NamespaceRegistryError("total_operation_count_limit_exceeded")
            registry[namespace_id] = (summary, operations)

        self._registry = registry

    @property
    def namespace_count(self) -> int:
        return len(self._registry)

    @property
    def operation_count(self) -> int:
        return sum(len(operations) for _, operations in self._registry.values())

    def discover(self, query: str | None = None) -> tuple[NamespaceSummary, ...]:
        """Return sorted namespace and operation IDs/summaries only."""
        if query is not None and (not isinstance(query, str) or len(query) > MAX_SUMMARY_BYTES):
            raise NamespaceRegistryError("invalid_search_query")
        folded = query.casefold() if query else None
        result: list[NamespaceSummary] = []
        for namespace_id in sorted(self._registry):
            summary, operations = self._registry[namespace_id]
            matches_namespace = folded is None or folded in namespace_id.casefold() or folded in summary.casefold()
            visible_ops = tuple(
                OperationSummary(operation_id, operations[operation_id][0])
                for operation_id in sorted(operations)
                if matches_namespace
                or folded is None
                or folded in operation_id.casefold()
                or folded in operations[operation_id][0].casefold()
            )
            if matches_namespace or visible_ops:
                result.append(NamespaceSummary(namespace_id, summary, visible_ops))
        return tuple(result)

    def lookup(self, namespace_id: str, operation_id: str) -> SchemaLookup:
        """Return one immutable schema and canonical JSON digest on demand."""
        if not isinstance(namespace_id, str) or namespace_id not in self._registry:
            return SchemaLookup(
                SchemaLookupStatus.UNKNOWN_NAMESPACE,
                namespace_id if isinstance(namespace_id, str) else "",
                operation_id if isinstance(operation_id, str) else "",
            )
        if not isinstance(operation_id, str):
            return SchemaLookup(SchemaLookupStatus.UNKNOWN_OPERATION, namespace_id, "")
        _, operations = self._registry[namespace_id]
        if operation_id not in operations:
            return SchemaLookup(SchemaLookupStatus.UNKNOWN_OPERATION, namespace_id, operation_id)
        _, schema, digest = operations[operation_id]
        return SchemaLookup(SchemaLookupStatus.OK, namespace_id, operation_id, schema, digest)


__all__ = [
    "MAX_IDENTIFIER_CHARS",
    "MAX_NAMESPACES",
    "MAX_OPERATIONS_PER_NAMESPACE",
    "MAX_SCHEMA_BYTES",
    "MAX_SUMMARY_BYTES",
    "MAX_TOTAL_OPERATIONS",
    "MAX_TOTAL_SCHEMA_BYTES",
    "NamespaceDescriptor",
    "NamespaceRegistry",
    "NamespaceRegistryError",
    "NamespaceSummary",
    "OperationDescriptor",
    "OperationSummary",
    "SchemaLookup",
    "SchemaLookupStatus",
]
