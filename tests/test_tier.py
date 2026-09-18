import json

import pytest

from wrench_harness import TierSelectionError, select_experimental_tier


def _write_inputs(tmp_path, *, learned_routing="DISABLE", artifact_exists=True):
    artifact = tmp_path / "artifact"
    if artifact_exists:
        artifact.mkdir(parents=True)
    catalog = {
        "schema": "wrench.dual-tier-model-catalog.v1",
        "status": "EXPERIMENTAL_TWO_TIER_ARTIFACTS_VERIFIED",
        "quality_claim": False,
        "tiers": [
            {"label": "compact_8E_safety", "artifact": str(artifact), "parameter_count": 10, "packed_weight_gib": 1.0, "directory_gib": 1.1, "num_experts": 8},
            {"label": "larger_16E", "artifact": str(artifact), "parameter_count": 20, "packed_weight_gib": 2.0, "directory_gib": 2.1, "num_experts": 16},
        ],
    }
    policy = {"schema": "wrench.routing-policy.v1", "learned_routing": learned_routing, "fallback": "stronger_model_path", "quality_claim": False}
    catalog_path = tmp_path / "catalog.json"
    policy_path = tmp_path / "policy.json"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    return catalog_path, policy_path


def test_select_experimental_tier_requires_disable_and_existing_artifact(tmp_path):
    catalog, policy = _write_inputs(tmp_path)
    result = select_experimental_tier("larger", catalog, policy)
    assert result["label"] == "larger_16E"
    assert result["status"] == "EXPERIMENTAL_ONLY"
    assert result["learned_routing"] == "DISABLE"

    bad_catalog, bad_policy = _write_inputs(tmp_path / "bad", learned_routing="ENABLE")
    with pytest.raises(TierSelectionError, match="DISABLE"):
        select_experimental_tier("compact", bad_catalog, bad_policy)


def test_select_experimental_tier_rejects_unknown_or_missing_artifact(tmp_path):
    catalog, policy = _write_inputs(tmp_path, artifact_exists=False)
    with pytest.raises(TierSelectionError, match="not present"):
        select_experimental_tier("compact", catalog, policy)
    with pytest.raises(TierSelectionError, match="preference"):
        select_experimental_tier("production", catalog, policy)
