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
        mechanical_fast_path=bool(request.get("mechanical_fast_path", True)),
    )
    # Windows worker subprocesses may inherit a cp1252 stdout. The model
    # package is allowed to read UTF-8 repository content, so writing the JSON
    # envelope through the text stream can crash on box-drawing or non-Latin
    # characters. Keep the child protocol byte-stable and UTF-8 everywhere.
    payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
