"""Provider-free binding from an OpenCode session record to E0 preparation.

This is an offline adapter seam. It does not register an OpenCode plugin,
query the OpenCode API, or authorize downstream dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .artifact_store import ArtifactStore
from .e0_context_pipeline import PreparationResult, prepare_e0_context
from .namespace_registry import NamespaceRegistry
from .opencode_session_root import resolve_opencode_session_root
from .snapshot import SourceSnapshot


@dataclass(frozen=True)
class OpenCodePreparationJoin:
    """Keep the session/root/snapshot identity alongside local preparation."""

    session_id: str
    configured_root: Path
    snapshot_sha256: str
    root_location_sha256: str | None
    root_identity: str | None
    preparation: PreparationResult


def prepare_opencode_e0_context(
    event_session_id: str,
    session_record: object,
    *,
    snapshot: SourceSnapshot,
    paths: Sequence[str | PathLike[str]],
    store: ArtifactStore,
    query: str,
    source_order_start: int,
    context_token_budget: int,
    prompt_token_budget: int,
    namespace_registry: NamespaceRegistry,
    schema_lookups: Sequence[tuple[str, str]],
    base_messages: Sequence[Mapping[str, object]],
    context_position: int,
    serializer: Callable[[Sequence[Mapping[str, object]]], str | bytes],
    tokenizer_counter: Callable[[str | bytes], int],
    serializer_id: str,
    tokenizer_id: str,
    required_evidence_ids: Sequence[str] = (),
    preserve_evidence_ids: Sequence[str] = (),
    required_source_paths: Sequence[str] = (),
    preserve_source_paths: Sequence[str] = (),
    max_candidates: int = 8,
) -> OpenCodePreparationJoin:
    """Resolve one session root and prepare only against that configured root.

    The signature mirrors the bounded E0 preparation surface except that the
    caller cannot supply or override ``source_root``. Preparation itself
    checks that the snapshot identity matches this root during exact reads.
    """
    if type(snapshot) is not SourceSnapshot:
        raise ValueError("invalid_source_snapshot")
    resolved = resolve_opencode_session_root(event_session_id, session_record)
    result = prepare_e0_context(
        source_root=resolved.configured_root,
        snapshot=snapshot,
        paths=paths,
        store=store,
        query=query,
        source_order_start=source_order_start,
        context_token_budget=context_token_budget,
        prompt_token_budget=prompt_token_budget,
        namespace_registry=namespace_registry,
        schema_lookups=schema_lookups,
        base_messages=base_messages,
        context_position=context_position,
        serializer=serializer,
        tokenizer_counter=tokenizer_counter,
        serializer_id=serializer_id,
        tokenizer_id=tokenizer_id,
        required_evidence_ids=required_evidence_ids,
        preserve_evidence_ids=preserve_evidence_ids,
        required_source_paths=required_source_paths,
        preserve_source_paths=preserve_source_paths,
        max_candidates=max_candidates,
    )
    return OpenCodePreparationJoin(
        session_id=resolved.session_id,
        configured_root=resolved.configured_root,
        snapshot_sha256=snapshot.snapshot_sha256,
        root_location_sha256=snapshot.root_location_sha256,
        root_identity=snapshot.root_identity,
        preparation=result,
    )


__all__ = ["OpenCodePreparationJoin", "prepare_opencode_e0_context"]
