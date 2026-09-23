"""Audit the replacement synthetic 5k suite without reading any sealed split."""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "phases/system-one-replacement-5k-20260923"
OLD = ROOT / "phases/system-one-binary-5k-20260922"
TRAIN = (OLD / "cases.jsonl",
         ROOT / "phases/system-one-policy-contrasts-v3-20260922/train.jsonl",
         ROOT / "evals/wrench-expanded-v2/calibration.jsonl")
POSITIVE = {"read_file", "read_lines", "literal_search", "git_read_status",
            "health_read", "patch_draft"}


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def normalized(prompt: str) -> str:
    return " ".join(prompt.casefold().split())


def main() -> None:
    manifest = json.loads((SUITE / "manifest.json").read_text(encoding="utf-8"))
    cases_path = SUITE / "cases.jsonl"
    if hashlib.sha256(cases_path.read_bytes()).hexdigest() != manifest["cases_sha256"]:
        raise ValueError("replacement case hash mismatch")
    if hashlib.sha256((ROOT / "tools/build_system_one_replacement_5k.py").read_bytes()).hexdigest() != manifest["generator_sha256"]:
        raise ValueError("replacement generator hash mismatch")
    cases = rows(cases_path)
    if (len(cases) != 5600 or Counter(case["label"] for case in cases)
            != {"abstain": 5000, "wrench": 600}
            or len({case["id"] for case in cases}) != 5600):
        raise ValueError("replacement inventory mismatch")
    groups = defaultdict(list)
    for case in cases:
        groups[(case["label"], case["pattern_group"])].append(case)
        if (case["category"] in POSITIVE) != (case["label"] == "wrench"):
            raise ValueError(f"category/label mismatch: {case['id']}")
        if not 15 <= len(case["prompt"]) <= 900:
            raise ValueError(f"prompt length invalid: {case['id']}")
    if len(groups) != 160 or Counter(map(len, groups.values())) != {50: 100, 10: 60}:
        raise ValueError("replacement group inventory mismatch")
    prompts = {normalized(case["prompt"]) for case in cases}
    if len(prompts) != 5600:
        raise ValueError("duplicate replacement prompts")
    overlaps = {}
    for path in TRAIN:
        intersect = prompts & {normalized(row["prompt"]) for row in rows(path)}
        overlaps[str(path.relative_to(ROOT))] = len(intersect)
        if intersect:
            raise ValueError(f"training overlap: {path}")
    old_manifest = json.loads((OLD / "manifest.json").read_text(encoding="utf-8"))
    old_paths = set(old_manifest["tracked_paths"])
    if old_paths & set(manifest["tracked_paths"]):
        raise ValueError("replacement path inventory overlaps retired suite")
    checked_paths = set()
    for case in cases:
        if case["label"] != "wrench":
            continue
        category = case["category"]
        target = case["target"]
        if category in {"read_file", "read_lines", "literal_search", "patch_draft"}:
            path = (ROOT / target).resolve()
            if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
                raise ValueError(f"eligible target unavailable: {case['id']}")
            checked_paths.add(target)
        if category == "read_file" and (ROOT / target).stat().st_size > 262144:
            raise ValueError(f"eligible read exceeds Wrench cap: {case['id']}")
        if category == "read_lines":
            values = [int(v) for v in re.findall(r"\b\d+\b", case["prompt"].replace(target, ""))]
            if (len(values) != 2 or values[0] < 1 or values[1] < values[0]
                    or values[1] - values[0] + 1 > 500
                    or values[1] > len((ROOT / target).read_text(encoding="utf-8").splitlines())):
                raise ValueError(f"eligible line range invalid: {case['id']}")
        if category == "patch_draft" and "return" not in (ROOT / target).read_text(encoding="utf-8"):
            raise ValueError(f"patch source missing: {case['id']}")
        if category == "health_read" and target not in {
                "http://localhost:4000/health", "http://127.0.0.1:4000/v1/models"}:
            raise ValueError(f"health URL outside allowlist: {case['id']}")
    report = {"schema": "wrench.system-one-replacement-audit.v1",
              "status": "STRUCTURAL_PASS_HUMAN_LABEL_REVIEW_PENDING",
              "cases_sha256": manifest["cases_sha256"],
              "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "rows": len(cases), "labels": dict(Counter(case["label"] for case in cases)),
              "categories": dict(Counter(case["category"] for case in cases)),
              "pattern_groups": len(groups), "positive_tracked_files_checked": len(checked_paths),
              "non_ascii_prompts": sum(any(ord(c) > 127 for c in case["prompt"]) for case in cases),
              "exact_prompt_overlaps_with_training": overlaps,
              "prior_path_overlap": 0, "sealed_final_read": False,
              "model_calls": 0, "tool_actions": 0,
              "limitation": "Authored patterns and structural checks do not prove human label quality or real-workflow accuracy"}
    path = SUITE / "audit.json"
    if path.exists():
        raise ValueError("preserve existing audit")
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "rows", "labels",
                                                   "pattern_groups", "positive_tracked_files_checked",
                                                   "exact_prompt_overlaps_with_training")}, indent=2))


if __name__ == "__main__":
    main()
