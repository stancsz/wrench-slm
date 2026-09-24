from pathlib import Path

import pytest

from wrench_harness.opencode_session_root import (
    OpenCodeSessionRootError,
    resolve_opencode_session_root,
)


def _record(session_id: str, directory: Path, **overrides):
    record = {
        "id": session_id,
        "location": {"directory": str(directory)},
    }
    record.update(overrides)
    return record


def test_resolves_matching_session_and_absolute_source_root(tmp_path):
    root = tmp_path / "project"
    root.mkdir()

    resolved = resolve_opencode_session_root(
        "ses_fixture123", _record("ses_fixture123", root)
    )

    assert resolved.session_id == "ses_fixture123"
    assert resolved.configured_root == root


@pytest.mark.parametrize(
    "event_id,record_id,error_code",
    [
        ("ses_event123", "ses_other123", "session_id_mismatch"),
        ("not_session_event123", "not_session_event123", "invalid_event_session_id"),
        ("ses_event123", "session_record123", "session_id_mismatch"),
        ("ses\x00event", "ses\x00event", "invalid_event_session_id"),
    ],
)
def test_rejects_invalid_or_mismatching_session_ids(
    tmp_path, event_id, record_id, error_code
):
    root = tmp_path / "project"
    root.mkdir()

    with pytest.raises(OpenCodeSessionRootError) as raised:
        resolve_opencode_session_root(event_id, _record(record_id, root))

    assert raised.value.code == error_code


@pytest.mark.parametrize(
    "record,error_code",
    [
        (None, "invalid_session_record"),
        ({"id": "ses_fixture123"}, "session_location_missing"),
        ({"id": "ses_fixture123", "location": None}, "session_location_missing"),
        (
            {"id": "ses_fixture123", "location": {"directory": "relative/path"}},
            "session_directory_must_be_absolute",
        ),
        (
            {"id": "ses_fixture123", "location": {"directory": ""}},
            "invalid_session_directory",
        ),
    ],
)
def test_rejects_malformed_or_missing_location(tmp_path, record, error_code):
    with pytest.raises(OpenCodeSessionRootError) as raised:
        resolve_opencode_session_root("ses_fixture123", record)

    assert raised.value.code == error_code


@pytest.mark.parametrize("subpath", ["src", "..", None, 7])
def test_rejects_nonempty_or_ambiguous_subpath(tmp_path, subpath):
    root = tmp_path / "project"
    root.mkdir()

    with pytest.raises(OpenCodeSessionRootError) as raised:
        resolve_opencode_session_root(
            "ses_fixture123",
            _record("ses_fixture123", root, subpath=subpath),
        )

    assert raised.value.code == "ambiguous_session_subpath"


def test_accepts_absent_or_empty_subpath(tmp_path):
    root = tmp_path / "project"
    root.mkdir()

    assert resolve_opencode_session_root(
        "ses_fixture123", _record("ses_fixture123", root)
    ).configured_root == root
    assert resolve_opencode_session_root(
        "ses_fixture123", _record("ses_fixture123", root, subpath="")
    ).configured_root == root


def test_rejects_unusable_source_root(tmp_path):
    missing = tmp_path / "missing"

    with pytest.raises(OpenCodeSessionRootError) as raised:
        resolve_opencode_session_root(
            "ses_fixture123", _record("ses_fixture123", missing)
        )

    assert raised.value.code == "session_directory_not_usable"
