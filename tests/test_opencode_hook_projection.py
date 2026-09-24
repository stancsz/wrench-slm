import copy
import hashlib
import json
import asyncio
from dataclasses import replace

import pytest

from wrench_harness.opencode_hook_projection import (
    CONTEXT_HOOK_OBSERVATION_SCHEMA,
    MAX_HOOK_MESSAGES,
    MAX_OPENCODE_CONTEXT_HOOK_BYTES,
    MAX_OPENCODE_CONTEXT_HOOK_OBSERVATION_CALLS,
    OpenCodeContextHookObserver,
    OpenCodePreparedTransitionStatus,
    OPENCODE_CONTEXT_HOOK_VERSION,
    PROJECTION_SCHEMA,
    OpenCodeProjectionStatus,
    OpenCodeTransitionStatus,
    _bounded_canonical_json,
    _prepared_transition_receipt_payload,
    project_opencode_context_hook,
    validate_opencode_context_hook_transition,
    validate_opencode_preparation_context_transition,
    verify_opencode_prepared_transition_receipt,
)
from wrench_harness import opencode_hook_projection as hook_projection
from wrench_harness.e0_context_pipeline import PreparationResult, PreparationStatus
from wrench_harness.prompt_compiler import PromptGateReceipt, PromptGateStatus


class _FakeMonotonicClock:
    def __init__(self, *values):
        self._values = iter(values)

    def __call__(self):
        value = next(self._values)
        if isinstance(value, BaseException):
            raise value
        return value


def test_hook_observer_has_no_observation_before_any_callback_invocation():
    observer = OpenCodeContextHookObserver(lambda: None, monotonic_ns=lambda: 10)

    assert observer.observation is None


def test_hook_observer_public_api_is_exported():
    assert {
        "CONTEXT_HOOK_OBSERVATION_SCHEMA",
        "MAX_OPENCODE_CONTEXT_HOOK_OBSERVATION_CALLS",
        "OpenCodeContextHookCall",
        "OpenCodeContextHookObservation",
        "OpenCodeContextHookObserver",
    }.issubset(set(hook_projection.__all__))


def test_hook_observer_measures_returned_callback_once_and_repeatedly():
    calls = []

    def callback(value):
        calls.append(value)
        return "callback-result"

    observer = OpenCodeContextHookObserver(
        callback, monotonic_ns=_FakeMonotonicClock(10, 15, 20, 32)
    )

    assert observer.observation is None
    assert asyncio.run(observer("first")) == "callback-result"
    assert asyncio.run(observer("second")) == "callback-result"

    observation = observer.observation
    assert calls == ["first", "second"]
    assert observation is not None
    assert observation.schema == CONTEXT_HOOK_OBSERVATION_SCHEMA
    assert observation.opencode_context_hook_version == OPENCODE_CONTEXT_HOOK_VERSION
    assert observation.invocation_count == 2
    assert observation.completed_count == 2
    assert observation.returned_count == 2
    assert observation.error_count == 0
    assert observation.elapsed_ns == 17
    assert [(row.invocation_index, row.elapsed_ns, row.result) for row in observation.calls] == [
        (1, 5, "returned"), (2, 12, "returned")
    ]
    assert not observation.calls_capped
    assert not observation.saturated


def test_hook_observer_records_sync_error_without_exception_content():
    def callback():
        raise RuntimeError("secret callback text")

    observer = OpenCodeContextHookObserver(
        callback, monotonic_ns=_FakeMonotonicClock(100, 107)
    )

    with pytest.raises(RuntimeError, match="secret callback text"):
        asyncio.run(observer())

    observation = observer.observation
    assert observation is not None
    assert observation.invocation_count == observation.completed_count == 1
    assert observation.returned_count == 0
    assert observation.error_count == 1
    assert observation.elapsed_ns == 7
    assert observation.calls[0].result == "error"
    assert not hasattr(observation.calls[0], "exception")
    assert "secret callback text" not in repr(observation)


