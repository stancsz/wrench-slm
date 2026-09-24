import json
from unittest.mock import Mock, patch

import pytest

from wrench_harness.artifact_store import ArtifactStore
from wrench_harness.e0_context_pipeline import PreparationStatus
from wrench_harness.opencode_context import (
    OpenCodePreparationJoin,
    prepare_opencode_e0_context,
)
from wrench_harness.opencode_session_root import OpenCodeSessionRootError
from wrench_harness.namespace_registry import (
    NamespaceDescriptor,
    NamespaceRegistry,
    OperationDescriptor,
)
from wrench_harness.snapshot import SourceSnapshot, create_snapshot


def _preparation_arguments(snapshot):
    return {
        "snapshot": snapshot,
        "paths": ["src/main.py"],
        "store": Mock(),
        "query": "find entry point",
        "source_order_start": 0,
        "context_token_budget": 64,
        "prompt_token_budget": 128,
        "namespace_registry": Mock(),
        "schema_lookups": [],
        "base_messages": [],
        "context_position": 0,
        "serializer": lambda messages: "{}",
        "tokenizer_counter": lambda payload: len(payload),
        "serializer_id": "fixture-json-v1",
        "tokenizer_id": "fixture-char-count-v1",
    }


def test_session_root_is_the_only_root_passed_to_preparation(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    snapshot = SourceSnapshot("wrench.source-snapshot.v2", (), "a" * 64, "b" * 64)
    prepared = Mock(status=PreparationStatus.READY)

    with patch("wrench_harness.opencode_context.prepare_e0_context", return_value=prepared) as prepare:
        result = prepare_opencode_e0_context(
            "ses_fixture123",
            {"id": "ses_fixture123", "location": {"directory": str(root)}},
            **_preparation_arguments(snapshot),
        )

    assert isinstance(result, OpenCodePreparationJoin)
    assert result.session_id == "ses_fixture123"
    assert result.configured_root == root
    assert result.snapshot_sha256 == snapshot.snapshot_sha256
    assert result.root_location_sha256 == snapshot.root_location_sha256
    assert result.preparation is prepared
    assert prepare.call_args.kwargs["source_root"] == root
    assert "source_root" not in _preparation_arguments(snapshot)


def test_invalid_session_fails_before_preparation(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    snapshot = SourceSnapshot("wrench.source-snapshot.v2", (), "a" * 64, "b" * 64)

    with patch("wrench_harness.opencode_context.prepare_e0_context") as prepare:
        with pytest.raises(OpenCodeSessionRootError):
            prepare_opencode_e0_context(
                "ses_event123",
                {"id": "ses_other123", "location": {"directory": str(root)}},
                **_preparation_arguments(snapshot),
            )

    prepare.assert_not_called()


def test_resolved_root_and_snapshot_identity_reach_real_preparation(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "sample.py").write_text("def target():\n    return 7\n", encoding="utf-8")
    snapshot = create_snapshot(root, ["sample.py"])
    registry = NamespaceRegistry([
        NamespaceDescriptor("files", "File metadata", (
            OperationDescriptor("inspect", "Inspect one path", {
                "type": "object", "properties": {"path": {"type": "string"}},
            }),
        )),
    ])

    result = prepare_opencode_e0_context(
        "ses_fixture123",
        {"id": "ses_fixture123", "location": {"directory": str(root)}},
        snapshot=snapshot,
        paths=("sample.py",),
        store=ArtifactStore(tmp_path / "store"),
        query="target",
        source_order_start=0,
        context_token_budget=128,
        prompt_token_budget=4096,
        namespace_registry=registry,
        schema_lookups=(("files", "inspect"),),
        base_messages=({"role": "system", "content": "fixture"},),
        context_position=1,
        serializer=lambda messages: json.dumps(messages, sort_keys=True),
        tokenizer_counter=lambda serialized: len(serialized),
        serializer_id="fixture-json-v1",
        tokenizer_id="fixture-char-count-v1",
    )

    assert result.preparation.status is PreparationStatus.READY
    assert result.session_id == "ses_fixture123"
    assert result.configured_root == root
    assert result.snapshot_sha256 == snapshot.snapshot_sha256
    assert result.root_location_sha256 == snapshot.root_location_sha256
    assert "target" in result.preparation.prompt


def test_session_root_mismatch_produces_no_prompt(tmp_path):
    snapshot_root = tmp_path / "snapshot-project"
    session_root = tmp_path / "session-project"
    snapshot_root.mkdir()
    session_root.mkdir()
    source = "def target():\n    return 7\n"
    (snapshot_root / "sample.py").write_text(source, encoding="utf-8")
    (session_root / "sample.py").write_text(source, encoding="utf-8")
    snapshot = create_snapshot(snapshot_root, ["sample.py"])
    callback_calls = []

    def serializer(messages):
        callback_calls.append("serialize")
        return json.dumps(messages, sort_keys=True)

    def tokenizer_counter(serialized):
        callback_calls.append("tokenize")
        return len(serialized)

    registry = NamespaceRegistry([
        NamespaceDescriptor("files", "File metadata", (
            OperationDescriptor("inspect", "Inspect one path", {
                "type": "object", "properties": {"path": {"type": "string"}},
            }),
        )),
    ])

    result = prepare_opencode_e0_context(
        "ses_fixture123",
        {"id": "ses_fixture123", "location": {"directory": str(session_root)}},
        snapshot=snapshot,
        paths=("sample.py",),
        store=ArtifactStore(tmp_path / "store"),
        query="target",
        source_order_start=0,
        context_token_budget=128,
        prompt_token_budget=4096,
        namespace_registry=registry,
        schema_lookups=(("files", "inspect"),),
        base_messages=({"role": "system", "content": "fixture"},),
        context_position=1,
        serializer=serializer,
        tokenizer_counter=tokenizer_counter,
        serializer_id="fixture-json-v1",
        tokenizer_id="fixture-char-count-v1",
    )

    assert result.preparation.status is PreparationStatus.SOURCE_MISSES
    assert result.preparation.prompt is None
    assert result.preparation.selected_evidence_ids == ()
    assert result.preparation.sources[0].status == "unknown_snapshot"
    assert callback_calls == []
