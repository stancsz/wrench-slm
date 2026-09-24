import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from wrench_harness.artifact_store import ArtifactStore
from wrench_harness.e0_context_pipeline import PreparationResult, PreparationStatus
from wrench_harness.opencode_context import (
    OpenCodeAdmissionStatus,
    OpenCodePreparationAdmission,
    OpenCodePreparationJoin,
    check_opencode_preparation_admission,
    prepare_opencode_e0_context,
)
from wrench_harness.outcome_receipt import (
    ReceiptResult,
    ReceiptStatus,
    build_outcome_receipt,
)
from wrench_harness.opencode_session_root import (
    OpenCodeSessionRootError,
    resolve_opencode_session_root,
)
from wrench_harness.namespace_registry import (
    NamespaceDescriptor,
    NamespaceRegistry,
    OperationDescriptor,
)
from wrench_harness.snapshot import SourceRootBinding, SourceSnapshot, create_snapshot
from wrench_harness.prompt_compiler import PromptGateReceipt, PromptGateStatus


def _admission_fixture():
    prompt_hash = "c" * 64
    gate = PromptGateReceipt(
        status=PromptGateStatus.READY,
        session_hash="d" * 64,
        selected_evidence_ids=(),
        omitted_evidence=(),
        required_evidence_reasons=(),
        prompt_sha256=prompt_hash,
        exact_token_count=1,
        hard_budget=8,
        tokenizer_id="fixture-tokenizer",
        serializer_id="fixture-serializer",
        serialized_bytes=2,
    )
    aggregate_hash = "a" * 64
    snapshot_hash = "b" * 64
    receipt = build_outcome_receipt({
        "schema": "wrench.e0.outcome-receipt.v1",
        "task_id": "e0-context-preparation",
        "run_id": aggregate_hash,
        "snapshot_sha256": snapshot_hash,
        "context_receipt_sha256": aggregate_hash,
        "selected_evidence_ids": [],
        "omitted_evidence_ids": [],
        "retrieval_misses": [],
        "actual_route": "none",
        "attempts": [],
        "work_calls": [],
        "verifier": {"identity": None, "result": "not_run", "evidence_ids": []},
        "outcome": {"status": "unknown", "provenance": "unknown", "evidence_ids": []},
        "correction_refs": [],
        "accounting": {
            "local_model_calls": 0,
            "frontier_model_calls": 0,
            "retries": 0,
            "fallback_calls": 0,
            "verifier_calls": 0,
            "tool_calls": 0,
            "local_tokens": 0,
            "frontier_tokens": 0,
            "local_token_counter_id": None,
            "frontier_token_counter_id": None,
            "token_count_status": "not_applicable",
            "local_cost_microunits": 0,
            "frontier_cost_microunits": 0,
            "cost_status": "known",
        },
        "completeness": "incomplete",
        "missing_fields": ["outcome"],
    })
    preparation = PreparationResult(
        status=PreparationStatus.READY,
        route="none",
        prompt="{}",
        prompt_gate=gate,
        outcome_receipt=receipt,
        aggregate_sha256=aggregate_hash,
        sources=(),
        selected_evidence_ids=(),
        omitted_evidence=(),
        retrieval_misses=(),
        schema_digests=(),
        structural_status="ready",
    )
    join = OpenCodePreparationJoin(
        session_id="ses_fixture123",
        configured_root=Path("C:/fixture"),
        snapshot_sha256=snapshot_hash,
        root_location_sha256="b" * 64,
        root_identity="posix:1:1",
        preparation=preparation,
    )
    return join


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
    snapshot = SourceSnapshot("wrench.source-snapshot.v3", (), "a" * 64, "b" * 64, "posix:1:1")
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
    assert result.root_identity == snapshot.root_identity
    assert result.preparation is prepared
    bound_root = prepare.call_args.kwargs["source_root"]
    assert type(bound_root) is SourceRootBinding
    assert bound_root.configured_root == root
    assert "source_root" not in _preparation_arguments(snapshot)


