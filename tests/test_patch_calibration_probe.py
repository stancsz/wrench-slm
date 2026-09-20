from tools.generate_patch_calibration_probe import build_rows


def test_explicit_patch_probe_has_operation_disjoint_holdout():
    train, holdout = build_rows()
    assert len(train) == 160
    assert len(holdout) == 40
    assert {row["family"] for row in train} == {"patch_draft"}
    assert {row["family"] for row in holdout} == {"patch_draft"}
    assert all('"review_only":true' in row["target"] for row in train + holdout)
    assert all("@@" in row["target"] for row in train + holdout)
    assert all(row["source"] == "explicit_patch_calibration_probe" for row in train + holdout)
