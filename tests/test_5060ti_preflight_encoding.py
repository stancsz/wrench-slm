from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "tools" / "run_5060ti_hf_preflight.ps1"


def test_5060ti_preflight_writes_resource_receipt_without_bom():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "UTF8Encoding($false)" in text
    assert "[IO.File]::WriteAllText($ResourcePath" in text
    assert "Set-Content -LiteralPath $ResourcePath -Encoding utf8" not in text
