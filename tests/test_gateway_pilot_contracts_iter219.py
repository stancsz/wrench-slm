import json
from pathlib import Path

import pytest

from wrench_harness.gateway_pilot_contracts import (
    validate_diverse_manifest,
    verify_episode_answer,
)


ROOT = Path(__file__).resolve().parents[1]
V218 = ROOT / "examples/gateway_context_mvp/iteration218_diverse_pilot_manifest.json"
V219 = ROOT / "examples/gateway_context_mvp/iteration219_diverse_pilot_manifest.json"


def _manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _episode(manifest: dict, episode_id: str) -> dict:
    return next(
        episode
        for repository in manifest["repositories"]
        for episode in repository["episodes"]
        if episode["id"] == episode_id
    )


def test_iter219_manifest_has_twelve_balanced_tasks_and_non_noop_repairs() -> None:
    result = validate_diverse_manifest(_manifest(V219))
    assert result == {
        "repositories": 3,
        "episodes": 12,
        "source_localization": 3,
        "bounded_code_repair": 3,
        "test_log_diagnosis": 3,
        "configuration_documentation": 3,
    }


def test_iter218_is_rejected_before_inference_because_repairs_are_noops() -> None:
    with pytest.raises(ValueError, match="code_repair_task_is_noop_on_initial_fixture"):
        validate_diverse_manifest(_manifest(V218))


@pytest.mark.parametrize(
    ("episode_id", "answer"),
    [
        (
            "api-02",
            "def retry_delay(attempt, base_ms, cap_ms):\n"
            "    return min(base_ms * (2 ** max(0, attempt)), cap_ms)\n",
        ),
        (
            "cache-02",
            "def bounded_ttl(requested_seconds, minimum_seconds, maximum_seconds):\n"
            "    return min(max(requested_seconds, minimum_seconds), maximum_seconds)\n",
        ),
        (
            "batch-02",
            "def bounded_batch_size(requested, minimum, maximum, quantum):\n"
            "    return min(max(requested - (requested % quantum), minimum), maximum)\n",
        ),
    ],
)
def test_iter219_repaired_functions_pass_predeclared_behavior_cases(episode_id: str, answer: str) -> None:
    result = verify_episode_answer(_episode(_manifest(V219), episode_id), answer)
    assert result["passed"] is True


def test_repair_verifier_rejects_unsafe_ast_and_behavior_regression() -> None:
    episode = _episode(_manifest(V219), "api-02")
    unsafe = "def retry_delay(attempt, base_ms, cap_ms):\n    return __import__('os').system('whoami')\n"
    wrong_negative_attempt = "def retry_delay(attempt, base_ms, cap_ms):\n    return min(base_ms * (2 ** attempt), cap_ms)\n"
    assert verify_episode_answer(episode, unsafe)["reason"] == "function_ast_or_signature_invalid"
    assert verify_episode_answer(episode, wrong_negative_attempt)["reason"] == "behavior_mismatch"


def test_evidence_oracle_checks_answer_terms_and_exact_quotes() -> None:
    manifest = _manifest(V219)
    episode = _episode(manifest, "api-03")
    answer = (
        "The report matches the test failure: the cap is 400 but the delay returns 800. "
        "test_retry_delay_caps_at_configured_limit "
        "return base_ms * (2 ** attempt) "
        "attempt=3 returned_ms=800 cap_ms = 400"
    )
    assert verify_episode_answer(episode, answer)["passed"] is True
    assert verify_episode_answer(episode, answer.replace("matches", "conflicts"))["passed"] is False


def test_exact_json_oracle_rejects_extra_or_wrong_fields() -> None:
    episode = _episode(_manifest(V219), "api-04")
    correct = '{"base_ms":100,"cap_ms":400,"max_attempts":4,"source":"config/gateway.toml"}'
    extra = '{"base_ms":100,"cap_ms":400,"max_attempts":4,"source":"config/gateway.toml","auth":300}'
    assert verify_episode_answer(episode, correct)["passed"] is True
    assert verify_episode_answer(episode, extra)["reason"] == "json_value_mismatch"
