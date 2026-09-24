from __future__ import annotations

import http.client
import hashlib
import json
import socket
import tempfile
import time
from dataclasses import replace
from unittest.mock import patch
from pathlib import Path

from wrench_harness.artifact_store import ArtifactStore
from wrench_harness.e0_offline_request_composition import (
    CompositionStatus,
    SYNTHETIC_SERIALIZER_ID,
    SYNTHETIC_TOKENIZER_ID,
    finalize_offline_e0_request,
    prepare_offline_e0_request,
    verify_offline_e0_composition_receipt,
)
import wrench_harness.e0_offline_request_composition as composition_module
from wrench_harness.namespace_registry import NamespaceRegistry
from wrench_harness.opencode_hook_projection import (
    OpenCodeProjectionStatus,
    project_opencode_context_hook,
)
from wrench_harness.opencode_project_registry import OpenCodeProjectRegistry
from wrench_harness.opencode_request_boundary import (
    FixtureResponse,
    LoopbackFixtureServer,
    RequestLeaseBoundary,
    StreamEnd,
)


TEST_TMP_ROOT = Path(
    r"C:\wrench-slm-data\tmp\W2-NS-E0-OFFLINE-COMPOSITION-20260924"
)
SESSION_ID = "ses_offline_compose001"


def _message(role: str, text: str) -> dict[str, object]:
    return {"role": role, "content": [{"type": "text", "text": text}]}


def _event() -> dict[str, object]:
    return {
        "sessionID": SESSION_ID,
        "agent": "build",
        "model": {"providerID": "synthetic-fixture", "id": "synthetic-fixture"},
        "system": [{"type": "text", "text": "Synthetic fixture rules."}],
        "messages": [
            _message("system", "Use only synthetic fixture evidence."),
            _message("user", "Explain synthetic_target."),
        ],
        "tools": {},
        "options": {"temperature": 0},
    }


def _fixture(tmp_path: Path, *, fixture_response: FixtureResponse | object | None = None,
             timeout_seconds: float = 5):
    source_root = tmp_path / "repo"
    (source_root / "src").mkdir(parents=True)
    (source_root / "src" / "sample.py").write_text(
        "def synthetic_target(value):\n    return value + 1\n",
        encoding="utf-8",
    )
    (source_root / "README.md").write_text(
        "Synthetic offline composition fixture.\n", encoding="utf-8"
    )
    data_root = tmp_path / "wrench-data"
    data_root.mkdir()
    registry = OpenCodeProjectRegistry(data_root)
    registry.enroll_project(
        "prj_offline_compose",
        source_root,
        ("README.md", "src/sample.py"),
        max_file_bytes=16 * 1024,
        max_total_bytes=32 * 1024,
    )
    store = ArtifactStore(data_root / "artifacts")
    nonce_count = 0

    def next_nonce() -> str:
        nonlocal nonce_count
        nonce_count += 1
        return f"synthetic-composition-nonce-{nonce_count}"

    boundary = RequestLeaseBoundary(nonce_factory=next_nonce, timeout_seconds=timeout_seconds)
    response = fixture_response or FixtureResponse((b"data: synthetic-fixture\n\n",))
    return source_root, data_root, registry, store, boundary, response


def _prepare(tmp_path: Path, *, prompt_token_budget: int = 4096, lease_id: str = "fixture-lease",
             fixture_response: FixtureResponse | object | None = None,
             timeout_seconds: float = 5, route_prompt: str | None = None,
             context_token_budget: int = 128):
    source_root, data_root, registry, store, boundary, response = _fixture(
        tmp_path, fixture_response=fixture_response, timeout_seconds=timeout_seconds
    )
    event = _event()
    result = prepare_offline_e0_request(
        registry,
        SESSION_ID,
        {"id": SESSION_ID, "location": {"directory": str(source_root)}},
        ("src/sample.py", "README.md"),
        event=event,
        fixture_response=response,
        store=store,
        boundary=boundary,
        namespace_registry=NamespaceRegistry(()),
        query="synthetic_target",
        route_prompt=route_prompt,
        lease_id=lease_id,
        context_token_budget=context_token_budget,
        prompt_token_budget=prompt_token_budget,
        context_position=1,
        max_candidates=8,
        max_tokens=16,
    )
    return result, store, boundary, response


