"""Fail closed for provider calls until budget enforcement and receipts exist."""

from __future__ import annotations

import json
import sys


LIVE_CALLS_DISABLED = (
    "live_teacher_calls_disabled_until_aggregate_budget_and_durable_usage_receipts_are_enforced"
)


def main() -> int:
    """Reject the old child-call protocol without parsing or sending its request."""

    sys.stdout.write(json.dumps({"ok": False, "error": LIVE_CALLS_DISABLED}) + "\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
