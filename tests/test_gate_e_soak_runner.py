from __future__ import annotations

import json
from unittest.mock import patch

import pytest

import tools.run_gate_e_router_soak as soak_runner
from tools.run_gate_e_router_soak import (
    _next_receipt_destination,
    _response_failure_observation,
)


def test_soak_requires_explicit_run_flag(capsys):
    with patch.object(soak_runner, "_resource_snapshot", side_effect=AssertionError):
        assert soak_runner.main([]) == 0

    assert "--run" in capsys.readouterr().out


def test_help_does_not_start_soak():
    with patch.object(soak_runner, "_resource_snapshot", side_effect=AssertionError):
        with pytest.raises(SystemExit) as error:
            soak_runner.main(["--help"])

    assert error.value.code == 0


def test_approved_retry_timeouts_are_applied_by_runner():
    assert soak_runner.PROPOSAL_TIMEOUT_SECONDS == 20.0
    assert soak_runner.REQUEST_TIMEOUT_SECONDS == 30.0


def test_response_failure_observation_keeps_only_allowlisted_metadata():
    body = {
        "choices": [{"message": {"content": "do-not-persist-this-prompt"}}],
        "wrench": {
            "status": "abstain",
            "backend": "test-only-proposal-router",
            "fallback_reason": "router_queue_timeout",
            "model_calls": 0,
            "test_only_proposal_router": {
                "attempts": 28,
                "failures": 0,
                "circuit_open": False,
            },
            "detail": "do-not-persist-this-detail",
        },
    }

    observed = _response_failure_observation(body)

    assert observed == {
        "kind": "response_check_failed",
        "status": "abstain",
        "backend": "test-only-proposal-router",
        "fallback_reason": "router_queue_timeout",
        "model_calls": 0,
        "router_attempts": 28,
        "router_failures": 0,
        "circuit_open": False,
    }
    assert "do-not-persist" not in json.dumps(observed)


def test_unknown_fallback_reason_is_not_persisted():
    observed = _response_failure_observation(
        {"wrench": {"status": "abstain", "fallback_reason": "private user content"}}
    )

    assert observed["fallback_reason"] == "other"
    assert "private user content" not in json.dumps(observed)


def test_receipt_destination_preserves_prior_attempts(tmp_path):
    attempt, first = _next_receipt_destination(tmp_path)
    assert attempt == 1
    first.write_text("first receipt", encoding="utf-8")

    attempt, second = _next_receipt_destination(tmp_path)
    assert attempt == 2
    assert second.name == "router-soak-receipt-attempt-02.json"
    second.write_text("second receipt", encoding="utf-8")

    attempt, third = _next_receipt_destination(tmp_path)
    assert attempt == 3
    assert first.read_text(encoding="utf-8") == "first receipt"
    assert second.read_text(encoding="utf-8") == "second receipt"
    assert not third.exists()