def test_synthetic_semantic_envelope_accounts_for_all_seven_fields_and_only_inserts_messages():
    projection = _event()
    serializer = composition_module._fixture_serializer_for_projection(projection)
    original_messages = json.loads(json.dumps(projection["messages"]))
    original = serializer(original_messages)
    original_size = len(original)
    mutations = {
        "sessionID": "ses_offline_composition_longer",
        "agent": "build-with-longer-identity",
        "model": {"providerID": "synthetic-fixture", "id": "synthetic-fixture-longer"},
        "system": [{"type": "text", "text": "Synthetic fixture rules, extended."}],
        "messages": [*_event()["messages"], _message("assistant", "A longer synthetic reply.")],
        "tools": {
            "synthetic_tool": {"description": "A synthetic tool.", "input": {"type": "object"}}
        },
        "options": {"temperature": 0, "synthetic_option": "longer"},
    }
    for field, value in mutations.items():
        changed = dict(projection)
        prepared_messages = original_messages
        if field == "messages":
            prepared_messages = value
        else:
            changed[field] = value
        serialized = composition_module._fixture_serializer_for_projection(changed)(prepared_messages)
        assert serialized != original, field
        assert len(serialized) > original_size, field
        assert composition_module._fixture_tokenizer(serialized) > composition_module._fixture_tokenizer(original), field

    inserted_messages = [*original_messages]
    inserted_messages.insert(1, _message("user", "Synthetic inserted context."))
    with_inserted = json.loads(serializer(inserted_messages))
    without_inserted = json.loads(original)
    assert with_inserted["schema"] == without_inserted["schema"]
    assert with_inserted["opencode_context_hook_version"] == without_inserted["opencode_context_hook_version"]
    for field in ("sessionID", "system", "agent", "model", "tools", "options"):
        assert with_inserted["projection"][field] == without_inserted["projection"][field]
    assert with_inserted["projection"]["messages"] == inserted_messages
    assert with_inserted["projection"]["messages"] != without_inserted["projection"]["messages"]


def test_unsupported_hook_projection_fails_closed_before_lease_or_pins():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="projection-reject-", dir=TEST_TMP_ROOT) as scratch:
        source_root, _, registry, store, boundary, response = _fixture(Path(scratch))
        event = _event()
        del event["options"]
        result = prepare_offline_e0_request(
            registry,
            SESSION_ID,
            {"id": SESSION_ID, "location": {"directory": str(source_root)}},
            ("src/sample.py", "README.md"),
            event=event,
            fixture_response=response,
            store=store,
            boundary=boundary,
            namespace_registry=NamespaceRegistry(()),
            query="synthetic_target",
            lease_id="fixture-invalid-projection",
        )
        assert result.status is CompositionStatus.PROJECT_REJECTED
        assert result.request is None and result.ticket is None and result.receipt is None
        assert not result.artifact_scope_active
        assert not store._pins
        assert not boundary._pending and not boundary._active


def test_fixture_unsupported_hook_message_fails_at_lowering_without_lease_or_pins():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lowering-reject-", dir=TEST_TMP_ROOT) as scratch:
        source_root, _, registry, store, boundary, response = _fixture(Path(scratch))
        event = _event()
        event["messages"][1] = _message("tool", "Synthetic tool result.")
        result = prepare_offline_e0_request(
            registry,
            SESSION_ID,
            {"id": SESSION_ID, "location": {"directory": str(source_root)}},
            ("src/sample.py", "README.md"),
            event=event,
            fixture_response=response,
            store=store,
            boundary=boundary,
            namespace_registry=NamespaceRegistry(()),
            query="synthetic_target",
            lease_id="fixture-unsupported-message",
        )
        assert result.status is CompositionStatus.LOWERING_REJECTED
        assert result.request is None and result.ticket is None and result.receipt is None
        assert not result.artifact_scope_active
        assert not store._pins
        assert not boundary._pending and not boundary._active


