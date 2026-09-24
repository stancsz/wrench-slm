from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
from dataclasses import replace
from unittest.mock import patch

from wrench_harness.artifact_store import ArtifactStore
from wrench_harness.e0_baseline_accounting import (
    build_e0_baseline_accounting_receipt,
    verify_e0_baseline_accounting_receipt,
    _payload as _baseline_payload,
)
from wrench_harness.e0_offline_request_composition import (
    CompositionStatus,
    finalize_offline_e0_request,
    prepare_offline_e0_request,
)
import wrench_harness.e0_offline_request_composition as composition
from wrench_harness.namespace_registry import NamespaceRegistry
from wrench_harness.opencode_project_registry import OpenCodeProjectRegistry
from wrench_harness.opencode_project_snapshot import prepare_opencode_project_snapshot
from wrench_harness.opencode_request_boundary import FixtureResponse, RequestLeaseBoundary, StreamEnd
from wrench_harness.snapshot_coverage import _inventory_payload, build_snapshot_inventory_receipt


_TMP = Path(r"C:\wrench-slm-data\tmp\W2-NS-E0-BASELINE-ACCOUNTING-20260924")
_SESSION = "ses_baseline_accounting001"


def _assert_raises(expected_type, expected_text, callback):
    try:
        callback()
    except expected_type as exc:
        assert expected_text in str(exc)
    else:
        raise AssertionError(f"expected {expected_type.__name__}")


def _event():
    return {
        "sessionID": _SESSION,
        "agent": "build",
        "model": {"providerID": "synthetic-fixture", "id": "synthetic-fixture"},
        "system": [{"type": "text", "text": "Synthetïc fixture rules."}],
        "messages": [
            {"role": "system", "content": [{"type": "text", "text": "Synthetic only."}]},
            {"role": "user", "content": [{"type": "text", "text": "Explain synthetic_target."}]},
        ],
        "tools": {},
        "options": {"temperature": 0},
    }


def test_baseline_accounting_joins_complete_inventory_projection_and_fixture_terminal():
    _TMP.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="baseline-accounting-", dir=_TMP) as scratch:
        root = Path(scratch) / "repo"
        root.mkdir()
        (root / "sample.py").write_text("def synthetic_target(value):\n    return value + 1\n", encoding="utf-8")
        data = Path(scratch) / "data"
        data.mkdir()
        registry = OpenCodeProjectRegistry(data)
        registry.enroll_project("prj_baseline", root, ("sample.py",), max_file_bytes=16 * 1024, max_total_bytes=32 * 1024)
        record = {"id": _SESSION, "location": {"directory": str(root)}}
        project_snapshot = prepare_opencode_project_snapshot(registry, _SESSION, record, ("sample.py",))
        inventory = build_snapshot_inventory_receipt(project_snapshot.snapshot, project_snapshot.binding)

        store = ArtifactStore(data / "artifacts")
        boundary = RequestLeaseBoundary(nonce_factory=lambda: "synthetic-baseline-nonce")
        event = _event()
        captured = {}
        original_lower = composition._lower_materialized_event

        def capture(materialized_event, **kwargs):
            captured["event"] = materialized_event
            return original_lower(materialized_event, **kwargs)

        with patch.object(composition, "_lower_materialized_event", side_effect=capture):
            result = prepare_offline_e0_request(
                registry,
                _SESSION,
                record,
                ("sample.py",),
                event=event,
                fixture_response=FixtureResponse((b"data: fixture\n\n",)),
                store=store,
                boundary=boundary,
                namespace_registry=NamespaceRegistry(()),
                query="synthetic_target",
                route_prompt="Find the exact text 'synthetic_target' below ., capped at 10 matches.",
                lease_id="baseline-accounting-lease",
                context_token_budget=128,
                prompt_token_budget=4096,
                max_tokens=16,
            )
        assert result.status is CompositionStatus.READY
        assert result.receipt is not None and result.request is not None
        assert captured.get("event") is not None
        stream = boundary.dispatch(result.request, result.fixture_response)
        assert list(stream) == [b"data: fixture\n\n"]
        terminal = finalize_offline_e0_request(result, stream)
        assert terminal is not None and terminal.terminal_outcome == StreamEnd.COMPLETE.value

        join_args = (
            project_snapshot,
            inventory,
            result.receipt,
            terminal,
            captured["event"],
            result.request,
        )
        receipt = build_e0_baseline_accounting_receipt(
            *join_args,
        )
        assert verify_e0_baseline_accounting_receipt(receipt)
        assert receipt.inventory_entry_count == receipt.exact_read_attempts == receipt.exact_read_successes == 1
        assert receipt.accounted_snapshot_manifest_entries == 1
        assert receipt.unaccounted_snapshot_manifest_entries == 0
        assert receipt.enrolled_omission_count is None
        assert receipt.context_candidate_count == result.receipt.candidate_count
        assert receipt.context_selected_candidate_order_sha256 == result.receipt.selected_candidate_order_sha256
        assert receipt.context_selected_candidate_count is None
        assert receipt.context_omitted_candidate_count is None
        assert receipt.route_preparation_sha256 == result.receipt.route_preparation_sha256
        assert receipt.synthetic_token_count == receipt.synthetic_envelope_chars
        assert receipt.synthetic_envelope_bytes > receipt.synthetic_envelope_chars
        assert receipt.lowered_request_body_bytes == len(result.request.body)
        assert "synthetic_target" not in repr(receipt)
        for invalid_count in (0, -1, True):
            forged = replace(receipt, context_candidate_count=invalid_count, receipt_sha256="0" * 64)
            encoded = json.dumps(
                _baseline_payload(forged), ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False,
            ).encode("utf-8")
            forged = replace(forged, receipt_sha256=hashlib.sha256(encoded).hexdigest())
            assert not verify_e0_baseline_accounting_receipt(forged)
        stale_hash = replace(inventory, exact_read_successes=0)
        _assert_raises(ValueError, "identity_or_inventory", lambda: build_e0_baseline_accounting_receipt(
            project_snapshot, stale_hash, result.receipt, terminal, captured["event"], result.request
        ))
        forged_payload = json.dumps(
            _inventory_payload(stale_hash), ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
        forged_inventory = replace(stale_hash, receipt_sha256=hashlib.sha256(forged_payload).hexdigest())
        _assert_raises(ValueError, "identity_or_inventory", lambda: build_e0_baseline_accounting_receipt(
            project_snapshot, forged_inventory, result.receipt, terminal, captured["event"], result.request
        ))
        altered_event = dict(captured["event"])
        altered_event["agent"] = "different-synthetic-agent"
        _assert_raises(ValueError, "projection_join", lambda: build_e0_baseline_accounting_receipt(
            project_snapshot, inventory, result.receipt, terminal, altered_event, result.request
        ))

        source_path = root / "sample.py"
        original_source = source_path.read_bytes()
        source_path.write_bytes(original_source + b"# changed after inventory\n")
        _assert_raises(ValueError, "identity_or_inventory", lambda: build_e0_baseline_accounting_receipt(*join_args))
        source_path.write_bytes(original_source)
        retired_root = root.with_name("repo-retired")
        root.rename(retired_root)
        root.mkdir()
        _assert_raises(ValueError, "source_freshness", lambda: build_e0_baseline_accounting_receipt(*join_args))
