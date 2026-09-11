import json

from scripts.verify_trusted_readiness import verify


def test_gate_rejects_current_receipt_with_explicit_reasons(tmp_path):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"schema": "production-readiness-receipt-v1", "read_only": True, "raw_content_written": False, "event_count_match": True, "replay_ready": False, "readiness_reasons": ["MISSING_PROMPT_OR_CONTEXT"]}), encoding="utf-8")
    result = verify(receipt)
    assert result["status"] == "REJECTED"
    assert "MISSING_PROMPT_OR_CONTEXT" in result["reasons"]
    assert "REPLAY_NOT_READY" in result["reasons"]
    assert "MISSING_SOURCE" in result["reasons"]


def test_gate_passes_only_complete_receipt(tmp_path):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"schema": "production-readiness-receipt-v1", "read_only": True, "raw_content_written": False, "source": "logs", "source_event_records": 1, "profile_events": 1, "replay_capabilities": {}, "usage_coverage": 1.0, "cost_status": "CALCULATED", "duration_unit_status": "UNVERIFIED_SECONDS", "event_count_match": True, "replay_ready": True, "readiness_reasons": []}), encoding="utf-8")
    assert verify(receipt)["status"] == "PASS"


def test_gate_rejects_incomplete_receipt_shape(tmp_path):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"schema": "production-readiness-receipt-v1", "read_only": True, "raw_content_written": False, "event_count_match": True, "replay_ready": True, "readiness_reasons": []}), encoding="utf-8")
    result = verify(receipt)
    assert result["status"] == "REJECTED"
    assert "MISSING_SOURCE" in result["reasons"]


def test_gate_rejects_non_read_only_receipt(tmp_path):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"event_count_match": True, "replay_ready": True, "readiness_reasons": [], "raw_content_written": True}), encoding="utf-8")
    result = verify(receipt)
    assert result["status"] == "REJECTED"
    assert "RAW_CONTENT_OUTPUT_FLAGGED" in result["reasons"]


def test_gate_recomputes_event_count_match(tmp_path):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"schema": "production-readiness-receipt-v1", "read_only": True, "raw_content_written": False, "source": "logs", "source_event_records": 2, "profile_events": 1, "replay_capabilities": {}, "usage_coverage": 1.0, "cost_status": "CALCULATED", "duration_unit_status": "UNVERIFIED_SECONDS", "event_count_match": True, "replay_ready": True, "readiness_reasons": []}), encoding="utf-8")
    result = verify(receipt)
    assert result["status"] == "REJECTED"
    assert "EVENT_COUNT_MISMATCH" in result["reasons"]


def test_gate_rejects_false_event_count_match_flag(tmp_path):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"schema": "production-readiness-receipt-v1", "read_only": True, "raw_content_written": False, "source": "logs", "source_event_records": 1, "profile_events": 1, "replay_capabilities": {}, "usage_coverage": 1.0, "cost_status": "CALCULATED", "duration_unit_status": "UNVERIFIED_SECONDS", "event_count_match": False, "replay_ready": True, "readiness_reasons": []}), encoding="utf-8")
    result = verify(receipt)
    assert result["status"] == "REJECTED"
    assert "EVENT_COUNT_MATCH_FLAG_FALSE" in result["reasons"]


def test_gate_rejects_invalid_usage_coverage(tmp_path):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"schema": "production-readiness-receipt-v1", "read_only": True, "raw_content_written": False, "source": "logs", "source_event_records": 1, "profile_events": 1, "replay_capabilities": {}, "usage_coverage": 2, "cost_status": "CALCULATED", "duration_unit_status": "UNVERIFIED_SECONDS", "event_count_match": True, "replay_ready": True, "readiness_reasons": []}), encoding="utf-8")
    result = verify(receipt)
    assert result["status"] == "REJECTED"
    assert "INVALID_USAGE_COVERAGE" in result["reasons"]


def test_gate_rejects_unknown_status_values(tmp_path):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"schema": "production-readiness-receipt-v1", "read_only": True, "raw_content_written": False, "source": "logs", "source_event_records": 1, "profile_events": 1, "replay_capabilities": {}, "usage_coverage": 1.0, "cost_status": "unknown", "duration_unit_status": "unknown", "event_count_match": True, "replay_ready": True, "readiness_reasons": []}), encoding="utf-8")
    result = verify(receipt)
    assert result["status"] == "REJECTED"
    assert "INVALID_COST_STATUS" in result["reasons"]
    assert "INVALID_DURATION_STATUS" in result["reasons"]


def test_gate_rejects_non_string_readiness_reasons_without_crashing(tmp_path):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"schema": "production-readiness-receipt-v1", "read_only": True, "raw_content_written": False, "source": "logs", "source_event_records": 1, "profile_events": 1, "replay_capabilities": {}, "usage_coverage": 1.0, "cost_status": "CALCULATED", "duration_unit_status": "UNVERIFIED_SECONDS", "event_count_match": True, "replay_ready": True, "readiness_reasons": [{"bad": True}]}), encoding="utf-8")
    result = verify(receipt)
    assert result["status"] == "REJECTED"
    assert result["reasons"] == ["INVALID_READINESS_REASONS"]