def test_compiler_message_reaches_loopback_request_and_pins_release_at_eof():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="compose-", dir=TEST_TMP_ROOT) as scratch:
        root = Path(scratch)
        source_root, data_root, registry, store, boundary, fixture_response = _fixture(root)
        event = _event()
        gate_envelopes: list[dict[str, object]] = []
        gate_preparations = []
        materialized_events = []
        original_serializer_factory = composition_module._fixture_serializer_for_projection
        original_prepare_context = composition_module.prepare_opencode_e0_context
        original_materializer = composition_module.materialize_opencode_prepared_context

        def capture_serializer(semantic_projection):
            serialize = original_serializer_factory(semantic_projection)

            def capture(messages):
                serialized = serialize(messages)
                gate_envelopes.append(json.loads(serialized))
                return serialized

            return capture

        def capture_prepare_context(*args, **kwargs):
            joined = original_prepare_context(*args, **kwargs)
            gate_preparations.append(joined.preparation)
            return joined

        def capture_materializer(join, event_snapshot):
            materialized = original_materializer(join, event_snapshot)
            materialized_events.append(materialized.event)
            return materialized

        release_calls: dict[int, int] = {}
        original_release = composition_module._PinScope.release_once

        def counted_release(scope):
            key = id(scope)
            release_calls[key] = release_calls.get(key, 0) + 1
            return original_release(scope)

        with (
            patch.object(composition_module._PinScope, "release_once", counted_release),
            patch.object(composition_module, "_fixture_serializer_for_projection", capture_serializer),
            patch.object(composition_module, "prepare_opencode_e0_context", capture_prepare_context),
            patch.object(composition_module, "materialize_opencode_prepared_context", capture_materializer),
        ):
            first = prepare_offline_e0_request(
                registry,
                SESSION_ID,
                {"id": SESSION_ID, "location": {"directory": str(source_root)}},
                ("src/sample.py", "README.md"),
                event=event,
                fixture_response=fixture_response,
                store=store,
                boundary=boundary,
                namespace_registry=NamespaceRegistry(()),
                query="synthetic_target",
                lease_id="fixture-lease-one",
                context_token_budget=128,
                prompt_token_budget=4096,
                context_position=1,
                max_candidates=8,
                max_tokens=16,
            )
            second = prepare_offline_e0_request(
                registry,
                SESSION_ID,
                {"id": SESSION_ID, "location": {"directory": str(source_root)}},
                ("README.md", "src/sample.py"),
                event=event,
                fixture_response=fixture_response,
                store=store,
                boundary=boundary,
                namespace_registry=NamespaceRegistry(()),
                query="synthetic_target",
                lease_id="fixture-lease-two",
                context_token_budget=128,
                prompt_token_budget=4096,
                context_position=1,
                max_candidates=8,
                max_tokens=16,
            )

        assert first.status is CompositionStatus.READY
        assert second.status is CompositionStatus.READY
        assert first.request is not None and second.request is not None
        assert first.ticket is not None and second.ticket is not None
        assert first.receipt is not None and second.receipt is not None
        assert first.artifact_scope_active and second.artifact_scope_active
        assert first.receipt.candidate_count == 1
        assert (
            first.receipt.selected_candidate_order_sha256
            == second.receipt.selected_candidate_order_sha256
        )
        assert first.receipt.source_hash_join_sha256 == second.receipt.source_hash_join_sha256
        assert first.receipt.preparation_sha256 == second.receipt.preparation_sha256
        assert first.receipt.serializer_id == SYNTHETIC_SERIALIZER_ID
        assert first.receipt.tokenizer_id == SYNTHETIC_TOKENIZER_ID
        assert first.receipt.exact_token_gate == "exact_gate_unavailable"
        assert len(first.receipt.semantic_projection_sha256) == 64
        assert sum(store._pins.values()) > 0

        with LoopbackFixtureServer(boundary, fixture_response) as server:
            for result in (first, second):
                assert result.request is not None
                connection = http.client.HTTPConnection(*server.address, timeout=3)
                connection.request(
                    result.request.method,
                    result.request.url,
                    body=result.request.body,
                    headers=dict(result.request.headers),
                )
                response = connection.getresponse()
                assert response.status == 200
                assert response.read() == b"data: synthetic-fixture\n\n"
                connection.close()
                if result is first:
                    assert not first.artifact_scope_active
                    assert second.artifact_scope_active
                else:
                    assert not second.artifact_scope_active

        assert not store._pins
        assert first._pin_scope is not None and second._pin_scope is not None
        assert release_calls[id(first._pin_scope)] == 1
        assert release_calls[id(second._pin_scope)] == 1
        assert first.receipt is not None
        assert first.request is not None
        lowered = json.loads(first.request.body.decode("utf-8"))
        assert hashlib.sha256(first.request.body).hexdigest() == first.receipt.request_body_sha256
        context_matches = []
        for message in lowered["messages"]:
            wire_event_message = {
                "role": message["role"],
                "content": [{"type": "text", "text": message["content"]}],
            }
            canonical = json.dumps(
                wire_event_message, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            if hashlib.sha256(canonical).hexdigest() == first.receipt.context_message_sha256:
                context_matches.append(message)
        assert len(context_matches) == 1
        assert "def synthetic_target(value)" in context_matches[0]["content"]
        expected_materialized_event = _event()
        expected_materialized_event["messages"].insert(
            1,
            {
                "role": context_matches[0]["role"],
                "content": [{"type": "text", "text": context_matches[0]["content"]}],
            },
        )
        expected_projection = project_opencode_context_hook(expected_materialized_event)
        assert expected_projection.status is OpenCodeProjectionStatus.READY
        assert expected_projection.projection is not None
        assert gate_envelopes[0]["projection"] == expected_materialized_event
        assert materialized_events[0] == expected_materialized_event
        assert materialized_events[0] is not event
        envelope_bytes = composition_module._canonical(gate_envelopes[0])
        gate_receipt = gate_preparations[0].prompt_gate
        assert hashlib.sha256(envelope_bytes).hexdigest() == gate_receipt.prompt_sha256
        assert len(envelope_bytes) == gate_receipt.serialized_bytes
        context_message_count = sum(
            hashlib.sha256(composition_module._canonical(message)).hexdigest()
            == first.receipt.context_message_sha256
            for message in gate_envelopes[0]["projection"]["messages"]
        )
        assert context_message_count == 1
        assert (
            len(gate_preparations) == 2
            and len(gate_envelopes) == 2
            and len(materialized_events) == 2
        )
        assert (
            expected_projection.projection.projection_sha256
            == first.receipt.semantic_projection_sha256
        )
        assert lowered["messages"] == [
            {"role": message["role"], "content": message["content"][0]["text"]}
            for message in expected_materialized_event["messages"]
        ]
        assert first.receipt.insertion_receipt_sha256
        assert "return value + 1" not in repr(first.receipt)


def test_non_ready_preparation_never_issues_request_or_retains_pins():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="reject-", dir=TEST_TMP_ROOT) as scratch:
        result, store, boundary, _ = _prepare(
            Path(scratch), prompt_token_budget=1, lease_id="fixture-rejected-lease"
        )
        assert result.status is CompositionStatus.PREPARATION_REJECTED
        assert result.request is None
        assert result.ticket is None
        assert result.receipt is None
        assert not result.artifact_scope_active
        assert not store._pins
        assert not boundary._pending
        assert not boundary._active