def test_caller_owned_artifact_request_reaches_preparation(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    snapshot = SourceSnapshot("wrench.source-snapshot.v3", (), "a" * 64, "b" * 64, "posix:1:1")
    store = ArtifactStore(tmp_path / "store")
    prepared = Mock(status=PreparationStatus.READY)

    with store.request() as request:
        arguments = _preparation_arguments(snapshot)
        arguments["store"] = store
        arguments["artifact_request"] = request
        with patch("wrench_harness.opencode_context.prepare_e0_context", return_value=prepared) as prepare:
            result = prepare_opencode_e0_context(
                "ses_fixture123",
                {"id": "ses_fixture123", "location": {"directory": str(root)}},
                **arguments,
            )

    assert result.preparation is prepared
    assert prepare.call_args.kwargs["artifact_request"] is request


def test_real_opencode_preparation_pins_until_caller_request_scope_closes(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "sample.py").write_text("def target():\n    return 7\n", encoding="utf-8")
    snapshot = create_snapshot(root, ["sample.py"])
    registry = NamespaceRegistry([NamespaceDescriptor("files", "Files", (
        OperationDescriptor("inspect", "Inspect", {"type": "object"}),
    ))])
    store = ArtifactStore(tmp_path / "store")

    with store.request() as request:
        join = prepare_opencode_e0_context(
            "ses_fixture123",
            {"id": "ses_fixture123", "location": {"directory": str(root)}},
            snapshot=snapshot,
            paths=("sample.py",),
            store=store,
            query="target",
            source_order_start=0,
            context_token_budget=128,
            prompt_token_budget=4096,
            namespace_registry=registry,
            schema_lookups=(),
            base_messages=({"role": "system", "content": "fixture"},),
            context_position=1,
            serializer=lambda messages: json.dumps(messages, sort_keys=True),
            tokenizer_counter=lambda serialized: len(serialized),
            serializer_id="fixture-json-v1",
            tokenizer_id="fixture-char-count-v1",
            artifact_request=request,
        )
        assert join.preparation.status is PreparationStatus.READY
        assert store._pins
        assert store.evict(target_bytes=1, now_unix_seconds=10).handles == ()

    assert store._pins == {}
    assert store.evict(target_bytes=1, now_unix_seconds=10).handles == ()


def test_invalid_session_fails_before_preparation(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    snapshot = SourceSnapshot("wrench.source-snapshot.v3", (), "a" * 64, "b" * 64, "posix:1:1")

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
    assert result.root_identity == snapshot.root_identity
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


def test_resolved_session_root_binding_survives_replacement_before_preparation(tmp_path):
    root = tmp_path / "session-project"
    root.mkdir()
    (root / "sample.py").write_text("def target():\n    return 7\n", encoding="utf-8")
    record = {"id": "ses_fixture123", "location": {"directory": str(root)}}
    resolved = resolve_opencode_session_root("ses_fixture123", record)
    snapshot = create_snapshot(resolved.binding, ["sample.py"])

    replacement = tmp_path / "replacement-project"
    replacement.mkdir()
    (replacement / "sample.py").write_text("def target():\n    return 7\n", encoding="utf-8")
    saved = tmp_path / "saved-session-project"
    root.rename(saved)
    replacement.rename(root)
    callback_calls = []
    arguments = _preparation_arguments(snapshot)
    arguments["serializer"] = lambda messages: callback_calls.append("serialize") or "{}"
    arguments["tokenizer_counter"] = lambda payload: callback_calls.append("tokenize") or len(payload)

    with patch("wrench_harness.opencode_context.prepare_e0_context") as prepare:
        with pytest.raises(OpenCodeSessionRootError, match="session_root_binding_mismatch"):
            prepare_opencode_e0_context(
                "ses_fixture123",
                record,
                **arguments,
                resolved_session_root=resolved,
            )

    prepare.assert_not_called()
    assert callback_calls == []


def test_preparation_admission_returns_join_only_when_all_local_gates_are_ready():
    join = _admission_fixture()

    admitted = check_opencode_preparation_admission(join.session_id, join)

    assert admitted == OpenCodePreparationAdmission(
        OpenCodeAdmissionStatus.READY, join, "ready"
    )


@pytest.mark.parametrize(
    ("event_session_id", "preparation_changes", "expected"),
    [
        ("ses_other123", {}, OpenCodeAdmissionStatus.SESSION_MISMATCH),
        ("ses_fixture123", {"status": PreparationStatus.SOURCE_MISSES}, OpenCodeAdmissionStatus.PREPARATION_NOT_READY),
        ("ses_fixture123", {"route": "frontier"}, OpenCodeAdmissionStatus.ROUTE_UNEXPECTED),
        ("ses_fixture123", {"prompt": None}, OpenCodeAdmissionStatus.PROMPT_MISSING),
        ("ses_fixture123", {"prompt_gate": None}, OpenCodeAdmissionStatus.PROMPT_GATE_NOT_READY),
        (
            "ses_fixture123",
            {"prompt_gate": replace(_admission_fixture().preparation.prompt_gate, status=PromptGateStatus.BUDGET_EXCEEDED)},
            OpenCodeAdmissionStatus.PROMPT_GATE_NOT_READY,
        ),
        (
            "ses_fixture123",
            {"outcome_receipt": ReceiptResult(ReceiptStatus.INCOMPLETE, None)},
            OpenCodeAdmissionStatus.PREPARATION_RECEIPT_INVALID,
        ),
        (
            "ses_fixture123",
            {"outcome_receipt": ReceiptResult(ReceiptStatus.VALID, None)},
            OpenCodeAdmissionStatus.PREPARATION_RECEIPT_INVALID,
        ),
        (
            "ses_fixture123",
            {"outcome_receipt": ReceiptResult(ReceiptStatus.INVALID, None)},
            OpenCodeAdmissionStatus.PREPARATION_RECEIPT_INVALID,
        ),
        (
            "ses_fixture123",
            {"retrieval_misses": (("src/missing.py", "unknown_snapshot"),)},
            OpenCodeAdmissionStatus.RETRIEVAL_MISSES,
        ),
    ],
)
def test_preparation_admission_fails_closed(event_session_id, preparation_changes, expected):
    join = _admission_fixture()
    preparation = replace(join.preparation, **preparation_changes)
    candidate = replace(join, preparation=preparation)

    result = check_opencode_preparation_admission(event_session_id, candidate)

    assert result.status is expected
    assert result.join is None


@pytest.mark.parametrize(
    "identity_field",
    ["snapshot_sha256", "context_receipt_sha256"],
)
def test_preparation_admission_rejects_valid_receipt_with_wrong_identity(identity_field):
    join = _admission_fixture()
    payload = json.loads(join.preparation.outcome_receipt.receipt.payload_json)
    payload[identity_field] = "f" * 64
    wrong_identity_receipt = build_outcome_receipt(payload)
    assert wrong_identity_receipt.status is ReceiptStatus.INCOMPLETE
    candidate = replace(
        join,
        preparation=replace(
            join.preparation,
            outcome_receipt=wrong_identity_receipt,
        ),
    )

    result = check_opencode_preparation_admission(join.session_id, candidate)

    assert result.status is OpenCodeAdmissionStatus.PREPARATION_RECEIPT_INVALID
    assert result.reason == "preparation_receipt_identity_mismatch"
    assert result.join is None
