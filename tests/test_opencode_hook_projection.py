import copy
import json

import pytest

from wrench_harness.opencode_hook_projection import (
    MAX_OPENCODE_CONTEXT_HOOK_BYTES,
    OPENCODE_CONTEXT_HOOK_VERSION,
    PROJECTION_SCHEMA,
    OpenCodeProjectionStatus,
    project_opencode_context_hook,
)


def _hook_event():
    return {
        "sessionID": "ses_projection123",
        "model": {
            "id": "gpt-4.1-2025-04-14",
            "providerID": "openai",
            "variant": "low-latency",
        },
        "system": ["Follow repository instructions.", {"type": "text", "text": "Keep tools unchanged."}],
        "messages": [
            {"role": "user", "content": "Find the project entry point."},
            {"role": "assistant", "content": "I will inspect the tree."},
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
    assert event == original


@pytest.mark.parametrize(
    ("field", "change"),
    [
        ("sessionID", lambda event: event.update(sessionID="ses_other123")),
        ("agent", lambda event: event.update(agent="review")),
        ("model", lambda event: event["model"].update(id="other-model")),
        ("system", lambda event: event["system"].append("Another system instruction.")),
        ("messages", lambda event: event["messages"].append({"role": "user", "content": "Next"})),
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
