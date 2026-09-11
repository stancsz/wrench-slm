import json
import hashlib
import subprocess
import sys

import pytest

from scripts.redact_production_scenarios import convert, convert_row, validate_authorization


def test_convert_row_redacts_secrets_deterministically():
    row = {"request_id": "req-1", "source_class": "observed_production_replay", "replay_eligible": False, "prompt": "use token=abc123456789 now", "context": {"x": "sk-abcdefghijklmnop", "key": "-----BEGIN RSA PRIVATE KEY-----\nsecret-body\n-----END RSA PRIVATE KEY-----"}}
    result = convert_row(row, "a" * 64, 1)
    assert result["redaction"]["status"] == "complete"
    assert result["redaction"]["replacement_count"] == 3
    assert "abc123456789" not in result["prompt"]
    assert "sk-abcdefghijklmnop" not in json.dumps(result)
    assert "secret-body" not in json.dumps(result)


def test_convert_rejects_evaluator_fields(tmp_path):
    source = tmp_path / "input.jsonl"
    source.write_text(json.dumps({"source_class": "synthetic", "replay_eligible": False, "prompt": "x", "context": {}, "expected_answer": "y"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="evaluator-only"):
        convert(source, tmp_path / "out.jsonl")


def test_convert_writes_only_audit_fields(tmp_path):
    source = tmp_path / "input.jsonl"
    source.write_text(json.dumps({"request_id": "r", "source_class": "synthetic", "replay_eligible": True, "prompt": "x", "context": {}, "usage": {"prompt_tokens": 4}}) + "\n", encoding="utf-8")
    output = tmp_path / "out.jsonl"
    counts = convert(source, output)
    row = json.loads(output.read_text(encoding="utf-8"))
    assert counts == {"input_rows": 1, "output_rows": 1, "rejected_rows": 0}
    assert set(row) == {"id", "source_class", "source_ref_sha256", "redaction", "prompt", "context", "replay_eligible"}


def test_convert_rejects_unclassified_rows(tmp_path):
    with pytest.raises(ValueError, match="explicitly classified"):
        convert_row({"prompt": "x", "context": {}}, "a" * 64, 1)


def test_convert_rejects_unapproved_replay_default():
    with pytest.raises(ValueError, match="replay_eligible"):
        convert_row({"source_class": "synthetic", "prompt": "x", "context": {}}, "a" * 64, 1)


def test_convert_does_not_leave_partial_output_on_rejection(tmp_path):
    source = tmp_path / "input.jsonl"
    source.write_text(
        json.dumps({"source_class": "synthetic", "replay_eligible": True, "prompt": "ok", "context": {}}) + "\n"
        + json.dumps({"source_class": "synthetic", "replay_eligible": True, "prompt": "bad", "context": {}, "gold": "x"}) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "out.jsonl"
    with pytest.raises(ValueError):
        convert(source, output)
    assert not output.exists()


def test_convert_preserves_existing_output_on_rejection(tmp_path):
    source = tmp_path / "input.jsonl"
    source.write_text(json.dumps({"source_class": "synthetic", "replay_eligible": True, "prompt": "bad", "context": {}, "gold": "x"}) + "\n", encoding="utf-8")
    output = tmp_path / "out.jsonl"
    output.write_text("previous trusted export\n", encoding="utf-8")
    with pytest.raises(ValueError):
        convert(source, output)
    assert output.read_text(encoding="utf-8") == "previous trusted export\n"


def test_authorization_receipt_must_match_source_hash(tmp_path):
    receipt = tmp_path / "authorization.json"
    receipt.write_text(json.dumps({"authorized": True, "source_sha256": "a" * 64}), encoding="utf-8")
    validate_authorization(receipt, "a" * 64)
    receipt.write_text(json.dumps({"authorized": False, "source_sha256": "a" * 64}), encoding="utf-8")
    with pytest.raises(ValueError, match="authorized=true"):
        validate_authorization(receipt, "a" * 64)


def test_cli_requires_matching_authorization_and_writes_export(tmp_path):
    source = tmp_path / "input.jsonl"
    source.write_text(json.dumps({"source_class": "synthetic", "replay_eligible": True, "prompt": "x", "context": {}}) + "\n", encoding="utf-8")
    receipt = tmp_path / "authorization.json"
    receipt.write_text(json.dumps({"authorized": True, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}), encoding="utf-8")
    output = tmp_path / "out.jsonl"
    result = subprocess.run([sys.executable, "scripts/redact_production_scenarios.py", "--input", str(source), "--output", str(output), "--authorization-receipt", str(receipt)], capture_output=True, text=True)
    assert result.returncode == 0
    assert output.exists()
    receipt.write_text(json.dumps({"authorized": True, "source_sha256": "0" * 64}), encoding="utf-8")
    rejected = tmp_path / "rejected.jsonl"
    result = subprocess.run([sys.executable, "scripts/redact_production_scenarios.py", "--input", str(source), "--output", str(rejected), "--authorization-receipt", str(receipt)], capture_output=True, text=True)
    assert result.returncode != 0
    assert not rejected.exists()