def test_rule_route_identity_reaches_lowered_request_and_terminal_receipt():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    route_prompt = "Find the exact text 'synthetic_target' below ., capped at 10 matches."
    with tempfile.TemporaryDirectory(prefix="route-lease-", dir=TEST_TMP_ROOT) as scratch:
        result, store, boundary, fixture_response = _prepare(
            Path(scratch),
            route_prompt=route_prompt,
            lease_id="fixture-route-lease",
        )
        assert result.status is CompositionStatus.READY
        assert result.route_status == "completed"
        assert result.receipt is not None and result.receipt.route_preparation_sha256
        assert result.receipt.terminal_outcome is None
        assert verify_offline_e0_composition_receipt(result.receipt)
        assert result.request is not None and result.ticket is not None
        assert result.artifact_scope_active and sum(store._pins.values()) > 0
        lowered = json.loads(result.request.body.decode("utf-8"))
        assert hashlib.sha256(result.request.body).hexdigest() == result.receipt.request_body_sha256
        context_matches = []
        for message in lowered["messages"]:
            projected_message = {
                "role": message["role"],
                "content": [{"type": "text", "text": message["content"]}],
            }
            canonical_message = json.dumps(
                projected_message, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            if hashlib.sha256(canonical_message).hexdigest() == result.receipt.context_message_sha256:
                context_matches.append(message)
        assert len(context_matches) == 1

        stream = boundary.dispatch(result.request, fixture_response)
        assert isinstance(stream, composition_module.FixtureResponseStream)
        assert result.artifact_scope_active and sum(store._pins.values()) > 0
        assert list(stream) == [b"data: synthetic-fixture\n\n"]
        assert stream.end is StreamEnd.COMPLETE
        assert not result.artifact_scope_active and not store._pins

        terminal = finalize_offline_e0_request(result, stream)
        assert terminal is not None
        assert terminal.route_preparation_sha256 == result.receipt.route_preparation_sha256
        assert terminal.terminal_outcome == StreamEnd.COMPLETE.value
        assert verify_offline_e0_composition_receipt(terminal)
        assert "def synthetic_target" not in repr(terminal)
        assert "return value + 1" not in repr(terminal)


def test_route_abstention_and_stale_snapshot_issue_no_ticket_or_pins():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="route-abstain-", dir=TEST_TMP_ROOT) as scratch:
        result, store, boundary, _ = _prepare(
            Path(scratch), route_prompt="Summarize the repository.",
            lease_id="fixture-route-abstain",
        )
        assert result.status is CompositionStatus.ROUTE_REJECTED
        assert result.route_status == "abstain"
        assert result.request is None and result.ticket is None and result.receipt is None
        assert not result.artifact_scope_active and not store._pins
        assert not boundary._pending and not boundary._active

    original_route_prepare = composition_module.route_and_prepare_e0_context
    with tempfile.TemporaryDirectory(prefix="route-stale-", dir=TEST_TMP_ROOT) as scratch:
        root = Path(scratch)
        source_root, _, registry, store, boundary, response = _fixture(root)
        event = _event()

        def stale_before_route(*args, **kwargs):
            (source_root / "src" / "sample.py").write_text(
                """def synthetic_target(value):
    return value - 1
""",
                encoding="utf-8",
            )
            return original_route_prepare(*args, **kwargs)

        with patch.object(composition_module, "route_and_prepare_e0_context", stale_before_route):
            stale = prepare_offline_e0_request(
                registry,
                SESSION_ID,
                {"id": SESSION_ID, "location": {"directory": str(source_root)}},
                ("src/sample.py", "README.md"),
                event=event,
                fixture_response=response,
                store=store,
                boundary=boundary,
                namespace_registry=NamespaceRegistry(()),
                query="synthetic_target",
                route_prompt="Find the exact text 'synthetic_target' below ., capped at 10 matches.",
                lease_id="fixture-route-stale",
            )
        assert stale.status is CompositionStatus.ROUTE_REJECTED
        assert stale.route_status == "abstain"
        assert stale.request is None and stale.ticket is None and stale.receipt is None
        assert not stale.artifact_scope_active and not store._pins
        assert not boundary._pending and not boundary._active


