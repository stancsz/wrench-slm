from pathlib import Path


def test_history_lookup_probe_binds_old_needle_and_expected_proposal():
    source = Path("tools/probe_history_lookup.py").read_text(encoding="utf-8")
    assert "history-lookup-quality-probe.v1" in source
    assert "needle_offset" in source
    assert "src/wrench_harness/worker.py" in source
    assert "quality_claim" in source
    assert '"max_tokens": 128' in source
