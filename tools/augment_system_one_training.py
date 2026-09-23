"""Expand authored unsealed classifier training contrasts with disjoint paths.

This reads no evaluation prompts or labels. The held-out 5k suite's path
inventory is used only to keep training file names separate from test paths.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "phases/system-one-readiness-20260922/contrast-training.jsonl"
SUITE_MANIFEST = ROOT / "phases/system-one-binary-5k-20260922/manifest.json"
OUTPUT = ROOT / "phases/system-one-training-augmented-20260922"
PATH_TOKENS = (
    "docs/key-management.md", "docs/commands.md", "docs/security.md", "docs/policy.md",
    "docs/manual.md", "docs/theme.md", "docs/usage.md", "docs/setup.md",
    "docs/guide.md", "docs/help.md", "docs/logs.txt", "scripts/remove-old.py",
    "src/main.py", "src/help.py", "notes.md", "notes.txt", "config.txt", "README.md",
)
PATTERN = re.compile("|".join(re.escape(item) for item in sorted(PATH_TOKENS, key=len, reverse=True)))


def replacements() -> list[str]:
    excluded = set(json.loads(SUITE_MANIFEST.read_text(encoding="utf-8"))["tracked_paths"])
    completed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True)
    candidates = []
    for relative in completed.stdout.decode("utf-8").split("\0"):
        if not relative or relative in excluded or relative.startswith("docs/archive/"):
            continue
        path = ROOT / relative
        if (path.is_file() and path.suffix in {".py", ".md", ".json", ".toml"}
                and path.stat().st_size <= 100_000 and relative.startswith(("src/", "docs/", "tests/", "examples/"))):
            candidates.append(relative.replace("\\", "/"))
    candidates.sort(key=lambda item: hashlib.sha256(("train-v1:" + item).encode()).digest())
    if len(candidates) < 12:
        raise ValueError("not enough distinct training paths")
    return candidates[:12]


def main():
    if OUTPUT.exists():
        raise FileExistsError("preserve prior training expansion; choose a new output version")
    paths = replacements()
    rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    expanded = []
    for row in rows:
        expanded.append(row)
        if not PATTERN.search(row["prompt"]):
            continue
        for index, path in enumerate(paths):
            candidate = dict(row)
            candidate["id"] = f"{row['id']}-aug-{index:02d}"
            candidate["prompt"] = PATTERN.sub(path, row["prompt"])
            if candidate["prompt"] != row["prompt"]:
                expanded.append(candidate)
    normalized = [" ".join(row["prompt"].casefold().split()) for row in expanded]
    if len(normalized) != len(set(normalized)):
        raise ValueError("expanded training has duplicate prompts")
    if any(row.get("split") != "training" or row["expected_status"] not in {"accepted", "abstain"}
           or not row["template_id"].startswith("extra_template_") or len(row["prompt"]) > 4096 for row in expanded):
        raise ValueError("invalid expanded training case")
    OUTPUT.mkdir(parents=True)
    dest = OUTPUT / "train-extra.jsonl"
    with dest.open("x", encoding="utf-8", newline="\n") as stream:
        for row in expanded:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    manifest = {"schema": "wrench.system-one-training-expansion.v1",
                "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                "expanded_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                "rows": len(expanded), "labels": dict(Counter(row["expected_status"] for row in expanded)),
                "groups": len({row["template_id"] for row in expanded}),
                "substitution_paths": paths, "test_prompts_read": False, "final_split_read": False,
                "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": manifest["rows"], "labels": manifest["labels"], "groups": manifest["groups"],
                      "sha256": manifest["expanded_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
