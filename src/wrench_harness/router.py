"""Bounded routing control around the proposal verifier."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable


def _stable_hash(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class RouterConfig:
    max_attempts: int = 1
    failure_threshold: int = 2
    config_version: str = "wrench-router-v1"

    @property
    def config_hash(self) -> str:
        return _stable_hash({
            "max_attempts": self.max_attempts,
            "failure_threshold": self.failure_threshold,
            "config_version": self.config_version,
        })


class CancellationToken:
    """Cooperative cancellation signal checked before and after one attempt."""

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled


class ProposalRouter:
    """Run bounded proposal attempts and fail closed when the circuit opens."""

    def __init__(self, config: RouterConfig = RouterConfig(), event_sink: Callable[[dict[str, Any]], None] | None = None):
        if config.max_attempts < 1 or config.failure_threshold < 1:
            raise ValueError("router ceilings must be positive")
        self.config = config
        self.attempts = 0
        self.failures = 0
        self.enabled = True
        self.circuit_open = False
        self.bypass_reason: str | None = None
        self.event_sink = event_sink

    def _emit(self, event: str, **fields: Any) -> None:
        if self.event_sink is None:
            return
        try:
            self.event_sink({"event": event, **fields})
        except Exception:  # noqa: BLE001
            return

    def run(self, invoke: Callable[[], dict[str, Any]], cancellation: CancellationToken | None = None) -> dict[str, Any]:
        if cancellation is not None and cancellation.cancelled:
            self._emit("cancelled", stage="before_attempt")
            return {"status": "abstain", "fallback_reason": "cancelled"}
        if not self.enabled:
            return {"status": "abstain", "fallback_reason": "router_disabled", "circuit_open": self.circuit_open}
        if self.attempts >= self.config.max_attempts:
            return {"status": "abstain", "fallback_reason": "attempt_ceiling", "circuit_open": self.circuit_open}
        self.attempts += 1
        try:
            result = invoke()
        except Exception as exc:  # noqa: BLE001
            result = {"status": "abstain", "fallback_reason": "router_invocation_error", "detail": type(exc).__name__}
        if cancellation is not None and cancellation.cancelled:
            self._emit("cancelled", stage="after_attempt")
            return {"status": "abstain", "fallback_reason": "cancelled"}
        if not isinstance(result, dict) or result.get("status") != "accepted":
            self.failures += 1
            if self.failures >= self.config.failure_threshold:
                self.enabled = False
                self.circuit_open = True
                self._emit("circuit_opened", failures=self.failures)
                if isinstance(result, dict):
                    result = {**result, "circuit_opened": True}
        return result

    def bypass(self, reason: str = "operator_bypass") -> None:
        self.enabled = False
        self.bypass_reason = reason
        self._emit("bypass", reason=reason)

    def reset(self, config_hash: str) -> bool:
        if config_hash != self.config.config_hash:
            return False
        self.attempts = 0
        self.failures = 0
        self.enabled = True
        self.circuit_open = False
        self.bypass_reason = None
        self._emit("reset")
        return True

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "circuit_open": self.circuit_open,
            "attempts": self.attempts,
            "failures": self.failures,
            "max_attempts": self.config.max_attempts,
            "failure_threshold": self.config.failure_threshold,
            "config_hash": self.config.config_hash,
            "bypass_reason": self.bypass_reason,
        }