def test_route_budget_rejection_releases_pins_before_request_ticket():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    route_prompt = "Find the exact text 'synthetic_target' below ., capped at 10 matches."
    with tempfile.TemporaryDirectory(prefix="route-budget-", dir=TEST_TMP_ROOT) as scratch:
        result, store, boundary, _ = _prepare(
            Path(scratch), route_prompt=route_prompt,
            context_token_budget=1, lease_id="fixture-route-budget",
        )
        assert result.status is CompositionStatus.PREPARATION_REJECTED
        assert result.route_status == "completed"
        assert result.request is None and result.ticket is None and result.receipt is None
        assert not result.artifact_scope_active and not store._pins
        assert not boundary._pending and not boundary._active


def test_terminal_cancel_and_failure_release_pins_once_and_finalize_receipt():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    route_prompt = "Find the exact text 'synthetic_target' below ., capped at 10 matches."
    for terminal_end in (StreamEnd.CANCELLED, StreamEnd.FAILED):
        with tempfile.TemporaryDirectory(prefix="route-terminal-", dir=TEST_TMP_ROOT) as scratch:
            release_calls: list[int] = []
            original_release = composition_module._PinScope.release_once

            def counted_release(scope):
                release_calls.append(id(scope))
                return original_release(scope)

            with patch.object(composition_module._PinScope, "release_once", counted_release):
                result, store, boundary, fixture_response = _prepare(
                    Path(scratch), route_prompt=route_prompt,
                    lease_id=f"fixture-route-{terminal_end.value}",
                )
                assert result.status is CompositionStatus.READY
                assert result.request is not None and result.receipt is not None
                assert result.ticket is not None and result.artifact_scope_active
                stream = boundary.dispatch(result.request, fixture_response)
                assert isinstance(stream, composition_module.FixtureResponseStream)
                assert result.artifact_scope_active and sum(store._pins.values()) > 0
                stream.close(terminal_end)
                assert stream.end is terminal_end
                assert not result.artifact_scope_active and not store._pins
                terminal = finalize_offline_e0_request(result, stream)
                assert terminal is not None
                assert terminal.terminal_outcome == terminal_end.value
                assert verify_offline_e0_composition_receipt(terminal)
            assert result._pin_scope is not None
            assert release_calls == [id(result._pin_scope)]


