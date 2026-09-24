from __future__ import annotations

import hashlib
import json

import pytest

import wrench_harness.namespace_registry as registry_module
from wrench_harness.namespace_registry import (
    NamespaceDescriptor,
    NamespaceRegistry,
    NamespaceRegistryError,
    OperationDescriptor,
    SchemaLookupStatus,
)


def _operation(operation_id, summary, schema=None):
    return OperationDescriptor(
        operation_id,
        summary,
        schema if schema is not None else {"type": "object"},
    )


def _namespace(namespace_id, summary, *operations):
    return NamespaceDescriptor(namespace_id, summary, tuple(operations))


def test_discovery_is_sorted_bounded_metadata_and_search_is_deterministic():
    registry = NamespaceRegistry(
        [
            _namespace("zeta", "Zeta operations", _operation("write", "Write data")),
            _namespace(
                "alpha", "Alpha operations",
                _operation("z-op", "Zed"), _operation("a-op", "Alpha lookup"),
            ),
        ]
    )

    summaries = registry.discover()
    assert [item.namespace_id for item in summaries] == ["alpha", "zeta"]
    assert [item.operation_id for item in summaries[0].operations] == ["a-op", "z-op"]
    assert [item.namespace_id for item in registry.discover("lookup")] == ["alpha"]
    assert [item.operation_id for item in registry.discover("lookup")[0].operations] == ["a-op"]
    assert registry.namespace_count == 2
    assert registry.operation_count == 3
    assert not hasattr(registry, "execute")


