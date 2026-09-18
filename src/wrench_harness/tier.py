"""Fail-closed selection of verified experimental Wrench model tiers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TierSelectionError(ValueError):
    """Raised when a tier catalog or rollout policy is not safe to use."""


_PREFERENCES = {
    "compact": "compact_8E_safety",
    "larger": "larger_16E",
}


def select_experimental_tier(
    preference: str,
    catalog_path: str | Path,
    policy_path: str | Path,
) -> dict[str, Any]:
    """Resolve one catalog tier without enabling learned routing or production use."""

    label = _PREFERENCES.get(preference)
    if label is None:
        raise TierSelectionError("tier preference must be 'compact' or 'larger'")
    try:
        catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
        policy = json.loads(Path(policy_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TierSelectionError("tier catalog or routing policy is unreadable") from exc
    if catalog.get("schema") != "wrench.dual-tier-model-catalog.v1":
        raise TierSelectionError("tier catalog schema mismatch")
    if catalog.get("status") != "EXPERIMENTAL_TWO_TIER_ARTIFACTS_VERIFIED" or catalog.get("quality_claim") is not False:
        raise TierSelectionError("tier catalog is not an experimental verified catalog")
    if policy.get("schema") != "wrench.routing-policy.v1" or policy.get("learned_routing") != "DISABLE":
        raise TierSelectionError("learned routing must remain DISABLE")
    rows = [row for row in catalog.get("tiers", []) if isinstance(row, dict) and row.get("label") == label]
    if len(rows) != 1:
        raise TierSelectionError(f"catalog tier missing or ambiguous: {label}")
    row = rows[0]
    artifact = row.get("artifact")
    if not isinstance(artifact, str) or not Path(artifact).is_dir():
        raise TierSelectionError(f"tier artifact is not present: {label}")
    return {
        "status": "EXPERIMENTAL_ONLY",
        "label": label,
        "artifact": artifact,
        "parameter_count": row.get("parameter_count"),
        "packed_weight_gib": row.get("packed_weight_gib"),
        "directory_gib": row.get("directory_gib"),
        "num_experts": row.get("num_experts"),
        "fallback": policy.get("fallback"),
        "learned_routing": policy.get("learned_routing"),
        "quality_claim": False,
    }
