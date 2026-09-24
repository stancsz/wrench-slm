"""Provider-free validation of the OpenCode session root boundary.

This module accepts the session record returned by a future OpenCode adapter.
It does not query OpenCode, load a plugin, or authorize model dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .snapshot import SnapshotAdmissionError, SourceRootBinding, bind_source_root


MAX_SESSION_ID_CHARS = 256
MAX_SESSION_ROOT_CHARS = 32_767


class OpenCodeSessionRootError(ValueError):
    """The OpenCode session record cannot safely identify a source root."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class OpenCodeSessionRoot:
    """Validated session identity and captured configured root binding."""

    session_id: str
    binding: SourceRootBinding

    @property
    def configured_root(self) -> Path:
        return self.binding.configured_root


def _valid_session_id(value: object) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("ses")
        and 0 < len(value) <= MAX_SESSION_ID_CHARS
        and not any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
    )


def resolve_opencode_session_root(
    event_session_id: str,
    session_record: Any,
) -> OpenCodeSessionRoot:
    """Bind a matching OpenCode session record to its validated source root.

    Only ``location.directory`` is accepted. An absent or empty ``subpath`` is
    allowed; any other value remains ambiguous until OpenCode defines its root
    semantics for the selected runtime. This function never falls back to a
    process directory, plugin location, cached path, or guessed worktree.
    """
    if not _valid_session_id(event_session_id):
        raise OpenCodeSessionRootError("invalid_event_session_id")
    if not isinstance(session_record, dict):
        raise OpenCodeSessionRootError("invalid_session_record")

    record_id = session_record.get("id")
    if not _valid_session_id(record_id) or record_id != event_session_id:
        raise OpenCodeSessionRootError("session_id_mismatch")

    location = session_record.get("location")
    if not isinstance(location, dict):
        raise OpenCodeSessionRootError("session_location_missing")
    directory = location.get("directory")
    if (
        not isinstance(directory, str)
        or not directory
        or len(directory) > MAX_SESSION_ROOT_CHARS
        or "\x00" in directory
    ):
        raise OpenCodeSessionRootError("invalid_session_directory")

    subpath = session_record.get("subpath")
    if "subpath" in session_record and subpath != "":
        raise OpenCodeSessionRootError("ambiguous_session_subpath")

    try:
        candidate = Path(directory)
        if not candidate.is_absolute():
            raise OpenCodeSessionRootError("session_directory_must_be_absolute")
        if any(part == ".." for part in candidate.parts):
            raise OpenCodeSessionRootError("session_directory_parent_component")
        binding = bind_source_root(candidate)
    except OpenCodeSessionRootError:
        raise
    except (SnapshotAdmissionError, OSError, TypeError, ValueError) as exc:
        raise OpenCodeSessionRootError("session_directory_not_usable") from exc

    return OpenCodeSessionRoot(record_id, binding)


__all__ = [
    "MAX_SESSION_ID_CHARS",
    "MAX_SESSION_ROOT_CHARS",
    "OpenCodeSessionRoot",
    "OpenCodeSessionRootError",
    "resolve_opencode_session_root",
]
