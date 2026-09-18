"""Schema- and hash-bound persistence for the routing guard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .router import ProposalRouter, RouterConfig


SCHEMA = "wrench.router-state.v1"


def save_router_state(router: ProposalRouter, path: str | Path) -> dict[str, Any]:
    """Persist a small router snapshot with an atomic same-directory replace."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    state = {"schema": SCHEMA, **router.status()}
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    return state


def load_router_state(config: RouterConfig, path: str | Path) -> ProposalRouter:
    """Restore only a valid state whose configuration hash matches exactly."""

    target = Path(path)
    try:
        state = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("router state unreadable") from exc
    if not isinstance(state, dict) or state.get("schema") != SCHEMA:
        raise ValueError("router state schema mismatch")
    if state.get("config_hash") != config.config_hash:
        raise ValueError("router state configuration hash mismatch")
    fields = ("attempts", "failures", "enabled", "circuit_open")
    if any(field not in state for field in fields):
        raise ValueError("router state fields missing")
    if not all(isinstance(state[field], int) and not isinstance(state[field], bool) and state[field] >= 0 for field in fields[:2]):
        raise ValueError("router state counters invalid")
    if not all(isinstance(state[field], bool) for field in fields[2:]):
        raise ValueError("router state flags invalid")
    router = ProposalRouter(config)
    router.attempts = state["attempts"]
    router.failures = state["failures"]
    router.enabled = state["enabled"]
    router.circuit_open = state["circuit_open"]
    router.bypass_reason = state.get("bypass_reason") if isinstance(state.get("bypass_reason"), str) else None
    return router
