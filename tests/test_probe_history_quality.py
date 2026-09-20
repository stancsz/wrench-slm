from pathlib import Path


def test_history_quality_probe_is_explicitly_synthetic_and_bounded():
    source = Path("tools/probe_history_quality.py").read_text(encoding="utf-8")
    assert "WRENCH CURRENT CONTROL BLOCK" in source
    assert "include-control-block" in source
    assert "history_skip_layers_before" in source
    assert "quality_claim" in source
    assert '"max_tokens": 128' in source
    assert "execute_model_output" in source
