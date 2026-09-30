import pytest

from tools.score_gateway_lora_screen_02 import (
    EXPECTED_ADAPTER_PROFILE,
    EXPECTED_STEPS,
    EXPECTED_TARGET_COUNT,
    EXPECTED_TARGET_MODULES,
    EXPECTED_TRAINABLE_PARAMETER_COUNT,
    EXPECTED_TRAINER_SOURCE_SHA256,
    verify_fit03_candidate_identity,
)


def _run_receipt() -> dict:
    return {
        "adapter_profile": EXPECTED_ADAPTER_PROFILE,
        "matched_target_count": EXPECTED_TARGET_COUNT,
        "matched_target_modules": list(EXPECTED_TARGET_MODULES),
        "trainable_parameter_count": EXPECTED_TRAINABLE_PARAMETER_COUNT,
        "fit_mode": True,
        "preflight_only": False,
        "expected_fit_optimizer_steps": EXPECTED_STEPS,
        "optimizer_steps": EXPECTED_STEPS,
        "runner_sha256": EXPECTED_TRAINER_SOURCE_SHA256,
    }


def test_fit03_candidate_requires_reviewed_trainer_and_exact_target_list():
    verify_fit03_candidate_identity(_run_receipt(), EXPECTED_TRAINER_SOURCE_SHA256)


def test_fit03_candidate_rejects_self_consistent_but_unreviewed_trainer():
    unreviewed_hash = "f" * 64
    receipt = {**_run_receipt(), "runner_sha256": unreviewed_hash}
    with pytest.raises(RuntimeError, match="reviewed runner"):
        verify_fit03_candidate_identity(receipt, unreviewed_hash)


def test_fit03_candidate_rejects_unreviewed_source_snapshot():
    with pytest.raises(RuntimeError, match="reviewed runner"):
        verify_fit03_candidate_identity(_run_receipt(), "e" * 64)


def test_fit03_candidate_rejects_changed_target_names_even_with_matching_count():
    receipt = _run_receipt()
    receipt["matched_target_modules"][-1] = "model.language_model.layers.23.mlp.down_proj"
    with pytest.raises(RuntimeError, match="attention-only fit-03 candidate"):
        verify_fit03_candidate_identity(receipt, EXPECTED_TRAINER_SOURCE_SHA256)


def test_fit03_candidate_rejects_wrong_fit_mode_or_step_count():
    receipt = {**_run_receipt(), "preflight_only": True}
    with pytest.raises(RuntimeError, match="attention-only fit-03 candidate"):
        verify_fit03_candidate_identity(receipt, EXPECTED_TRAINER_SOURCE_SHA256)
