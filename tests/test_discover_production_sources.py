import json

from scripts.discover_production_sources import discover


def test_discovery_is_metadata_only_and_counts_sources(tmp_path):
    source = tmp_path / "logs"
    (source / "events").mkdir(parents=True)
    (source / "tool_calls.log").write_text(
        "[INFO] Completed: read_file (call_1) args: {}\n"
        "[INFO] Completed: read_file (call_2) args: {}\n"
        "[INFO] Completed: exec_command (call_3) args: {}\n",
        encoding="utf-8",
    )
    (source / "events" / "day.jsonl").write_text('{"req_id":"one","prompt":"read","tool":"read_file","prompt_tokens":3,"input_tokens_estimate":4,"output_tokens_estimate":2}\nnot-json\n', encoding="utf-8")
    receipt = discover(source, tmp_path / "out")
    assert receipt["status"] == "SOURCE_DISCOVERED"
    assert receipt["completed_tool_records"] == 3
    assert receipt["event_json_records"] == 1
    assert receipt["cost_field_coverage"]["prompt_tokens"] == 1
    assert receipt["cost_field_coverage"]["input_tokens_estimate"] == 1
    assert receipt["replay_capabilities"]["has_completion_token_estimate"]
    assert receipt["replay_ready"]
    assert receipt["tool_distribution"]["read_file"] == 2
    assert receipt["raw_content_written"] is False
    saved = json.loads((tmp_path / "out" / "source-discovery.json").read_text(encoding="utf-8"))
    assert saved["production_authorization_required"] is True


def test_discovery_records_sqlite_schema_without_content(tmp_path):
    import sqlite3
    source = tmp_path / "logs"
    source.mkdir()
    db = sqlite3.connect(source / "state.sqlite3")
    db.execute("create table messages (id text, body text)")
    db.execute("insert into messages values ('r1', 'private body')")
    db.commit()
    db.close()
    receipt = discover(source, tmp_path / "out")
    assert receipt["sqlite_files"][0]["tables"][0]["name"] == "messages"
    assert receipt["sqlite_files"][0]["tables"][0]["rows"] == 1
    assert "private body" not in json.dumps(receipt)
