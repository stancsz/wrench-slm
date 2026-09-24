from __future__ import annotations

import json
import os
import subprocess
from dataclasses import replace

from wrench_harness import core
from wrench_harness import e0_route_preparation
from wrench_harness.artifact_store import ArtifactStore
from wrench_harness.e0_context_pipeline import PreparationStatus
from wrench_harness.e0_route_preparation import (
    MAX_ROUTE_PREPARATION_RECEIPT_BYTES,
    RoutePreparationStatus,
    route_and_prepare_e0_context,
    verify_route_preparation_accounting_receipt,
)
from wrench_harness.e0_rule_route import RuleRouteStatus
from wrench_harness.namespace_registry import NamespaceRegistry
from wrench_harness.prompt_compiler import PromptGateStatus
from wrench_harness.prompt_compiler import materialize_prompt_messages
from wrench_harness.snapshot import bind_source_root, create_snapshot


_FILES = {
    "src/service.py": b"def normalize(value):\n    return value.strip()\n# route-join-fixture-42\n",
    "logs/session.log": b"event=route-join-fixture-42\n",
    "tests/test_service.py": b"def test_normalize():\n    assert normalize(' x ') == 'x'\n# route-join-fixture-42\n",
}
_ROUTE_PROMPT = "Find the exact text 'route-join-fixture-42' below ., capped at 10 matches."


def _tripwires(monkeypatch):
    def fail(name):
        def unexpected(*_args, **_kwargs):
            raise AssertionError(f"unexpected execution path: {name}")
        return unexpected

    monkeypatch.setattr(core, "execute_proposal", fail("execute_proposal"))
    monkeypatch.setattr(core, "execute_model_output", fail("execute_model_output"))
    monkeypatch.setattr(subprocess, "run", fail("subprocess.run"))
    monkeypatch.setattr(subprocess, "Popen", fail("subprocess.Popen"))
    monkeypatch.setattr(os, "system", fail("os.system"))


