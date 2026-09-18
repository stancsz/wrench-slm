from __future__ import annotations

import subprocess
import json
from pathlib import Path

from wrench_harness import execute_proposal
from tools.validate_pruning_source import validate_pruning_source


def proposal(action: str, **fields):
    return {"schema": "wrench.proposal.v1", "action": action, **fields}


def test_read_file_and_lines_are_bounded(tmp_path: Path):
    target = tmp_path / "note.txt"
    target.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")

    result = execute_proposal(proposal("read_file", path="note.txt"), tmp_path)
    assert result["status"] == "accepted"
    assert result["observation"]["text"] == "alpha\nbeta\ngamma\n"

    result = execute_proposal(proposal("read_lines", path="note.txt", start=2, end=3), tmp_path)
    assert result["status"] == "accepted"
    assert result["observation"]["lines"] == ["beta", "gamma"]

    rejected = execute_proposal(proposal("read_file", path="..\\outside.txt"), tmp_path)
    assert rejected == {"status": "abstain", "fallback_reason": "path_outside_allowed_root"}


def test_literal_search_is_not_regex_and_respects_limit(tmp_path: Path):
    (tmp_path / "a.txt").write_text("needle\nneedle.*\n", encoding="utf-8")
    result = execute_proposal(proposal("literal_search", root=".", literal="needle.*", max_matches=3), tmp_path)
    assert result["status"] == "accepted"
    assert result["observation"]["matches"][0]["line"] == 2
    assert result["observation"]["truncated"] is False

    capped = execute_proposal(proposal("literal_search", root=".", literal="needle.*", max_matches=1), tmp_path)
    assert len(capped["observation"]["matches"]) == 1
    assert capped["observation"]["truncated"] is True

    regex = execute_proposal(
        proposal("literal_search", root=".", literal="^needle", mode="regex", max_matches=3), tmp_path
    )
    assert regex["fallback_reason"] == "literal_mode_required"


def test_git_status_is_read_only(tmp_path: Path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    result = execute_proposal(proposal("git_read_status", repo_root="."), tmp_path)
    assert result["status"] == "accepted"
    assert result["observation"]["mutated"] is False


def test_health_and_patch_fail_closed(tmp_path: Path):
    target = tmp_path / "note.txt"
    target.write_text("old\n", encoding="utf-8")
    external = execute_proposal(proposal("health_read", url="https://example.com/health"), tmp_path)
    assert external["fallback_reason"] == "health_endpoint_not_allowlisted"

    patch = execute_proposal(
        proposal(
            "patch_draft",
            files=["note.txt"],
            review_only=True,
            diff="--- a/note.txt\n+++ b/note.txt\n@@ -1 +1 @@\n-old\n+new\n",
        ),
        tmp_path,
    )
    assert patch["status"] == "accepted"
    assert patch["observation"]["applied"] is False
    assert target.read_text(encoding="utf-8") == "old\n"

    applied = execute_proposal(proposal("patch_draft", files=["note.txt"], review_only=False, diff="x"), tmp_path)
    assert applied["fallback_reason"] == "patch_draft_requires_review_only"


def test_pruning_source_rejects_packed_ftw(tmp_path: Path):
    (tmp_path / "config.json").write_text(
        json.dumps(
            {
                "model_type": "qwen3_5_moe",
                "architectures": ["Qwen3_5MoeForConditionalGeneration"],
                "text_config": {
                    "num_hidden_layers": 40,
                    "hidden_size": 2048,
                    "num_experts": 256,
                    "num_experts_per_tok": 8,
                },
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "hf_quant_config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "freetoken-00000.ftw").write_bytes(b"packed")
    result = validate_pruning_source(tmp_path)
    assert result["eligible"] is False
    assert "packed_ftw_not_sliceable" in result["rejection_reasons"]
    assert "safetensors_index_missing" in result["rejection_reasons"]
