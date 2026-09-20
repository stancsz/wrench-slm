from pathlib import Path


def test_220_case_retrieval_receipt_reports_evidence_window_recall(tmp_path: Path):
    import json
    import subprocess
    import sys

    output = tmp_path / "retrieval.json"
    result = subprocess.run(
        [
            sys.executable,
            "tools/evaluate_mechanical_retrieval.py",
            "--cases",
            "220",
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["target_reference_recall"] == 1.0
    assert receipt["evidence_window_recall"] == 1.0