def test_hook_observer_records_async_rejection_and_rethrows_original_error():
    error = ValueError("secret rejection text")

    async def callback():
        raise error

    observer = OpenCodeContextHookObserver(
        callback, monotonic_ns=_FakeMonotonicClock(200, 211)
    )

    with pytest.raises(ValueError) as raised:
        asyncio.run(observer())

    assert raised.value is error
    observation = observer.observation
    assert observation is not None
    assert observation.invocation_count == observation.completed_count == 1
    assert observation.returned_count == 0
    assert observation.error_count == 1
    assert observation.elapsed_ns == 11
    assert observation.calls[0].result == "error"
    assert "secret rejection text" not in repr(observation)


def test_hook_observer_caps_ordered_per_call_rows_without_storing_content():
    clock_values = []
    for index in range(MAX_OPENCODE_CONTEXT_HOOK_OBSERVATION_CALLS + 1):
        clock_values.extend((index * 10, index * 10 + 2))
    observer = OpenCodeContextHookObserver(
        lambda secret: None, monotonic_ns=_FakeMonotonicClock(*clock_values)
    )

    for index in range(MAX_OPENCODE_CONTEXT_HOOK_OBSERVATION_CALLS + 1):
        asyncio.run(observer(f"private-{index}"))

    observation = observer.observation
    assert observation is not None
    assert observation.invocation_count == MAX_OPENCODE_CONTEXT_HOOK_OBSERVATION_CALLS + 1
    assert len(observation.calls) == MAX_OPENCODE_CONTEXT_HOOK_OBSERVATION_CALLS
    assert [row.invocation_index for row in observation.calls] == list(
        range(1, MAX_OPENCODE_CONTEXT_HOOK_OBSERVATION_CALLS + 1)
    )
    assert observation.calls_capped
    assert "private-" not in repr(observation)


def test_hook_observer_clamps_large_per_call_elapsed_value():
    observer = OpenCodeContextHookObserver(
        lambda: None, monotonic_ns=_FakeMonotonicClock(0, 1 << 63)
    )

    asyncio.run(observer())

    observation = observer.observation
    assert observation is not None
    assert observation.elapsed_ns == (1 << 63) - 1
    assert observation.calls[0].elapsed_ns == (1 << 63) - 1
    assert observation.saturated


def test_hook_observer_saturates_aggregate_when_bounded_rows_overflow_sum():
    maximum = (1 << 63) - 1
    observer = OpenCodeContextHookObserver(
        lambda: None,
        monotonic_ns=_FakeMonotonicClock(0, maximum, maximum, maximum + 1),
    )

    asyncio.run(observer())
    asyncio.run(observer())

    observation = observer.observation
    assert observation is not None
    assert [row.elapsed_ns for row in observation.calls] == [maximum, 1]
    assert observation.elapsed_ns == maximum
    assert observation.saturated


def test_hook_observer_calls_callback_when_start_clock_raises():
    calls = []
    observer = OpenCodeContextHookObserver(
        lambda: calls.append("called") or "returned",
        monotonic_ns=_FakeMonotonicClock(RuntimeError("private clock failure")),
    )

    assert asyncio.run(observer()) == "returned"

    observation = observer.observation
    assert calls == ["called"]
    assert observation is not None
    assert observation.returned_count == 1
    assert observation.timing_error_count == 1
    assert observation.elapsed_ns == 0
    assert observation.calls[0].elapsed_ns is None
    assert "private clock failure" not in repr(observation)


def test_hook_observer_end_clock_failure_does_not_replace_callback_return():
    observer = OpenCodeContextHookObserver(
        lambda: "returned",
        monotonic_ns=_FakeMonotonicClock(10, RuntimeError("private clock failure")),
    )

    assert asyncio.run(observer()) == "returned"

    observation = observer.observation
    assert observation is not None
    assert observation.returned_count == 1
    assert observation.timing_error_count == 1
    assert observation.calls[0].elapsed_ns is None
    assert "private clock failure" not in repr(observation)


