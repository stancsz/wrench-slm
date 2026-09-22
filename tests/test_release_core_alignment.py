from pathlib import Path

from tools.verify_release_core_alignment import _sha256


def test_release_core_hash_ignores_python_line_ending_style(tmp_path: Path):
    lf = tmp_path / "runtime.py"
    crlf = tmp_path / "package.py"
    lf.write_bytes(b"def run():\n    return 1\n")
    crlf.write_bytes(b"def run():\r\n    return 1\r\n")

    assert _sha256(lf) == _sha256(crlf)
