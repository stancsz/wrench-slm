from __future__ import annotations

import pytest

from wrench_harness.execution_state import (
    PATCH_SCHEMA,
    ExecutionStateError,
    StateFieldSpec,
    apply_state_patch,
    new_execution_state,
)


TASK_SHA256 = "a" * 64
OBSERVATION_SHA256 = "b" * 64
TEST_SHA256 = "c" * 64
EVIDENCE = {"obs-1": OBSERVATION_SHA256, "test-1": TEST_SHA256}
FIELDS = {
    "task_summary": StateFieldSpec("string", required=True, max_chars=256),
    "changed_files": StateFieldSpec("string_list", max_chars=128, max_items=8),
    "test_count": StateFieldSpec("integer"),
    "verified": StateFieldSpec("boolean"),
}


def set_change(field: str, value: object, *evidence_ids: str) -> dict[str, object]:
    return {
        "op": "set",
        "field": field,
        "value": value,
        "evidence_ids": list(evidence_ids),
    }


def patch(*changes: dict[str, object], session_id: str = "session-1", revision: int = 0):
    return {
        "schema": PATCH_SCHEMA,
        "session_id": session_id,
        "base_revision": revision,
        "changes": list(changes),
    }


def assert_code(code: str, call) -> None:
    with pytest.raises(ExecutionStateError) as exc_info:
        call()
    assert exc_info.value.code == code


def test_patch_creates_new_revision_with_exact_evidence_hashes():
    initial = new_execution_state("session-1", TASK_SHA256)

    result = apply_state_patch(
        initial,
        patch(
            set_change("task_summary", "Investigate parser failure", "obs-1"),
            set_change("changed_files", ["src/parser.py"], "obs-1", "test-1"),
        ),
        field_specs=FIELDS,
        evidence_hashes=EVIDENCE,
    )

    assert result.state.revision == 1
    assert result.changed_fields == ("changed_files", "task_summary")
    assert result.state.facts["task_summary"].value == "Investigate parser failure"
    assert result.state.facts["changed_files"].value == ("src/parser.py",)
    assert result.state.facts["changed_files"].evidence[0].sha256 == OBSERVATION_SHA256
    assert len(result.state.sha256) == 64
    assert len(result.patch_sha256) == 64
    assert initial.revision == 0
    assert initial.facts == {}


def test_state_and_facts_are_immutable():
    result = apply_state_patch(
        new_execution_state("session-1", TASK_SHA256),
        patch(set_change("task_summary", "Known issue", "obs-1")),
        field_specs=FIELDS,
        evidence_hashes=EVIDENCE,
    )

    with pytest.raises(TypeError):
        result.state.facts["other"] = result.state.facts["task_summary"]


def test_stale_patch_is_rejected_without_mutating_current_state():
    initial = new_execution_state("session-1", TASK_SHA256)
    first = apply_state_patch(
        initial,
        patch(set_change("task_summary", "Known issue", "obs-1")),
        field_specs=FIELDS,
        evidence_hashes=EVIDENCE,
    )

    assert_code(
        "state_patch_stale",
        lambda: apply_state_patch(
            first.state,
            patch(set_change("verified", True, "test-1")),
            field_specs=FIELDS,
            evidence_hashes=EVIDENCE,
        ),
    )
    assert first.state.revision == 1
    assert "verified" not in first.state.facts


def test_patch_must_match_session_and_task_fields_are_not_authority():
    initial = new_execution_state("session-1", TASK_SHA256)

    assert_code(
        "state_patch_session_mismatch",
        lambda: apply_state_patch(
            initial,
            patch(set_change("task_summary", "Known issue", "obs-1"), session_id="other"),
            field_specs=FIELDS,
            evidence_hashes=EVIDENCE,
        ),
    )
    assert_code(
        "state_field_schema_invalid",
        lambda: apply_state_patch(
            initial,
            patch(set_change("tool_permissions", ["run_tests"], "obs-1")),
            field_specs={"tool_permissions": StateFieldSpec("string_list")},
            evidence_hashes=EVIDENCE,
        ),
    )
    assert_code(
        "state_field_schema_invalid",
        lambda: apply_state_patch(
            new_execution_state("session-1", TASK_SHA256),
            patch(set_change("permissions", "restricted", "obs-1")),
            field_specs={"permissions": StateFieldSpec("string")},
            evidence_hashes=EVIDENCE,
        ),
    )


def test_patch_requires_current_evidence_manifest_entries():
    initial = new_execution_state("session-1", TASK_SHA256)

    assert_code(
        "state_patch_evidence_missing",
        lambda: apply_state_patch(
            initial,
            patch(set_change("task_summary", "Known issue", "missing-1")),
            field_specs=FIELDS,
            evidence_hashes=EVIDENCE,
        ),
    )
    assert_code(
        "state_evidence_manifest_invalid",
        lambda: apply_state_patch(
            initial,
            patch(set_change("task_summary", "Known issue", "obs-1")),
            field_specs=FIELDS,
            evidence_hashes={"obs-1": "not-a-hash"},
        ),
    )


