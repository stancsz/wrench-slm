from __future__ import annotations

import json

from tools.train_intent_router import _evaluate_predictions, _label


def test_intent_router_labels_allowlisted_family_and_boundary_as_abstain():
    assert _label({"expected_status": "accepted", "family": "read_file"}) == "read_file"
    assert _label({"expected_status": "abstain", "family": "read_file"}) == "abstain"
    assert _label({"expected_status": "abstain", "family": "out_of_domain"}) == "abstain"


def test_intent_router_keeps_boundary_verifier_in_authority(tmp_path):
    target = tmp_path / "README.md"
    target.write_text("hello\n", encoding="utf-8")
    rows = [
        {
            "id": "accepted-read",
            "family": "read_file",
            "prompt": "Read README.md with a 4096 byte ceiling.",
            "target": json.dumps(
                {
                    "schema": "wrench.proposal.v1",
                    "action": "read_file",
                    "path": "README.md",
                    "max_bytes": 4096,
                }
            ),
            "expected_status": "accepted",
        },
        {
            "id": "missing-read",
            "family": "read_file",
            "prompt": "Read a missing file safely.",
            "target": "{}",
            "expected_status": "abstain",
        },
    ]
    result = _evaluate_predictions(rows, ["read_file", "read_file"], [0.99, 0.99], allowed_root=tmp_path)
    assert result["outcome_matches"] == 2
    assert result["verified_accepts"] == 1
    assert result["prohibited_accepts"] == 0
