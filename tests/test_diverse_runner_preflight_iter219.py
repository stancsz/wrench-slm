import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from examples.gateway_context_mvp import run_diverse_local_pilot_iter219 as runner


def test_goal_identity_gate_accepts_only_exact_declared_bytes() -> None:
    runner.validate_goal_identity(runner.DECLARED_ACTIVE_GOAL_SHA256)
    with pytest.raises(RuntimeError, match="active_goal_identity_mismatch"):
        runner.validate_goal_identity("0" * 64)


def test_runner_preflight_stops_before_model_setup_when_goal_identity_is_stale(monkeypatch) -> None:
    monkeypatch.setattr(runner, "actual_goal_sha256", lambda: "0" * 64)
    monkeypatch.setattr(runner, "validate_storage_admission", lambda: pytest.fail("storage should not be touched"))
    with pytest.raises(RuntimeError, match="active_goal_identity_mismatch"):
        runner.preflight_identity()


def test_frozen_manifest_digest_and_contract_validate() -> None:
    manifest, digest = runner.load_and_validate_manifest()
    assert digest == runner.EXPECTED_MANIFEST_SHA256
    assert sum(len(repo["episodes"]) for repo in manifest["repositories"]) == 12


@pytest.mark.parametrize(
    ("requested_limit", "expected_limit"),
    [(None, 8192), (65536, 65536)],
)
def test_episode_context_forwards_bounded_ingestion_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, requested_limit: int | None, expected_limit: int
) -> None:
    forwarded: list[int] = []
    prepared_messages = [{"role": "user", "content": "def fixture()"}]

    def prepare(**kwargs):
        forwarded.append(kwargs["source_ingestion_token_limit"])
        return SimpleNamespace(
            status=runner.PreparationStatus.READY,
            prompt=json.dumps(prepared_messages),
            selected_source_references=None,
            retrieval_misses=(),
            omitted_evidence=(),
        )

    monkeypatch.setattr(runner, "prepare_e0_context", prepare)
    monkeypatch.setattr(runner, "_task_prompts", lambda _episode: ("system", "request"))
    monkeypatch.setattr(
        runner,
        "_render_messages",
        lambda _tokenizer, _messages: ("rendered", {"input_ids": SimpleNamespace(shape=(1, 5))}),
    )
    monkeypatch.setattr(runner.demo, "_token_count", lambda _tokenizer, _payload: 5)
    kwargs = {} if requested_limit is None else {"source_ingestion_token_limit": requested_limit}

    _, _, receipt = runner._build_episode_context(
        Mock(),
        "fixture-tokenizer",
        {"id": "fixture", "files": {"src/main.py": "def fixture():\\n    return 1\\n"}},
        {
            "id": "episode-1",
            "query_template": "find fixture function",
            "oracle": {"quotes": ["def fixture()"]},
        },
        tmp_path / "workspace",
        **kwargs,
    )

    assert forwarded == [expected_limit]
    assert receipt["oracle_quotes_visible"] == 1