def _run(tmp_path, *, context_budget=512, prompt=_ROUTE_PROMPT):
    root = tmp_path / "repo"
    root.mkdir()
    for relative_path, content in _FILES.items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    binding = bind_source_root(root)
    snapshot = create_snapshot(binding, tuple(_FILES))
    result = route_and_prepare_e0_context(
        prompt,
        root_binding=binding,
        snapshot=snapshot,
        store=ArtifactStore(tmp_path / f"store-{context_budget}"),
        query="route-join-fixture-42",
        source_order_start=1,
        context_token_budget=context_budget,
        prompt_token_budget=8192,
        namespace_registry=NamespaceRegistry([]),
        schema_lookups=(),
        base_messages=({"role": "system", "content": "Authored synthetic fixture."},),
        context_position=1,
        serializer=lambda messages: json.dumps(
            materialize_prompt_messages(messages), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
        tokenizer_counter=lambda value: len(value),
        serializer_id="fixture-json-v1",
        tokenizer_id="fixture-char-count-v1",
    )
    return result, root, binding, snapshot


def test_orchestrator_routes_then_joins_exact_required_source_hashes(tmp_path, monkeypatch):
    _tripwires(monkeypatch)
    result, _, _, _ = _run(tmp_path)

    assert result.status is RoutePreparationStatus.JOINED
    assert result.route_result.status is RuleRouteStatus.COMPLETED
    assert result.route_result.action == "literal_search"
    assert result.preparation.status is PreparationStatus.READY
    assert result.preparation.prompt_gate.status is PromptGateStatus.READY
    assert result.preparation.prompt is not None
    assert result.accounting_receipt is not None
    assert verify_route_preparation_accounting_receipt(
        result.accounting_receipt,
        route_result=result.route_result,
        preparation=result.preparation,
    )

    route_hashes = {row.path: row.content_sha256 for row in result.route_result.evidence}
    prepared_hashes = {
        row.path: row.content_sha256 for row in result.preparation.sources if row.status == "ok"
    }
    assert prepared_hashes == route_hashes
    payload = json.loads(result.accounting_receipt.payload_json)
    assert payload["snapshot_sha256"] == result.route_result.snapshot_sha256
    assert payload["route_status"] == "completed"
    assert payload["action"] == "literal_search"
    assert payload["route_counters"] == {
        "exact_read_attempts": 3,
        "exact_read_successes": 3,
        "exact_read_bytes": sum(len(content) for content in _FILES.values()),
    }
    assert payload["preparation_accounting_sha256"] == result.preparation.accounting_receipt.accounting_sha256
    assert len(payload["evidence_join"]) == 3
    assert all(row["route_content_sha256"] == row["preparation_content_sha256"] for row in payload["evidence_join"])


def test_route_abstention_does_not_prepare_caller_selected_paths(tmp_path):
    result, _, _, _ = _run(tmp_path, prompt="Summarize the repository.")

    assert result.status is RoutePreparationStatus.ROUTE_NOT_COMPLETED
    assert result.route_result.status is RuleRouteStatus.ABSTAIN
    assert result.preparation is None
    assert result.accounting_receipt is None


def test_stale_snapshot_abstention_does_not_prepare_sources(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    for relative_path, content in _FILES.items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    binding = bind_source_root(root)
    snapshot = create_snapshot(binding, tuple(_FILES))
    (root / "src/service.py").write_bytes(b"changed after snapshot\n")

    stale = route_and_prepare_e0_context(
        _ROUTE_PROMPT,
        root_binding=binding,
        snapshot=snapshot,
        store=ArtifactStore(tmp_path / "store"),
        query="route-join-fixture-42",
        source_order_start=1,
        context_token_budget=512,
        prompt_token_budget=8192,
        namespace_registry=NamespaceRegistry([]),
        schema_lookups=(),
        base_messages=({"role": "system", "content": "Authored synthetic fixture."},),
        context_position=1,
        serializer=lambda messages: json.dumps(materialize_prompt_messages(messages), sort_keys=True, separators=(",", ":")),
        tokenizer_counter=lambda value: len(value),
        serializer_id="fixture-json-v1",
        tokenizer_id="fixture-char-count-v1",
    )
    assert stale.status is RoutePreparationStatus.ROUTE_NOT_COMPLETED
    assert stale.route_result.status is RuleRouteStatus.ABSTAIN
    assert stale.route_result.reason == "snapshot_read_changed"
    assert stale.preparation is None
    assert stale.accounting_receipt is None


def test_required_evidence_budget_omission_returns_no_prompt_but_join_receipt(tmp_path):
    result, _, _, _ = _run(tmp_path, context_budget=1)

    assert result.status is RoutePreparationStatus.JOINED
    assert result.preparation.status is PreparationStatus.PROMPT_REJECTED
    assert result.preparation.prompt is None
    assert result.preparation.prompt_gate.status is PromptGateStatus.REQUIRED_EVIDENCE_OMITTED
    assert result.preparation.outcome_receipt.status.value == "incomplete"
    assert result.preparation.omitted_evidence
    assert result.accounting_receipt is not None
    assert verify_route_preparation_accounting_receipt(
        result.accounting_receipt,
        route_result=result.route_result,
        preparation=result.preparation,
    )


def test_accounting_join_rejects_digest_mutation_and_oversize_receipt(tmp_path):
    result, _, _, _ = _run(tmp_path)
    receipt = result.accounting_receipt
    assert receipt is not None

    changed = replace(receipt, payload_json=receipt.payload_json.replace('"exact_read_attempts":3', '"exact_read_attempts":2'))
    assert not verify_route_preparation_accounting_receipt(
        changed, route_result=result.route_result, preparation=result.preparation
    )
    oversized = replace(receipt, payload_json=" " * (MAX_ROUTE_PREPARATION_RECEIPT_BYTES + 1))
    assert not verify_route_preparation_accounting_receipt(
        oversized, route_result=result.route_result, preparation=result.preparation
    )


def test_interstep_source_change_fails_closed_without_route_preparation_receipt(
    tmp_path, monkeypatch
):
    original_prepare = e0_route_preparation.prepare_e0_context
    mutations = []

    def mutate_after_route_then_prepare(**kwargs):
        service_file = kwargs["source_root"].configured_root / "src" / "service.py"
        service_file.write_bytes(b"def normalize(value):\n    return value.lower()\n")
        mutations.append(service_file)
        return original_prepare(**kwargs)

    monkeypatch.setattr(
        e0_route_preparation, "prepare_e0_context", mutate_after_route_then_prepare
    )
    result, _, _, _ = _run(tmp_path)

    assert len(mutations) == 1
    assert result.route_result.status is RuleRouteStatus.COMPLETED
    assert result.status is RoutePreparationStatus.EVIDENCE_JOIN_MISMATCH
    assert result.preparation is not None
    assert result.accounting_receipt is None
    assert not verify_route_preparation_accounting_receipt(
        result.accounting_receipt,
        route_result=result.route_result,
        preparation=result.preparation,
    )
