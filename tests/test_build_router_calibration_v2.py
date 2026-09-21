from pathlib import Path

from tools.build_router_calibration_v2 import build


def test_router_calibration_v2_uses_only_calibration_rows_and_adds_paths():
    input_path = Path("evals/wrench-expanded-v2/calibration.jsonl")
    rows, manifest = build(input_path)
    assert manifest["split_policy"].startswith("calibration_only")
    assert manifest["base_row_count"] == 132
    assert manifest["augmented_path_count"] >= 12
    assert len(rows) == manifest["row_count"]
    assert all(row["split"] == "calibration" for row in rows)
    augmented = [row for row in rows if row.get("source") == "path_diversity_v2"]
    assert any("src/wrench_harness/server.py" in row["prompt"] for row in augmented)
    assert any("phases/phase-264-current-source-4m-prefill/README.md" in row["prompt"] for row in augmented)
