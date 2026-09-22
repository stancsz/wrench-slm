"""A no-model introduction to Wrench's actual proposal verifier.

Run from an installed source checkout: python examples/local_first.py
Creates and removes its own temporary fixture; makes no network requests.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from wrench_harness import execute_proposal


def run_demo():
    with TemporaryDirectory(prefix="wrench-example-") as directory:
        root = Path(directory)
        fixture = root / "settings.txt"
        fixture.write_text("timeout=30\nretries=2\n", encoding="utf-8")
        before = fixture.read_bytes()
        cases = [
            ("Read a setting", {"action": "read_lines", "path": "settings.txt", "start": 1, "end": 1}),
            ("Stay inside the workspace", {"action": "read_file", "path": "../outside.txt"}),
            ("Decline shell execution", {"action": "shell", "command": "echo hello"}),
        ]
        results = []
        for title, fields in cases:
            proposal = {"schema": "wrench.proposal.v1", **fields}
            result = execute_proposal(proposal, root)
            # Make the receipt portable without exposing a machine-specific path.
            observation = result.get("observation", {})
            if "path" in observation:
                observation["path"] = Path(observation["path"]).name
            results.append({"title": title, "proposal": proposal, "result": result})
        assert results[0]["result"]["observation"]["lines"] == ["timeout=30"]
        assert results[1]["result"]["fallback_reason"] == "path_outside_allowed_root"
        assert results[2]["result"]["fallback_reason"] == "action_not_allowlisted"
        assert fixture.read_bytes() == before, "The fixture must remain unchanged"
        return {"scope": "Direct verifier example; no model, cloud call, or savings benchmark.", "cases": results, "fixture_unchanged": True}


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2))
