"""Independent structural and oracle-boundary audit for the 5k binary suite."""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "phases/system-one-binary-5k-20260922"
TRAIN = ROOT / "phases/system-one-training-augmented-20260922/train-extra.jsonl"
OTHER_UNSEALED = (
    ROOT / "phases/system-one-readiness-20260922/evaluation.jsonl",
    ROOT / "evals/wrench-expanded-v2/calibration.jsonl",
    ROOT / "evals/wrench-expanded-v2/development.jsonl",
)
ELIGIBLE = {"read_file", "read_lines", "literal_search", "git_read_status", "health_read", "patch_draft"}


def rows(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalized(prompt: str):
    return " ".join(prompt.casefold().split())


def main():
    manifest = json.loads((SUITE / "manifest.json").read_text(encoding="utf-8"))
    raw = (SUITE / "cases.jsonl").read_bytes()
    cases = rows(SUITE / "cases.jsonl")
    assert hashlib.sha256(raw).hexdigest() == manifest["cases_sha256"]
    assert hashlib.sha256((ROOT / "tools/build_system_one_5k_suite.py").read_bytes()).hexdigest() == manifest["generator_sha256"]
    assert Counter(case["label"] for case in cases) == {"abstain": 5000, "wrench": 600}
    assert dict(Counter(case["category"] for case in cases)) == manifest["categories"]
    assert len({case["id"] for case in cases}) == len(cases) == 5600
    prompts = [normalized(case["prompt"]) for case in cases]
    assert len(set(prompts)) == len(prompts)
    groups = defaultdict(list)
    for case in cases:
        groups[(case["label"], case["pattern_group"])].append(case)
        assert (case["category"] in ELIGIBLE) == (case["label"] == "wrench")
        assert 15 <= len(case["prompt"]) <= 900
    assert len(groups) == 160
    assert Counter(len(group) for group in groups.values()) == {50: 100, 10: 60}
    positive_paths = set()
    for case in cases:
        if case["label"] != "wrench":
            continue
        category, target = case["category"], case["target"]
        if category in {"read_file", "read_lines", "literal_search", "patch_draft"}:
            path = (ROOT / target).resolve()
            assert path.is_relative_to(ROOT.resolve()) and path.is_file(), case["id"]
            positive_paths.add(target)
        if category == "read_file":
            assert (ROOT / target).stat().st_size <= 262144, case["id"]
        elif category == "read_lines":
            numbers = [int(value) for value in re.findall(r"\b\d+\b", case["prompt"].replace(target, ""))]
            assert len(numbers) == 2 and 1 <= numbers[0] <= numbers[1] and numbers[1] - numbers[0] + 1 <= 500, case["id"]
            assert numbers[1] <= len((ROOT / target).read_text(encoding="utf-8").splitlines()), case["id"]
        elif category == "git_read_status":
            assert "untracked" not in case["prompt"].casefold(), case["id"]
        elif category == "health_read":
            assert target == "http://localhost:4000/health" and target in case["prompt"], case["id"]
        elif category == "patch_draft":
            quoted = re.findall(r"'([^']+)'", case["prompt"])
            assert quoted and any(text in (ROOT / target).read_text(encoding="utf-8") for text in quoted), case["id"]
    overlaps = {}
    prompt_set = set(prompts)
    for path in (TRAIN, *OTHER_UNSEALED):
        overlap = prompt_set & {normalized(row["prompt"]) for row in rows(path)}
        overlaps[str(path.relative_to(ROOT))] = len(overlap)
        assert not overlap, str(path)
    report = {"schema": "wrench.system-one-5k-audit.v1",
              "status": "STRUCTURAL_PASS_HUMAN_LABEL_REVIEW_PENDING",
              "cases_sha256": manifest["cases_sha256"],
              "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "rows": len(cases), "labels": dict(Counter(case["label"] for case in cases)),
              "categories": manifest["categories"], "pattern_groups": len(groups),
              "positive_tracked_files_checked": len(positive_paths),
              "non_ascii_prompts": sum(any(ord(char) > 127 for char in case["prompt"]) for case in cases),
              "exact_prompt_overlaps_with_unsealed_sources": overlaps,
              "sealed_final_read": False, "model_calls": 0, "tool_actions": 0,
              "limitation": "Structural checks and generated oracle metadata do not replace human review of realistic task labels"}
    with (SUITE / "audit.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