def test_invalid_fixture_response_fails_before_lease_creation():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="response-reject-", dir=TEST_TMP_ROOT) as scratch:
        result, store, boundary, _ = _prepare(
            Path(scratch), fixture_response=object(), lease_id="fixture-invalid-response"
        )
        assert result.status is CompositionStatus.PROJECT_REJECTED
        assert result.request is None and result.ticket is None
        assert not boundary._pending and not boundary._active
        assert not store._pins


def test_timer_start_failure_rolls_back_pending_lease_and_releases_once():
    released: list[str] = []
    boundary = RequestLeaseBoundary(
        nonce_factory=lambda: "synthetic-timer-start-failure-nonce",
        timeout_seconds=5,
    )
    try:
        with patch(
            "wrench_harness.opencode_request_boundary.threading.Timer.start",
            side_effect=RuntimeError("synthetic timer start failure"),
        ):
            boundary.prepare("synthetic-timer-start-failure", lambda: released.append("released"))
    except RuntimeError as exc:
        assert "synthetic timer start failure" in str(exc)
    else:
        raise AssertionError("timer start failure was not propagated")

    assert released == ["released"]
    assert not boundary._pending
    assert not boundary._active
    assert "synthetic-timer-start-failure-nonce" in boundary._used_nonces
    assert boundary.expire() == 0
    assert released == ["released"]


