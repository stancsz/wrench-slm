from pathlib import Path

from tools.evaluation_provenance import canonical_jsonl_sha256, raw_sha256


def test_jsonl_provenance_is_stable_across_platform_line_endings(tmp_path: Path):
    lf = tmp_path / "lf.jsonl"
    crlf = tmp_path / "crlf.jsonl"
    lf.write_bytes(b'{"id":1}\n{"id":2}\n')
    crlf.write_bytes(b'{"id":1}\r\n{"id":2}\r\n')

    assert canonical_jsonl_sha256(lf) == canonical_jsonl_sha256(crlf)
    assert raw_sha256(lf) != raw_sha256(crlf)
