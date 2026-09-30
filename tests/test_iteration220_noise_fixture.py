from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from examples.gateway_context_mvp.build_iteration220_noise_manifest import (
    NOISE_LINES_PER_REPOSITORY,
    OUTPUT,
    SOURCE,
    build_manifest,
)
from wrench_harness.gateway_pilot_contracts import validate_diverse_manifest


def test_iteration220_preserves_tasks_and_adds_bounded_non_oracle_noise() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    manifest = build_manifest(source)
    assert validate_diverse_manifest(manifest)["episodes"] == 12
    assert manifest["fixture_lineage"]["oracle_paths_passed_to_retriever"] is False

    for original, expanded in zip(source["repositories"], manifest["repositories"], strict=True):
        assert original["episodes"] == expanded["episodes"]
        assert all(
            expanded["files"][path] == content
            for path, content in original["files"].items()
        )
        log_paths = sorted(path for path in expanded["files"] if path.startswith("logs/adjacent-service"))
        assert len(log_paths) == 4
        assert sum(expanded["files"][path].count("\n") - 1 for path in log_paths) == NOISE_LINES_PER_REPOSITORY
        noise_text = "\n".join(
            expanded["files"][path]
            for path in expanded["files"]
            if path not in original["files"]
        )
        for episode in expanded["episodes"]:
            for quote in episode["oracle"].get("quotes", []):
                assert quote not in noise_text


def test_iteration220_frozen_manifest_exists_and_matches_builder() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    expected = build_manifest(source)
    actual = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert actual == expected
