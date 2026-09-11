import json

from scripts.build_production_readiness_receipt import build


def test_paired_receipt_matches_discovery_and_profile(tmp_path):
    source = tmp_path / "logs"
    (source / "events").mkdir(parents=True)
    (source / "events" / "day.jsonl").write_text(
        json.dumps({"req_id": "r", "prompt": "read", "tool": "read_file", "prompt_tokens": 3, "completion_tokens": 2}) + "\n",
        encoding="utf-8",
    )
    receipt = build(source, tmp_path / "out")
    assert receipt["event_count_match"] is True
    assert receipt["source_event_records"] == 1
    assert receipt["profile_events"] == 1
    assert receipt["raw_content_written"] is False
    assert receipt["readiness_reasons"] == ["MISSING_PROMPT_OR_CONTEXT", "PRICE_LEDGER_REQUIRED", "DURATION_UNIT_UNVERIFIED_OR_OUTLIER"]
