"""Stable provenance helpers for cross-host JSONL evaluation inputs."""

from __future__ import annotations

import hashlib
from pathlib import Path


def canonical_jsonl_bytes(path: Path) -> bytes:
    """Return JSONL bytes with platform line endings normalized to LF."""

    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def canonical_jsonl_sha256(path: Path) -> str:
    return hashlib.sha256(canonical_jsonl_bytes(path)).hexdigest()


def raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