def test_schema_lookup_is_deferred_and_returns_canonical_digest():
    registry = NamespaceRegistry(
        [_namespace("files", "File operations", _operation("read", "Read a file", {"type": "object", "properties": {"path": {"type": "string"}}}))]
    )

    discovery = registry.discover()[0]
    assert "schema" not in discovery.__dict__
    result = registry.lookup("files", "read")
    canonical = json.dumps(
        {"type": "object", "properties": {"path": {"type": "string"}}},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    assert result.status is SchemaLookupStatus.OK
    assert result.schema["type"] == "object"
    assert result.sha256 == hashlib.sha256(canonical).hexdigest()
    assert not hasattr(result, "execute")


def test_unknown_namespace_and_operation_are_explicit():
    registry = NamespaceRegistry([_namespace("known", "Known", _operation("op", "Operation"))])

    assert registry.lookup("missing", "op").status is SchemaLookupStatus.UNKNOWN_NAMESPACE
    assert registry.lookup("known", "missing").status is SchemaLookupStatus.UNKNOWN_OPERATION
    assert registry.lookup([], "op").status is SchemaLookupStatus.UNKNOWN_NAMESPACE


def test_input_schema_mutation_is_isolated_and_returned_schema_is_immutable():
    original = {"type": "object", "properties": {"names": {"type": "array", "items": {"type": "string"}}}}
    registry = NamespaceRegistry([_namespace("ns", "Namespace", _operation("op", "Operation", original))])
    original["properties"]["names"]["items"]["type"] = "integer"
    original["new"] = True

    schema = registry.lookup("ns", "op").schema
    assert schema["properties"]["names"]["items"]["type"] == "string"
    assert "new" not in schema
    with pytest.raises(TypeError):
        schema["new"] = True
    with pytest.raises(TypeError):
        schema["properties"]["new"] = {}
    with pytest.raises(TypeError):
        schema["properties"]["names"]["type"] = "integer"


def test_namespace_and_operation_count_limits_are_enforced(monkeypatch):
    monkeypatch.setattr(registry_module, "MAX_NAMESPACES", 1)
    with pytest.raises(NamespaceRegistryError, match="namespace_count_limit_exceeded"):
        NamespaceRegistry([_namespace("a", "A"), _namespace("b", "B")])

    monkeypatch.setattr(registry_module, "MAX_NAMESPACES", 4)
    monkeypatch.setattr(registry_module, "MAX_OPERATIONS_PER_NAMESPACE", 1)
    with pytest.raises(NamespaceRegistryError, match="operation_count_limit_exceeded"):
        NamespaceRegistry([_namespace("a", "A", _operation("x", "X"), _operation("y", "Y"))])

    monkeypatch.setattr(registry_module, "MAX_OPERATIONS_PER_NAMESPACE", 4)
    monkeypatch.setattr(registry_module, "MAX_TOTAL_OPERATIONS", 1)
    with pytest.raises(NamespaceRegistryError, match="total_operation_count_limit_exceeded"):
        NamespaceRegistry([_namespace("a", "A", _operation("x", "X")), _namespace("b", "B", _operation("y", "Y"))])


def test_schema_per_and_aggregate_canonical_byte_limits(monkeypatch):
    monkeypatch.setattr(registry_module, "MAX_SCHEMA_BYTES", 6)
    with pytest.raises(NamespaceRegistryError, match="schema_byte_limit_exceeded"):
        NamespaceRegistry([_namespace("a", "A", _operation("x", "X", {"x": 1}))])

    monkeypatch.setattr(registry_module, "MAX_SCHEMA_BYTES", 4)
    with pytest.raises(NamespaceRegistryError, match="schema_byte_limit_exceeded"):
        NamespaceRegistry([_namespace("a", "A", _operation("x", "X", {"value": "x"}))])

    monkeypatch.setattr(registry_module, "MAX_SCHEMA_BYTES", 10)
    with pytest.raises(NamespaceRegistryError, match="schema_byte_limit_exceeded"):
        NamespaceRegistry([_namespace("a", "A", _operation("x", "X", {"a": "12345", "b": "12345"}))])

    monkeypatch.setattr(registry_module, "MAX_SCHEMA_BYTES", 4)
    with pytest.raises(NamespaceRegistryError, match="schema_byte_limit_exceeded"):
        NamespaceRegistry([_namespace("a", "A", _operation("x", "X", {"x": "ééé"}))])

    monkeypatch.setattr(registry_module, "MAX_SCHEMA_BYTES", 100)
    monkeypatch.setattr(registry_module, "MAX_TOTAL_SCHEMA_BYTES", 13)
    with pytest.raises(NamespaceRegistryError, match="aggregate_schema_byte_limit_exceeded"):
        NamespaceRegistry(
            [_namespace("a", "A", _operation("x", "X", {"x": 1})), _namespace("b", "B", _operation("y", "Y", {"y": 2}))]
        )


def test_schema_depth_and_node_limits_accept_boundary_and_reject_overflow(monkeypatch):
    monkeypatch.setattr(registry_module, "MAX_SCHEMA_DEPTH", 3)
    NamespaceRegistry([_namespace("depth-ok", "Depth", _operation("op", "Op", {"a": {"b": 1}}))])
    monkeypatch.setattr(registry_module, "MAX_SCHEMA_DEPTH", 2)
    with pytest.raises(NamespaceRegistryError, match="schema_depth_limit_exceeded"):
        NamespaceRegistry(
            [_namespace("depth-over", "Depth", _operation("op", "Op", {"a": {"b": {"c": 1}}}))]
        )

    monkeypatch.setattr(registry_module, "MAX_SCHEMA_DEPTH", 64)
    monkeypatch.setattr(registry_module, "MAX_SCHEMA_NODES", 3)
    NamespaceRegistry([_namespace("nodes-ok", "Nodes", _operation("op", "Op", {"a": 1}))])
    monkeypatch.setattr(registry_module, "MAX_SCHEMA_NODES", 4)
    with pytest.raises(NamespaceRegistryError, match="schema_node_limit_exceeded"):
        NamespaceRegistry([_namespace("nodes-over", "Nodes", _operation("op", "Op", {"a": 1, "b": 2}))])


def test_oversized_builtin_schema_is_rejected_before_key_traversal(monkeypatch):
    monkeypatch.setattr(registry_module, "MAX_SCHEMA_NODES", 10)
    schema = {f"key-{index}": index for index in range(100)}

    with pytest.raises(NamespaceRegistryError, match="schema_node_limit_exceeded"):
        NamespaceRegistry([_namespace("bounded", "Bounded", _operation("op", "Op", schema))])


def test_custom_mapping_is_rejected_without_iteration():
    class HostileMapping(dict):
        def items(self):
            raise AssertionError("custom mapping must not be traversed")

    with pytest.raises(NamespaceRegistryError, match="schema_must_be_object"):
        NamespaceRegistry([_namespace("bounded", "Bounded", _operation("op", "Op", HostileMapping()))])


def test_duplicate_ids_and_invalid_schemas_fail_closed():
    with pytest.raises(NamespaceRegistryError, match="duplicate_namespace_id"):
        NamespaceRegistry([_namespace("same", "A"), _namespace("same", "B")])
    with pytest.raises(NamespaceRegistryError, match="duplicate_operation_id"):
        NamespaceRegistry([_namespace("ns", "N", _operation("same", "A"), _operation("same", "B"))])
    with pytest.raises(NamespaceRegistryError, match="schema_contains_non_json_value"):
        NamespaceRegistry([_namespace("ns", "N", _operation("op", "O", {"callable": lambda: None}))])