def test_hook_observer_end_clock_failure_preserves_original_callback_error():
    callback_error = ValueError("callback failure")

    def callback():
        raise callback_error

    observer = OpenCodeContextHookObserver(
        callback,
        monotonic_ns=_FakeMonotonicClock(20, RuntimeError("private clock failure")),
    )

    with pytest.raises(ValueError) as raised:
        asyncio.run(observer())

    assert raised.value is callback_error
    observation = observer.observation
    assert observation is not None
    assert observation.error_count == 1
    assert observation.timing_error_count == 1
    assert observation.calls[0].elapsed_ns is None
    assert "private clock failure" not in repr(observation)


def test_hook_observer_treats_non_integer_clock_sample_as_unavailable():
    observer = OpenCodeContextHookObserver(
        lambda: "returned", monotonic_ns=_FakeMonotonicClock(1.5)
    )

    assert asyncio.run(observer()) == "returned"

    observation = observer.observation
    assert observation is not None
    assert observation.timing_error_count == 1
    assert observation.calls[0].elapsed_ns is None


def _hook_event():
    return {
        "sessionID": "ses_projection123",
        "model": {
            "id": "gpt-4.1-2025-04-14",
            "providerID": "openai",
            "variant": "low-latency",
        },
        "system": [{"type": "text", "text": "Follow repository instructions."}, {"type": "text", "text": "Keep tools unchanged."}],
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "Find the project entry point."}]},
            {"role": "assistant", "content": [{"type": "text", "text": "I will inspect the tree."}]},
        ],
        "options": {
            "temperature": 0,
            "providerOptions": {"openai": {"reasoningEffort": "low", "vendorFlag": True}},
        },
        "agent": "build",
        "tools": {
            "z_read": {
                "description": "Read a file",
                "input": {"type": "object", "properties": {"path": {"type": "string"}}},
            },
            "a_search": {
                "description": "Search source",
                "input": True,
            },
        },
    }


def _text_message(text):
    return {"role": "user", "content": [{"type": "text", "text": text}]}


def _prepared_context(message, position):
    gate = PromptGateReceipt(
        status=PromptGateStatus.READY,
        session_hash="a" * 64,
        selected_evidence_ids=("evidence-1",),
        omitted_evidence=(),
        required_evidence_reasons=(),
        prompt_sha256="b" * 64,
        exact_token_count=10,
        hard_budget=100,
        tokenizer_id="tokenizer-v1",
        serializer_id="serializer-v1",
        serialized_bytes=64,
        context_message_sha256=hashlib.sha256(
            _bounded_canonical_json(message, MAX_OPENCODE_CONTEXT_HOOK_BYTES)
        ).hexdigest(),
        context_insertion_position=position,
    )
    preparation = PreparationResult(
        status=PreparationStatus.READY,
        route="context",
        prompt="prepared prompt",
        prompt_gate=gate,
        outcome_receipt=None,
        aggregate_sha256="c" * 64,
        sources=(),
        selected_evidence_ids=("evidence-1",),
        omitted_evidence=(),
        retrieval_misses=(),
        schema_digests=(),
        structural_status="ready",
    )
    return preparation, gate


