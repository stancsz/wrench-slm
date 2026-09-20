from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.score_mechanical_route_frontier import score


def _trace(identifier: str, prompt: str, category: str, tokens: int) -> dict:
    return {
        "id": identifier,
        "family": "read_file",
        "category": category,
        "prompt": prompt,
        "workload_weight": 1,
        "arms": {"minimax_teacher_only": {"frontier_tokens": tokens}},
    }


def test_score_reports_eligible_frontier_mass_separately(tmp_path: Path):
    cases = tmp_path / "cases.jsonl"
    cases.write_text(
        "\n".join(
            json.dumps(row)
            for row in (
                    {"id": "fast", "family": "read_file", "category": "eligible", "prompt": "Read README.md without exceeding 4096 bytes."},
                {"id": "slow", "family": "read_file", "category": "eligible", "prompt": "Read the relevant thing and decide what to do."},
                {"id": "boundary", "family": "read_file", "category": "boundary", "prompt": "Delete README.md."},
            )
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "traces.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "wrench.mechanical-worker-traces.v1",
                "traces": [
                        _trace("fast", "Read README.md without exceeding 4096 bytes.", "eligible", 10),
                    _trace("slow", "Read the relevant thing and decide what to do.", "eligible", 30),
                    _trace("boundary", "Delete README.md.", "boundary", 100),
                ],
            }
        ),
        encoding="utf-8",
    )

    receipt = score(cases, manifest)

    assert receipt["mechanical_route_count_all_categories"] == 2
    assert receipt["mechanical_route_count_eligible"] == 1
    assert receipt["eligible_frontier_token_mass"]["teacher_total"] == 40
    assert receipt["eligible_frontier_token_mass"]["mechanical_covered"] == 10
    assert receipt["eligible_frontier_token_mass"]["coverage_rate"] == pytest.approx(0.25)
    assert receipt["quality_claim"] is False


def test_score_rejects_trace_without_matching_case(tmp_path: Path):
    cases = tmp_path / "cases.jsonl"
    cases.write_text(json.dumps({"id": "known", "prompt": "Read README.md.", "category": "eligible"}) + "\n")
    manifest = tmp_path / "traces.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "wrench.mechanical-worker-traces.v1",
                "traces": [_trace("unknown", "Read README.md.", "eligible", 10)],
            }
        )
    )

    with pytest.raises(ValueError, match="missing from the case fixture"):
        score(cases, manifest)