def test_boundary_rejection_consumes_lease_and_runs_release_once():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="boundary-reject-", dir=TEST_TMP_ROOT) as scratch:
        release_calls: dict[int, int] = {}
        original_release = composition_module._PinScope.release_once

        def counted_release(scope):
            key = id(scope)
            release_calls[key] = release_calls.get(key, 0) + 1
            return original_release(scope)

        with patch.object(composition_module._PinScope, "release_once", counted_release):
            result, store, boundary, fixture = _prepare(
                Path(scratch), lease_id="fixture-boundary-reject"
            )
        assert result.status is CompositionStatus.READY
        assert result.request is not None and result.ticket is not None
        assert result.artifact_scope_active
        rejected = replace(result.request, body=b"{}")

        with LoopbackFixtureServer(boundary, fixture) as server:
            connection = http.client.HTTPConnection(*server.address, timeout=3)
            connection.request(
                rejected.method,
                rejected.url,
                body=rejected.body,
                headers=dict(rejected.headers),
            )
            response = connection.getresponse()
            assert response.status == 400
            response.read()
            connection.close()

        assert not result.artifact_scope_active
        assert not store._pins
        assert not boundary._pending and not boundary._active
        assert result._pin_scope is not None
        assert release_calls[id(result._pin_scope)] == 1


def test_materialization_and_lowering_failures_leave_no_lease_or_pins():
    for patched_name in (
        "materialize_opencode_prepared_context",
        "_lower_materialized_event",
    ):
        TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="prelease-fail-", dir=TEST_TMP_ROOT) as scratch:
            with patch(
                f"wrench_harness.e0_offline_request_composition.{patched_name}",
                side_effect=RuntimeError("synthetic failure"),
            ):
                result, store, boundary, _ = _prepare(
                    Path(scratch), lease_id=f"fixture-{patched_name}"
                )
            assert result.status is CompositionStatus.LOWERING_REJECTED
            assert result.request is None and result.ticket is None
            assert not result.artifact_scope_active
            assert not boundary._pending and not boundary._active
            assert not store._pins


def test_active_timeout_keeps_composition_pins_until_writer_cleanup():
    TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    fixture = FixtureResponse((b"z" * 16_384,) * 64)
    with tempfile.TemporaryDirectory(prefix="timeout-", dir=TEST_TMP_ROOT) as scratch:
        result, store, boundary, _ = _prepare(
            Path(scratch),
            fixture_response=fixture,
            timeout_seconds=0.5,
            lease_id="fixture-active-timeout",
        )
        assert result.status is CompositionStatus.READY
        assert result.request is not None and result.ticket is not None
        assert result.artifact_scope_active

        with LoopbackFixtureServer(boundary, fixture) as server:
            sock = socket.create_connection(server.address, timeout=3)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
            request = result.request
            header_lines = [
                f"{request.method} {request.url} HTTP/1.1",
                f"Host: 127.0.0.1:{server.address[1]}",
                *(f"{name}: {value}" for name, value in request.headers),
                f"Content-Length: {len(request.body)}",
                "Connection: close",
                "",
                "",
            ]
            sock.sendall("\r\n".join(header_lines).encode("ascii") + request.body)
            response_headers = bytearray()
            while b"\r\n\r\n" not in response_headers:
                part = sock.recv(1)
                assert part
                response_headers.extend(part)
                assert len(response_headers) < 16_384
            assert response_headers.startswith(b"HTTP/1.0 200") or response_headers.startswith(b"HTTP/1.1 200")

            deadline = time.monotonic() + 3
            active_lease = None
            while time.monotonic() < deadline:
                active_lease = boundary._active.get(result.ticket.nonce)
                if active_lease is not None and active_lease.timeout_requested:
                    break
                time.sleep(0.01)
            assert active_lease is not None and active_lease.timeout_requested
            assert result.artifact_scope_active
            assert sum(store._pins.values()) > 0

            sock.close()
            deadline = time.monotonic() + 3
            while result.artifact_scope_active and time.monotonic() < deadline:
                time.sleep(0.01)
            assert not result.artifact_scope_active
            assert not store._pins
            assert result.ticket.nonce not in boundary._active