def test_projection_preserves_every_context_field_and_tool_order():
    event = _hook_event()
    original = copy.deepcopy(event)

    result = project_opencode_context_hook(event)

    assert result.status is OpenCodeProjectionStatus.READY
    assert result.projection is not None
    projection = result.projection
    copied = json.loads(projection.payload_json)
    assert copied == original
    assert list(copied["tools"]) == ["z_read", "a_search"]
    assert list(copied) == list(original)
    assert projection.session_id == event["sessionID"]
    assert projection.agent_id == event["agent"]
    assert projection.provider_id == event["model"]["providerID"]
    assert projection.model_id == event["model"]["id"]
    assert projection.model_variant == event["model"]["variant"]
    assert projection.projection_schema == PROJECTION_SCHEMA
    assert projection.opencode_context_hook_version == OPENCODE_CONTEXT_HOOK_VERSION
    assert projection.serialized_bytes == len(projection.payload_json.encode("utf-8"))
    assert len(projection.projection_sha256) == 64
    canonical = _bounded_canonical_json(
        {
            "schema": PROJECTION_SCHEMA,
            "opencode_context_hook_version": OPENCODE_CONTEXT_HOOK_VERSION,
            "payload": original,
        },
        MAX_OPENCODE_CONTEXT_HOOK_BYTES,
    )
    assert projection.projection_sha256 == hashlib.sha256(canonical).hexdigest()
    assert event == original


def test_projection_hash_is_canonical_across_mapping_order_but_payload_order_is_preserved():
    first = _hook_event()
    reordered = dict(reversed(list(first.items())))
    reordered["options"] = dict(reversed(list(reordered["options"].items())))

    first_projection = project_opencode_context_hook(first).projection
    reordered_projection = project_opencode_context_hook(reordered).projection

    assert first_projection is not None
    assert reordered_projection is not None
    assert first_projection.projection_sha256 == reordered_projection.projection_sha256
    assert list(json.loads(first_projection.payload_json)) == list(first)
    assert list(json.loads(reordered_projection.payload_json)) == list(reordered)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("system", ["scalar system part"]),
        ("system", [{"type": "image", "text": "not a system text part"}]),
        ("messages", [{"role": "user", "content": "scalar message content"}]),
        ("messages", [{"role": "unknown", "content": []}]),
    ],
)
def test_projection_rejects_noncanonical_hook_message_shapes(field, value):
    event = _hook_event()
    event[field] = value

    result = project_opencode_context_hook(event)

    assert result.status is OpenCodeProjectionStatus.INVALID_SHAPE
    assert result.projection is None


@pytest.mark.parametrize(
    ("field", "change"),
    [
        ("sessionID", lambda event: event.update(sessionID="ses_other123")),
        ("agent", lambda event: event.update(agent="review")),
        ("model", lambda event: event["model"].update(id="other-model")),
        ("system", lambda event: event["system"].append({"type": "text", "text": "Another system instruction."})),
        ("messages", lambda event: event["messages"].append(_text_message("Next"))),
        ("options", lambda event: event["options"].update(providerOnlyOption="retained")),
        ("tools", lambda event: event["tools"]["z_read"].update(description="Changed")),
    ],
)
def test_every_context_field_changes_projection_identity(field, change):
    original = project_opencode_context_hook(_hook_event()).projection
    altered_event = _hook_event()
    change(altered_event)

    altered = project_opencode_context_hook(altered_event).projection

    assert original is not None
    assert altered is not None
    assert altered.projection_sha256 != original.projection_sha256, field


def test_transition_accepts_exact_single_context_message_insertion():
    before_event = _hook_event()
    after_event = copy.deepcopy(before_event)
    expected = _text_message("Prepared repository context.")
    position = 1
    after_event["messages"].insert(position, copy.deepcopy(expected))
    before = project_opencode_context_hook(before_event).projection
    after = project_opencode_context_hook(after_event).projection

    result = validate_opencode_context_hook_transition(
        before, after, expected_message=expected, insertion_position=position
    )

    assert result.status is OpenCodeTransitionStatus.READY
    assert result.reason == "ready"
    assert result.receipt is not None
    assert result.receipt.session_id == before_event["sessionID"]
    assert result.receipt.insertion_position == position
    assert result.receipt.before_projection_sha256 == before.projection_sha256
    assert result.receipt.after_projection_sha256 == after.projection_sha256
    assert len(result.receipt.inserted_message_sha256) == 64
    assert not hasattr(result.receipt, "content")


