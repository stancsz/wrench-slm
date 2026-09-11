"""Gate the frozen selective pilot on trusted-data readiness.

This wrapper does not change the frozen runner or authorize spending by itself.
It requires a passing readiness receipt, then forwards the remaining arguments
to ``selective_pilot_run.py``. Use the frozen runner directly only for the
documented zero-provider dry-run.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.verify_trusted_readiness import verify


RUNNER = ROOT / "scripts" / "selective_pilot_run.py"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trusted-readiness-receipt", required=True, type=Path)
    parser.add_argument(
        "runner_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to selective_pilot_run.py after the readiness gate",
    )
    args = parser.parse_args()
    if not args.runner_args:
        parser.error("runner arguments are required after --trusted-readiness-receipt")
    result = verify(args.trusted_readiness_receipt)
    if result["status"] != "PASS":
        print("Trusted-data readiness rejected; frozen runner was not started.")
        print(result)
        return 1
    command = [sys.executable, str(RUNNER), *args.runner_args]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
