"""Create one paired, metadata-only production-source readiness receipt."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.discover_production_sources import discover
from scripts.profile_production_usage import profile, read_events


def build(source: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    discovery = discover(source, output / "source-discovery")
    usage = profile(read_events(source))
    reasons = []
    if not discovery["replay_capabilities"]["has_prompt_field"] or not discovery["replay_capabilities"]["has_context_field"]:
        reasons.append("MISSING_PROMPT_OR_CONTEXT")
    if usage["cost_status"] != "CALCULATED":
        reasons.append("PRICE_LEDGER_REQUIRED")
    if usage["duration_unit_status"] != "UNVERIFIED_SECONDS":
        reasons.append("DURATION_UNIT_UNVERIFIED_OR_OUTLIER")
    paired = {
        "schema": "production-readiness-receipt-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source.resolve()),
        "read_only": True,
        "raw_content_written": False,
        "source_event_records": discovery["event_json_records"],
        "profile_events": usage["events"],
        "event_count_match": discovery["event_json_records"] == usage["events"],
        "replay_ready": discovery["replay_ready"],
        "readiness_reasons": reasons,
        "replay_capabilities": discovery["replay_capabilities"],
        "usage_coverage": usage["usage_coverage"],
        "cost_status": usage["cost_status"],
        "duration_unit_status": usage["duration_unit_status"],
        "evidence_boundary": "Metadata-only source and usage readiness; not semantic replay or production savings evidence.",
    }
    (output / "usage-profile.json").write_text(json.dumps(usage, indent=2, ensure_ascii=False), encoding="utf-8")
    (output / "receipt.json").write_text(json.dumps(paired, indent=2, ensure_ascii=False), encoding="utf-8")
    return paired


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
