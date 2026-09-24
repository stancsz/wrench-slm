"""Provider-free snapshot input seam for an explicitly enrolled OpenCode root.

This module resolves the event/session/root through the Wrench-owned project
registry, validates a finite caller-selected subset of enrolled paths before
reading source bytes, then returns the existing bound ``SourceSnapshot``.
The result is only input to later context preparation. It is not a prompt,
dispatch decision, persistence operation, or exact-token gate.
"""

from __future__ import annotations

import itertools
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping

from .opencode_project_registry import (
    EnrolledProject,
    ExactTokenGateStatus,
    OpenCodeProjectRegistry,
    ProjectRegistryError,
)
from .snapshot import (
    MAX_SNAPSHOT_FILES,
    SnapshotAdmissionError,
    SourceRootBinding,
    SourceSnapshot,
    _normalize_relative_path,
    _path_duplicate_key,
    create_snapshot,
)


MAX_SELECTED_PATHS = MAX_SNAPSHOT_FILES


class ProjectSnapshotError(ValueError):
    """Project binding or selected source set cannot create a snapshot."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ProjectSnapshotStatus(str, Enum):
    SNAPSHOT_INPUT_READY = "snapshot_input_ready"


@dataclass(frozen=True)
class OpenCodeProjectSnapshot:
    """Bound, content-free metadata for a snapshot input seam."""

    status: ProjectSnapshotStatus
    project_id: str
    session_id: str = field(repr=False)
    binding: SourceRootBinding = field(repr=False)
    snapshot: SourceSnapshot = field(repr=False)
    selected_paths: tuple[str, ...] = field(repr=False)
    exact_token_gate: ExactTokenGateStatus = ExactTokenGateStatus.UNAVAILABLE


def _selected_path_subset(
    selected_paths: Iterable[str | os.PathLike[str]],
    project: EnrolledProject,
) -> tuple[str, ...]:
    if isinstance(selected_paths, (str, bytes, bytearray, os.PathLike, Mapping)):
        raise ProjectSnapshotError("selected_paths_must_be_finite_iterable")
    limit = min(MAX_SELECTED_PATHS, len(project.source_paths))
    try:
        iterator = iter(selected_paths)
    except (TypeError, ValueError) as exc:
        raise ProjectSnapshotError("selected_paths_must_be_finite_iterable") from exc

    allowed = {_path_duplicate_key(path) for path in project.source_paths}
    normalized: list[str] = []
    seen: set[str] = set()
    try:
        for index, value in enumerate(itertools.islice(iterator, limit + 1)):
            if index >= limit:
                raise ProjectSnapshotError("selected_path_count_limit_exceeded")
            try:
                path = _normalize_relative_path(value)
            except (SnapshotAdmissionError, TypeError, ValueError, OSError) as exc:
                raise ProjectSnapshotError("selected_path_invalid") from exc
            key = _path_duplicate_key(path)
            if key in seen:
                raise ProjectSnapshotError("selected_path_duplicate")
            if key not in allowed:
                raise ProjectSnapshotError("selected_path_not_enrolled")
            if any(_path_within(path, excluded) for excluded in project.exclusions):
                raise ProjectSnapshotError("selected_path_excluded")
            seen.add(key)
            normalized.append(path)
    except ProjectSnapshotError:
        raise
    except Exception as exc:
        raise ProjectSnapshotError("selected_paths_iteration_failed") from exc
    if not normalized:
        raise ProjectSnapshotError("selected_paths_empty")
    return tuple(sorted(normalized, key=_path_duplicate_key))


def _path_within(path: str, prefix: str) -> bool:
    path_key = _path_duplicate_key(path)
    prefix_key = _path_duplicate_key(prefix).rstrip("/")
    return path_key == prefix_key or path_key.startswith(prefix_key + "/")


def prepare_opencode_project_snapshot(
    registry: OpenCodeProjectRegistry,
    event_session_id: str,
    session_record: object,
    selected_paths: Iterable[str | os.PathLike[str]],
) -> OpenCodeProjectSnapshot:
    """Resolve enrollment and create one bounded, root-bound source snapshot.

    Every selected path is normalized, deduplicated, and checked against the
    enrolled finite set before the snapshot primitive reads any source file.
    The profile's file and aggregate ceilings are enforced by the secure
    snapshot readers, including while reading the final byte allowance.
    """
    if type(registry) is not OpenCodeProjectRegistry:
        raise ProjectSnapshotError("project_registry_invalid")
    try:
        project = registry.resolve_session(event_session_id, session_record)
    except ProjectRegistryError as exc:
        raise ProjectSnapshotError(exc.code) from exc
    selected = _selected_path_subset(selected_paths, project)
    try:
        snapshot = create_snapshot(
            project.binding,
            selected,
            max_source_bytes=project.max_file_bytes,
            max_snapshot_bytes=project.max_total_bytes,
        )
    except SnapshotAdmissionError as exc:
        raise ProjectSnapshotError(str(exc)) from exc
    return OpenCodeProjectSnapshot(
        status=ProjectSnapshotStatus.SNAPSHOT_INPUT_READY,
        project_id=project.project_id,
        session_id=project.session_id,
        binding=project.binding,
        snapshot=snapshot,
        selected_paths=selected,
        exact_token_gate=ExactTokenGateStatus.UNAVAILABLE,
    )


__all__ = [
    "MAX_SELECTED_PATHS",
    "OpenCodeProjectSnapshot",
    "ProjectSnapshotError",
    "ProjectSnapshotStatus",
    "prepare_opencode_project_snapshot",
]