def test_existing_state_evidence_must_still_match_the_current_manifest():
    initial = new_execution_state("session-1", TASK_SHA256)
    first = apply_state_patch(
        initial,
        patch(set_change("task_summary", "Known issue", "obs-1")),
        field_specs=FIELDS,
        evidence_hashes=EVIDENCE,
    )

    assert_code(
        "current_state_evidence_stale",
        lambda: apply_state_patch(
            first.state,
            patch(set_change("verified", True, "test-1"), revision=1),
            field_specs=FIELDS,
            evidence_hashes={"test-1": TEST_SHA256},
        ),
    )


def test_patch_rejects_wrong_value_types_and_bool_as_integer():
    initial = new_execution_state("session-1", TASK_SHA256)

    assert_code(
        "state_patch_value_invalid",
        lambda: apply_state_patch(
            initial,
            patch(set_change("test_count", True, "test-1")),
            field_specs=FIELDS,
            evidence_hashes=EVIDENCE,
        ),
    )
    assert_code(
        "state_patch_value_invalid",
        lambda: apply_state_patch(
            initial,
            patch(set_change("test_count", 2**63, "test-1")),
            field_specs=FIELDS,
            evidence_hashes=EVIDENCE,
        ),
    )


def test_required_fields_cannot_be_deleted_or_left_unset():
    initial = new_execution_state("session-1", TASK_SHA256)
    assert_code(
        "required_state_field_missing",
        lambda: apply_state_patch(
            initial,
            patch(set_change("verified", False, "test-1")),
            field_specs=FIELDS,
            evidence_hashes=EVIDENCE,
        ),
    )
    seeded = apply_state_patch(
        initial,
        patch(set_change("task_summary", "Known issue", "obs-1")),
        field_specs={"task_summary": FIELDS["task_summary"]},
        evidence_hashes=EVIDENCE,
    ).state
    delete_required = {
        "op": "delete",
        "field": "task_summary",
        "evidence_ids": ["test-1"],
    }
    assert_code(
        "required_state_field_cannot_be_deleted",
        lambda: apply_state_patch(
            seeded,
            patch(delete_required, revision=1),
            field_specs={"task_summary": FIELDS["task_summary"]},
            evidence_hashes=EVIDENCE,
        ),
    )


def test_patch_rejects_duplicate_fields_and_missing_evidence():
    initial = new_execution_state("session-1", TASK_SHA256)
    assert_code(
        "state_patch_duplicate_field",
        lambda: apply_state_patch(
            initial,
            patch(
                set_change("task_summary", "First", "obs-1"),
                set_change("task_summary", "Second", "test-1"),
            ),
            field_specs=FIELDS,
            evidence_hashes=EVIDENCE,
        ),
    )
    assert_code(
        "state_patch_evidence_refs_invalid",
        lambda: apply_state_patch(
            initial,
            patch({"op": "set", "field": "task_summary", "value": "No evidence", "evidence_ids": []}),
            field_specs=FIELDS,
            evidence_hashes=EVIDENCE,
        ),
    )


def test_patch_rejects_unknown_fields_and_non_json_shapes():
    initial = new_execution_state("session-1", TASK_SHA256)
    assert_code(
        "state_patch_field_not_allowed",
        lambda: apply_state_patch(
            initial,
            patch(set_change("unreviewed_fact", "value", "obs-1")),
            field_specs=FIELDS,
            evidence_hashes=EVIDENCE,
        ),
    )
    assert_code(
        "state_patch_shape_invalid",
        lambda: apply_state_patch(
            initial,
            {**patch(set_change("task_summary", "x", "obs-1")), "extra": True},
            field_specs=FIELDS,
            evidence_hashes=EVIDENCE,
        ),
    )


def test_patch_and_state_are_bounded():
    initial = new_execution_state("session-1", TASK_SHA256)
    large_fields = {f"fact_{i}": StateFieldSpec("string", max_chars=4096) for i in range(5)}
    changes = [set_change(field, "x" * 4096, "obs-1") for field in large_fields]

    assert_code(
        "state_patch_byte_limit_exceeded",
        lambda: apply_state_patch(
            initial,
            patch(*changes),
            field_specs=large_fields,
            evidence_hashes=EVIDENCE,
        ),
    )


def test_state_cumulative_size_limit_applies_across_revisions():
    field_specs = {
        f"fact_{index:02d}": StateFieldSpec("string", max_chars=2048)
        for index in range(35)
    }
    state = new_execution_state("session-1", TASK_SHA256)
    for start in range(0, 35, 7):
        changes = [
            set_change(field, "x" * 2048, "obs-1")
            for field in list(field_specs)[start : start + 7]
        ]
        proposal = patch(*changes, revision=state.revision)
        if start == 28:
            assert_code(
                "execution_state_byte_limit_exceeded",
                lambda: apply_state_patch(
                    state,
                    proposal,
                    field_specs=field_specs,
                    evidence_hashes=EVIDENCE,
                ),
            )
        else:
            state = apply_state_patch(
                state,
                proposal,
                field_specs=field_specs,
                evidence_hashes=EVIDENCE,
            ).state
