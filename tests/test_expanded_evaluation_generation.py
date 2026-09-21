from __future__ import annotations

import json

from tools.generate_expanded_evaluation import build


def test_health_eligible_prompts_bind_numeric_bounds_in_the_request():
    rows = [row for row in build() if row["family"] == "health_read" and row["category"] == "eligible"]
    assert len(rows) == 20
    for row in rows:
        target = json.loads(row["target"])
        assert str(target["timeout_seconds"]) in row["prompt"]
        assert str(target["max_bytes"]) in row["prompt"]


def test_patch_eligible_prompts_bind_the_exact_review_diff():
    rows = [row for row in build() if row["family"] == "patch_draft" and row["category"] == "eligible"]
    assert len(rows) == 20
    for row in rows:
        target = json.loads(row["target"])
        assert target["diff"] in row["prompt"]


def test_read_file_eligible_variants_use_the_verifier_ceiling():
    rows = [row for row in build() if row["family"] == "read_file" and row["category"] == "eligible"]
    assert len(rows) == 20
    assert {json.loads(row["target"])["max_bytes"] for row in rows} == {262144}
