from __future__ import annotations

import json
from pathlib import Path

import pytest

from wrench_harness import ProposalRouter, RouterConfig, load_router_state, save_router_state


@pytest.mark.parametrize(
    "overrides",
    [
        {"attempts": 4},
        {"attempts": 0, "failures": 1},
        {"attempts": 2, "failures": 2},
        {"enabled": True, "circuit_open": True, "failures": 2},
        {"enabled": False, "circuit_open": True, "failures": 1},
        {"enabled": False, "circuit_open": False, "bypass_reason": None},
        {"bypass_reason": "maintenance"},
        {"bypass_reason": 17},
    ],
)
def test_router_state_rejects_impossible_or_malformed_snapshots(
    tmp_path: Path, overrides: dict[str, object]
):
    config = RouterConfig(max_attempts=3, failure_threshold=2)
    router = ProposalRouter(config)
    router.run(lambda: {"status": "abstain", "fallback_reason": "test"})
    state_path = tmp_path / "router-state.json"
    save_router_state(router, state_path)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update(overrides)
    state_path.write_text(json.dumps(state), encoding="utf-8")

    with pytest.raises(ValueError, match="router state"):
        load_router_state(config, state_path)


def test_open_circuit_survives_router_restart_until_hash_bound_reset(tmp_path: Path):
    config = RouterConfig(max_attempts=3, failure_threshold=2)
    router = ProposalRouter(config)

    def reject():
        return {"status": "abstain", "fallback_reason": "test"}

    router.run(reject)
    opened = router.run(reject)
    assert opened["circuit_opened"] is True

    state_path = tmp_path / "router-state.json"
    save_router_state(router, state_path)
    restored = load_router_state(config, state_path)

    assert restored.status() == router.status()
    invoked = False

    def should_not_run():
        nonlocal invoked
        invoked = True
        return {"status": "accepted"}

    assert restored.run(should_not_run)["fallback_reason"] == "router_disabled"
    assert not invoked
    assert restored.reset(config.config_hash)
    assert restored.run(lambda: {"status": "accepted"})["status"] == "accepted"


def test_operator_bypass_survives_router_restart(tmp_path: Path):
    config = RouterConfig(max_attempts=3, failure_threshold=2)
    router = ProposalRouter(config)
    router.bypass("maintenance")
    state_path = tmp_path / "router-state.json"
    save_router_state(router, state_path)

    restored = load_router_state(config, state_path)
    assert restored.status() == router.status()
    assert restored.run(lambda: {"status": "accepted"})["fallback_reason"] == "router_disabled"
