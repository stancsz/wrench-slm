#!/usr/bin/env python3
"""Build a prompt-complete 220-case mechanical contract.

The historical 220-case fixture is retained unchanged. This derived contract
keeps the same family and split shape, but makes every eligible request
executable from its prompt. In particular, health bounds are stated exactly
and patch requests contain an explicit bounded text operation. It is a
mechanical-route contract, not a teacher-parity or production benchmark.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from generate_expanded_evaluation import build as build_historical_shape
from wrench_harness.mechanical import mechanical_route


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_fixture(root: Path) -> None:
    if root.exists():
        raise FileExistsError(f"refusing to overwrite fixture: {root}")
    root.mkdir(parents=True)
    files = {
        "README.md": "README fixture\nstatus marker\nrouter verifier selection\n",
        "GOAL.md": "GOAL fixture\nprohibited quality_claim parameter_count\n",
        "docs/PROJECT_PLAN.md": "PROJECT_PLAN fixture\nfallback_reason verifier\n",
        "dataset/README.md": "DATASET fixture\nEXPERIMENTAL health_read\n",
        "tests/test_harness.py": "def test_fixture():\n    return 'health_read'\n",
        "config/wrench-routing-policy.json": '{"router":"wrench","selection":"bounded"}\n',
        "phases/phase-49-release-gate-audit/README.md": "phase fixture\nparameter_count\n",
        "phases/phase-58-desktop-full-weight-comparison/README.md": "phase fixture\nprohibited\n",
        "src/wrench_harness/core.py": "# core fixture\nfallback_reason verifier\n",
        "pyproject.toml": "[project]\nname = 'wrench-fixture'\n",
        "src/search/fallback.txt": "fallback_reason\nrouter\nverifier\n",
        "phases/search/quality.txt": "quality_claim\nEXPERIMENTAL\nparameter_count\n",
        "docs/search/selection.txt": "selection\nhealth_read\n",
        "tests/search/router.txt": "router\nverifier\nDISABLE\n",
    }
    for relative, content in files.items():
        padded = content + "".join(f"fixture line {index}\n" for index in range(1, 25))
        _write(root / relative, padded)
    completed = subprocess.run(
        ["git", "init", "--quiet", str(root)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"git init failed: {completed.stderr.strip()}")


def _explicit_patch_case(row: dict[str, Any], index: int, fixture: Path) -> None:
    operations = (
        ("replace", f'Replace "old-{index}" with "new-{index}" in files/patch-{index}.txt and leave the file unchanged for review only.', f"old-{index}\nkeep-{index}\n"),
        ("append", f'Append "new-{index}" to files/patch-{index}.txt as an unapplied review-only patch.', f"keep-{index}\n"),
        ("prepend", f'Prepend "new-{index}" to files/patch-{index}.txt, leaving the file unchanged.', f"keep-{index}\n"),
        ("insert", f'Insert "new-{index}" after the unique text "anchor-{index}" in files/patch-{index}.txt for review.', f"before-{index}\nanchor-{index}\nafter-{index}\n"),
        ("remove", f'Remove "obsolete-{index}" from files/patch-{index}.txt and return only a review patch.', f"keep-{index}\nobsolete-{index}\nend-{index}\n"),
    )
    _, prompt, content = operations[index % len(operations)]
    path = fixture / f"files/patch-{index}.txt"
    _write(path, content)
    candidate = mechanical_route(prompt, allowed_root=fixture)
    if not isinstance(candidate, dict) or candidate.get("action") != "patch_draft":
        raise ValueError(f"explicit patch did not route: {row['id']} -> {prompt}")
    row["prompt"] = prompt
    row["target"] = json.dumps(candidate, ensure_ascii=False, separators=(",", ":"))
    row["contract_annotation"] = "prompt_complete_explicit_patch"


def build(output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite output: {output_dir}")
    output_dir.mkdir(parents=True)
    fixture = output_dir / "fixture"
    _build_fixture(fixture)

    rows = [json.loads(json.dumps(row, ensure_ascii=False)) for row in build_historical_shape()]
    eligible_patch = [row for row in rows if row["family"] == "patch_draft" and row["category"] == "eligible"]
    eligible_health = [row for row in rows if row["family"] == "health_read" and row["category"] == "eligible"]
    for index, row in enumerate(eligible_patch):
        _explicit_patch_case(row, index, fixture)
    for row in eligible_health:
        target = json.loads(row["target"])
        row["prompt"] = (
            f"Read the local health endpoint at {target['url']} with a timeout of "
            f"{target['timeout_seconds']} seconds and a {target['max_bytes']} byte response cap."
        )
        row["contract_annotation"] = "prompt_complete_health_bounds"

    payload = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)
    cases_path = output_dir / "cases.jsonl"
    cases_path.write_text(payload, encoding="utf-8")
    receipt = {
        "schema": "wrench.executable-mechanical-contract.v1",
        "status": "BUILT_PROMPT_COMPLETE_MECHANICAL_CONTRACT",
        "historical_shape": "evals/wrench-expanded-v1/cases.jsonl",
        "case_count": len(rows),
        "eligible_case_count": sum(row["category"] == "eligible" for row in rows),
        "explicit_patch_case_count": len(eligible_patch),
        "explicit_health_case_count": len(eligible_health),
        "boundary_case_count": sum(row["category"] == "boundary" for row in rows),
        "out_of_domain_case_count": sum(row["category"] == "out_of_domain" for row in rows),
        "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        "fixture_path": str(fixture.resolve()),
        "fixture_git_repository": (fixture / ".git").is_dir(),
        "sealed_final_split_used_for_training": False,
        "quality_claim": False,
        "release_authorization": False,
        "limitations": [
            "This contract measures the bounded deterministic route, not MiniMax parity.",
            "The fixture is synthetic and does not establish production workflow utility.",
            "Historical 220-case results remain unchanged and are reported separately.",
        ],
    }
    (output_dir / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    receipt = build(args.output_dir.resolve())
    print(json.dumps({key: receipt[key] for key in ("status", "case_count", "eligible_case_count", "explicit_patch_case_count", "explicit_health_case_count")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
