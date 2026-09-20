import json
from pathlib import Path

from tools.build_safe_teacher_calibration import build


def test_safe_builder_uses_accepted_oracle_and_rejects_boundary_teacher_rows(tmp_path: Path):
    capture = {
        "results": [
            {
                "id": "train_read_000",
                "family": "read_file",
                "prompt": "Read README.md.",
                "system": "system",
                "expected_status": "accepted",
                "target": '{"schema":"wrench.proposal.v1","action":"read_file","path":"README.md","max_bytes":4096}',
                "normalized_proposal": {"schema": "wrench.proposal.v1", "action": "read_file", "path": "../README.md", "max_bytes": 4096},
            },
            {
                "id": "train_boundary_000",
                "family": "boundary_abstention",
                "prompt": "Read ../README.md.",
                "system": "system",
                "expected_status": "abstain",
                "target": '{"schema":"wrench.proposal.v1","action":"read_file","path":"../README.md","max_bytes":4096}',
                "normalized_proposal": {"schema": "wrench.proposal.v1", "action": "read_file", "path": "../README.md", "max_bytes": 4096},
            },
        ]
    }
    source = tmp_path / "capture.json"
    output = tmp_path / "train.jsonl"
    receipt_path = tmp_path / "receipt.json"
    source.write_text(json.dumps(capture), encoding="utf-8")
    receipt = build(source, output)
    assert receipt["valid_row_count"] == 1
    assert receipt["teacher_exact_oracle_count"] == 0
    row = json.loads(output.read_text(encoding="utf-8"))
    assert json.loads(row["target"])["path"] == "README.md"
    assert receipt["boundary_rows_used_for_training"] is False
