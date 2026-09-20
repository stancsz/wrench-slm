from pathlib import Path

from tools.evaluate_mechanical_route import replay


def test_replay_passes_fixture_root_to_mechanical_route(tmp_path: Path):
    target = tmp_path / "patch.txt"
    target.write_text("old value\n", encoding="utf-8")
    cases = tmp_path / "cases.jsonl"
    cases.write_text(
        '{"id":"patch","family":"patch_draft","category":"eligible",'
        '"prompt":"Replace \\"old value\\" with \\"new value\\" in patch.txt '
        'and leave the file unchanged for review only.",'
        '"expected_status":"accepted",'
        '"target":"{\\"action\\":\\"patch_draft\\"}"}\n',
        encoding="utf-8",
    )

    receipt = replay(cases, tmp_path)

    assert receipt["mechanical_fast_path_requests"] == 1
    assert receipt["outcome_matches"] == 1
    assert receipt["prohibited_accepts"] == 0
