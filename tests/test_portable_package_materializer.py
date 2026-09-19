from pathlib import Path


def test_materializer_is_available_and_does_not_overwrite_by_contract():
    script = Path("tools/materialize_wrench_portable_package.py").read_text(encoding="utf-8")
    assert "refusing to overwrite existing target" in script
    assert "copy_cross_volume" in script
    assert "serve_freetoken.ps1" in script
    assert "EXPERIMENTAL_NOT_PUBLISHABLE" in script
    assert "public_upload_authorized" in script
