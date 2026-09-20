from tools.generate_boundary_calibration_probe import build_rows


def test_boundary_probe_is_separate_from_final_split():
    rows = build_rows(20)
    assert len(rows) == 120
    assert len({row["expected_fallback_reason"] for row in rows}) == 6
    assert all(row["family"] == "boundary_abstention" for row in rows)
    assert all(row["source"] == "synthetic_boundary_calibration_probe" for row in rows)
    assert all(row["teacher_exact_oracle"] is True for row in rows)