@pytest.mark.parametrize(
    ("field", "change", "expected_status"),
    [
        ("sessionID", lambda event: event.update(sessionID="ses_other123"), OpenCodeTransitionStatus.SESSION_MISMATCH),
        ("agent", lambda event: event.update(agent="review"), OpenCodeTransitionStatus.PROTECTED_CONTEXT_CHANGED),
        ("model", lambda event: event["model"].update(id="other-model"), OpenCodeTransitionStatus.PROTECTED_CONTEXT_CHANGED),
        ("system", lambda event: event["system"].append({"type": "text", "text": "Changed"}), OpenCodeTransitionStatus.PROTECTED_CONTEXT_CHANGED),
        ("tools", lambda event: event["tools"].pop("a_search"), OpenCodeTransitionStatus.PROTECTED_CONTEXT_CHANGED),
        ("options", lambda event: event["options"].update(extra=True), OpenCodeTransitionStatus.PROTECTED_CONTEXT_CHANGED),
    ],
)
def test_transition_rejects_changed_protected_context(field, change, expected_status):
    before_event = _hook_event()
    after_event = copy.deepcopy(before_event)
    after_event["messages"].insert(0, _text_message("Prepared."))
    change(after_event)

    result = validate_opencode_context_hook_transition(
        project_opencode_context_hook(before_event).projection,
        project_opencode_context_hook(after_event).projection,
        expected_message=_text_message("Prepared."),
        insertion_position=0,
    )

    assert result.status is expected_status, field
    assert result.receipt is None


@pytest.mark.parametrize(
    "change_messages",
    [
        lambda messages: messages.__setitem__(0, _text_message("Changed")),
        lambda messages: messages.reverse(),
        lambda messages: messages.__setitem__(1, _text_message("Wrong insertion")),
    ],
)
def test_transition_rejects_changed_reordered_or_wrong_inserted_messages(change_messages):
    before_event = _hook_event()
    after_event = copy.deepcopy(before_event)
    expected = _text_message("Prepared.")
    after_event["messages"].insert(1, copy.deepcopy(expected))
    change_messages(after_event["messages"])

    result = validate_opencode_context_hook_transition(
        project_opencode_context_hook(before_event).projection,
        project_opencode_context_hook(after_event).projection,
        expected_message=expected,
        insertion_position=1,
    )

    assert result.status is OpenCodeTransitionStatus.MESSAGE_SEQUENCE_MISMATCH
    assert result.receipt is None


@pytest.mark.parametrize(
    ("expected_message", "insertion_position"),
    [
        (_text_message("Prepared."), True),
        (_text_message("Prepared."), -1),
        (_text_message("Prepared."), 3),
        ({"role": "user", "content": "scalar content is not a hook Message"}, 0),
        (["not", "an", "object"], 0),
    ],
)
def test_transition_rejects_invalid_message_or_position(expected_message, insertion_position):
    before_event = _hook_event()
    after_event = copy.deepcopy(before_event)
    expected = _text_message("Prepared.")
    after_event["messages"].insert(0, expected)

    result = validate_opencode_context_hook_transition(
        project_opencode_context_hook(before_event).projection,
        project_opencode_context_hook(after_event).projection,
        expected_message=expected_message,
        insertion_position=insertion_position,
    )

    assert result.status is OpenCodeTransitionStatus.INSERTION_POSITION_INVALID
    assert result.receipt is None


def test_transition_rejects_forged_or_malformed_projection():
    before = project_opencode_context_hook(_hook_event()).projection
    after_event = _hook_event()
    after_event["messages"].append(_text_message("Prepared."))
    after = project_opencode_context_hook(after_event).projection
    assert before is not None and after is not None
    forged = replace(before, projection_sha256="0" * 64)

    result = validate_opencode_context_hook_transition(
        forged,
        after,
        expected_message=_text_message("Prepared."),
        insertion_position=2,
    )

    assert result.status is OpenCodeTransitionStatus.INVALID_PROJECTION
    assert result.receipt is None


