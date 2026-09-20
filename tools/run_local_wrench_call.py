"""Execute one bounded Wrench HTTP call in a killable child process."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from wrench_harness import execute_local_qwen


def main() -> int:
    request = json.loads(sys.stdin.read())
    result = execute_local_qwen(
        request["endpoint"],
        request["model"],
        request["messages"],
        request["root"],
        max_tokens=int(request["max_tokens"]),
        timeout_seconds=float(request["timeout"]),
        capture_trace=True,
        mechanical_fast_path=True,
    )
    sys.stdout.write(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
