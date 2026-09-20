from pathlib import Path

from wrench_harness.core import execute_proposal


def test_literal_search_prunes_model_artifacts_and_large_files(tmp_path: Path):
    (tmp_path / "source.py").write_text("needle\n", encoding="utf-8")
    artifact_dir = tmp_path / "artifacts" / "model"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "weights.safetensors").write_text("needle\n", encoding="utf-8")
    (tmp_path / "large.jsonl").write_bytes(b"needle\n" + b"x" * (8 * 1024 * 1024))

    result = execute_proposal(
        {
            "schema": "wrench.proposal.v1",
            "action": "literal_search",
            "root": ".",
            "literal": "needle",
            "max_matches": 10,
        },
        tmp_path,
    )

    assert result["status"] == "accepted"
    assert [item["path"] for item in result["observation"]["matches"]] == [str(tmp_path / "source.py")]