def test_prepared_transition_binds_ready_preparation_gate_and_hook_insertion():
    before_event = _hook_event()
    expected = _text_message("Prepared repository context.")
    position = 1
    after_event = copy.deepcopy(before_event)
    after_event["messages"].insert(position, copy.deepcopy(expected))
    preparation, _gate = _prepared_context(expected, position)

    result = validate_opencode_preparation_context_transition(
        preparation,
        project_opencode_context_hook(before_event).projection,
        project_opencode_context_hook(after_event).projection,
        expected_message=expected,
    )

    assert result.status is OpenCodePreparedTransitionStatus.READY
    assert result.reason == "ready"
    assert result.receipt is not None
    assert result.receipt.preparation_sha256 == preparation.aggregate_sha256
    assert result.receipt.transition.insertion_position == position
    assert len(result.receipt.receipt_sha256) == 64
    assert verify_opencode_prepared_transition_receipt(result.receipt)
    assert not hasattr(result.receipt, "content")


def test_prepared_transition_rejects_expected_message_that_differs_from_gate_binding():
    expected = _text_message("Prepared repository context.")
    preparation, _gate = _prepared_context(expected, 0)

    result = validate_opencode_preparation_context_transition(
        preparation,
        project_opencode_context_hook(_hook_event()).projection,
        project_opencode_context_hook(_hook_event()).projection,
        expected_message=_text_message("different"),
    )

    assert result.status is OpenCodePreparedTransitionStatus.INSERTION_BINDING_MISMATCH
    assert result.receipt is None


def test_prepared_transition_rejects_gate_position_that_does_not_match_inserted_message():
    before_event = _hook_event()
    expected = _text_message("Prepared repository context.")
    actual_position = 1
    after_event = copy.deepcopy(before_event)
    after_event["messages"].insert(actual_position, copy.deepcopy(expected))
    preparation, _gate = _prepared_context(expected, 0)

    result = validate_opencode_preparation_context_transition(
        preparation,
        project_opencode_context_hook(before_event).projection,
        project_opencode_context_hook(after_event).projection,
        expected_message=expected,
    )

    assert result.status is OpenCodePreparedTransitionStatus.TRANSITION_REJECTED
    assert result.reason == "transition_message_sequence_mismatch"
    assert result.receipt is None


@pytest.mark.parametrize("case", ["no_binding", "non_ready_preparation", "bool_position"])
def test_prepared_transition_rejects_missing_or_invalid_preparation_binding(case):
    expected = _text_message("Prepared repository context.")
    position = 0
    preparation, _gate = _prepared_context(expected, position)
    if case == "no_binding":
        preparation = replace(
            preparation,
            prompt_gate=replace(
                preparation.prompt_gate,
                context_message_sha256=None,
                context_insertion_position=None,
            ),
        )
        expected_status = OpenCodePreparedTransitionStatus.INSERTION_BINDING_MISSING
    elif case == "non_ready_preparation":
        preparation = replace(preparation, status=PreparationStatus.CONTEXT_FAILED)
        expected_status = OpenCodePreparedTransitionStatus.INVALID_PREPARATION
    else:
        preparation = replace(
            preparation,
            prompt_gate=replace(preparation.prompt_gate, context_insertion_position=True),
        )
        expected_status = OpenCodePreparedTransitionStatus.INSERTION_BINDING_INVALID

    result = validate_opencode_preparation_context_transition(
        preparation,
        project_opencode_context_hook(_hook_event()).projection,
        project_opencode_context_hook(_hook_event()).projection,
        expected_message=expected,
    )

    assert result.status is expected_status
    assert result.receipt is None


