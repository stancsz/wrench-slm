from __future__ import annotations

import json
import os
import subprocess

from wrench_harness import core
from wrench_harness.artifact_store import ArtifactStore
from wrench_harness.e0_context_pipeline import PreparationStatus, prepare_e0_context
from wrench_harness.e0_rule_route import RuleRouteStatus, run_e0_rule_route
from wrench_harness.namespace_registry import NamespaceRegistry
from wrench_harness.outcome_receipt import ReceiptStatus
from wrench_harness.prompt_compiler import PromptGateStatus, materialize_prompt_messages
from wrench_harness.snapshot import bind_source_root, create_snapshot


_FILES = {
    "src/service.py": (
        b"def normalize(value):\n"
        b"    return value.strip()\n"
        b"# triage-marker-2026 source observation\n"
    ),
    "logs/session.log": b"fixture event=triage-marker-2026\n",
    "tests/test_service.py": (
        b"def test_normalize():\n"
        b"    assert normalize(' x ') == 'x'\n"
        b"# triage-marker-2026 test observation\n"
    ),
}


def _install_tripwires(monkeypatch):
    def fail(name):
        def unexpected(*_args, **_kwargs):
            raise AssertionError(f"unexpected execution path: {name}")
        return unexpected

    monkeypatch.setattr(core, "execute_proposal", fail("execute_proposal"))
    monkeypatch.setattr(core, "execute_model_output", fail("execute_model_output"))
    monkeypatch.setattr(subprocess, "run", fail("subprocess.run"))
    monkeypatch.setattr(subprocess, "Popen", fail("subprocess.Popen"))
    monkeypatch.setattr(os, "system", fail("os.system"))


def _compose(tmp_path, *, context_budget: int):
    root = tmp_path / "repo"
    root.mkdir()
    for relative_path, content in _FILES.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    binding = bind_source_root(root)
    snapshot = create_snapshot(binding, tuple(_FILES))
    routed = run_e0_rule_route(
        "Find the exact text 'triage-marker-2026' below ., capped at 10 matches.",
        root_binding=binding,
        snapshot=snapshot,
    )
    assert routed.status is RuleRouteStatus.COMPLETED
    assert routed.route == "none"
    assert routed.action == "literal_search"
    assert routed.snapshot_sha256 == snapshot.snapshot_sha256
    matches = routed.observation["matches"]
    paths = tuple(dict.fromkeys(row["path"] for row in matches))
    assert set(paths) == set(_FILES)
    assert routed.exact_read_attempts == routed.exact_read_successes == len(_FILES)

    route_message = {
        "schema": "wrench.synthetic.route-result-reference.v1",
        "provenance": "caller-supplied offline route result",
        "snapshot_sha256": routed.snapshot_sha256,
        "action": routed.action,
        "matches": matches,
    }
    prepared = prepare_e0_context(
        source_root=binding,
        snapshot=snapshot,
        paths=paths,
        store=ArtifactStore(tmp_path / f"store-{context_budget}"),
        query="triage-marker-2026",
        source_order_start=1,
        context_token_budget=context_budget,
        prompt_token_budget=8192,
        namespace_registry=NamespaceRegistry([]),
        schema_lookups=(),
        base_messages=(
            {"role": "system", "content": "Fixed synthetic fixture instruction."},
            {"role": "user", "content": json.dumps(route_message, sort_keys=True)},
        ),
        context_position=1,
        serializer=lambda messages: json.dumps(
            materialize_prompt_messages(messages), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
        tokenizer_counter=lambda value: len(value),
        serializer_id="fixture-json-v1",
        tokenizer_id="fixture-char-count-v1",
        required_source_paths=paths,
        preserve_source_paths=paths,
    )
    return routed, prepared, paths


def test_route_result_composes_required_source_log_and_test_evidence(tmp_path, monkeypatch):
    _install_tripwires(monkeypatch)
    routed, prepared, paths = _compose(tmp_path, context_budget=256)

    assert prepared.status is PreparationStatus.READY
    assert prepared.route == "none"
    assert prepared.prompt is not None
    assert prepared.prompt_gate.status is PromptGateStatus.READY
    assert prepared.prompt_gate.required_evidence_reasons == ()
    assert prepared.outcome_receipt.status is ReceiptStatus.INCOMPLETE

    route_hashes = {row.path: row.content_sha256 for row in routed.evidence}
    prepared_hashes = {row.path: row.content_sha256 for row in prepared.sources if row.status == "ok"}
    assert set(prepared_hashes) == set(paths)
    assert prepared_hashes == route_hashes
    assert {
        row.evidence_id for row in prepared.sources if row.status == "ok"
    }.issubset(set(prepared.selected_evidence_ids))

    prompt_messages = json.loads(prepared.prompt)
    route_reference = json.loads(prompt_messages[-1]["content"])
    assert route_reference["snapshot_sha256"] == routed.snapshot_sha256
    assert {row["path"] for row in route_reference["matches"]} == set(paths)
    context_content = prompt_messages[1]["content"]
    context_text = json.loads(
        context_content[
            context_content.index("BEGIN UNTRUSTED SOURCE JSON STRING\n")
            + len("BEGIN UNTRUSTED SOURCE JSON STRING\n"):
            -len("\nEND UNTRUSTED SOURCE JSON STRING")
        ]
    )
    for relative_path, content in _FILES.items():
        assert content.decode("utf-8") in context_text
        assert any(row.path == relative_path for row in prepared.sources)


def test_route_composition_rejects_all_required_preserved_sources_when_hot_budget_is_tight(tmp_path, monkeypatch):
    _install_tripwires(monkeypatch)
    routed, prepared, paths = _compose(tmp_path, context_budget=1)

    assert prepared.status is PreparationStatus.PROMPT_REJECTED
    assert prepared.route == "none"
    assert prepared.prompt is None
    assert prepared.prompt_gate.status is PromptGateStatus.REQUIRED_EVIDENCE_OMITTED
    assert prepared.outcome_receipt.status is ReceiptStatus.INCOMPLETE

    source_ids = {row.path: row.evidence_id for row in prepared.sources if row.status == "ok"}
    assert set(source_ids) == set(paths)
    assert {row.path: row.content_sha256 for row in prepared.sources if row.status == "ok"} == {
        row.path: row.content_sha256 for row in routed.evidence
    }
    expected_omissions = {
        (evidence_id, "preserved_unit_exceeds_active_budget")
        for evidence_id in source_ids.values()
    }
    assert set(prepared.prompt_gate.required_evidence_reasons) == expected_omissions
    assert expected_omissions.issubset(set(prepared.omitted_evidence))
