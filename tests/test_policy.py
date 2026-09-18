import json
from pathlib import Path


def test_learned_routing_is_explicitly_disabled_until_release_gates():
    policy_path = Path(__file__).resolve().parents[1] / "config" / "wrench-routing-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    assert policy["schema"] == "wrench.routing-policy.v1"
    assert policy["learned_routing"] == "DISABLE"
    assert policy["fallback"] == "stronger_model_path"
    assert policy["quality_claim"] is False
    assert "approved_real_workflow_traces" in policy["enablement_requires"]