def test_prepared_transition_receipt_verifier_rejects_tampering():
    before_event = _hook_event()
    expected = _text_message("Prepared repository context.")
    after_event = copy.deepcopy(before_event)
    after_event["messages"].insert(0, copy.deepcopy(expected))
    preparation, _gate = _prepared_context(expected, 0)
    result = validate_opencode_preparation_context_transition(
        preparation,
        project_opencode_context_hook(before_event).projection,
        project_opencode_context_hook(after_event).projection,
        expected_message=expected,
    )
    assert result.receipt is not None

    tampered = replace(result.receipt, preparation_sha256="d" * 64)

    assert not verify_opencode_prepared_transition_receipt(tampered)


def test_prepared_transition_receipt_verifier_rejects_position_beyond_hook_limit():
    before_event = _hook_event()
    expected = _text_message("Prepared repository context.")
    after_event = copy.deepcopy(before_event)
    after_event["messages"].insert(0, copy.deepcopy(expected))
    preparation, _gate = _prepared_context(expected, 0)
    result = validate_opencode_preparation_context_transition(
        preparation,
        project_opencode_context_hook(before_event).projection,
        project_opencode_context_hook(after_event).projection,
        expected_message=expected,
    )
    assert result.receipt is not None

    impossible_transition = replace(
        result.receipt.transition,
        insertion_position=MAX_HOOK_MESSAGES,
    )
    payload = _prepared_transition_receipt_payload(
        result.receipt.preparation_sha256,
        impossible_transition,
    )
    canonical = _bounded_canonical_json(payload, 4096)
    impossible = replace(
        result.receipt,
        transition=impossible_transition,
        receipt_sha256=hashlib.sha256(canonical).hexdigest(),
    )

    assert not verify_opencode_prepared_transition_receipt(impossible)


@pytest.mark.parametrize(
    "missing_field",
    ["sessionID", "agent", "model", "system", "messages", "tools", "options"],
)
def test_projection_rejects_missing_context_fields(missing_field):
    event = _hook_event()
    del event[missing_field]

    result = project_opencode_context_hook(event)

    assert result.status is OpenCodeProjectionStatus.INVALID_FIELDS
    assert result.projection is None


def test_projection_rejects_unknown_fields_and_invalid_model_shape():
    extra_field = _hook_event()
    extra_field["requestKind"] = "primary"
    bad_model = _hook_event()
    bad_model["model"]["unexpected"] = "ignored-by-old-client"

    assert project_opencode_context_hook(extra_field).status is OpenCodeProjectionStatus.INVALID_FIELDS
    assert project_opencode_context_hook(bad_model).status is OpenCodeProjectionStatus.INVALID_SHAPE


def test_projection_accepts_missing_optional_model_variant():
    event = _hook_event()
    del event["model"]["variant"]

    result = project_opencode_context_hook(event)

    assert result.status is OpenCodeProjectionStatus.READY
    assert result.projection.model_variant is None


def test_projection_rejects_explicit_null_model_variant():
    event = _hook_event()
    event["model"]["variant"] = None

    result = project_opencode_context_hook(event)

    assert result.status is OpenCodeProjectionStatus.INVALID_SHAPE
    assert result.projection is None


@pytest.mark.parametrize("invalid_case", ["oversized", "cycle", "non_json"])
def test_projection_rejects_unbounded_or_non_json_input(invalid_case):
    event = _hook_event()
    if invalid_case == "oversized":
        event["system"][0] = "x" * (MAX_OPENCODE_CONTEXT_HOOK_BYTES + 1)
        expected = OpenCodeProjectionStatus.INPUT_LIMIT_EXCEEDED
    elif invalid_case == "cycle":
        loop = []
        loop.append(loop)
        event["options"]["cycle"] = loop
        expected = OpenCodeProjectionStatus.INVALID_SHAPE
    else:
        event["options"]["unsupported"] = object()
        expected = OpenCodeProjectionStatus.INVALID_SHAPE

    result = project_opencode_context_hook(event)

    assert result.status is expected
    assert result.projection is None
