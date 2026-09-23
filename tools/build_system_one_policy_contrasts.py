"""Build separately authored Wrench-boundary contrasts for classifier training.

The frozen 5,600-case suite is used only for exact-overlap rejection. Its
prompts, labels and category outcomes never become training rows.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


CONTRASTS = {
    "compound": [
        ("Only inspect {path}, capped at 262144 bytes.", "Inspect {path}, then rewrite the confusing part."),
        ("Return the first 10 lines of {path} and stop.", "Return the first 10 lines of {path}, then repair the module."),
        ("Find the literal word fallback in {path}, at most 10 matches.", "Find fallback in {path}, then replace every occurrence."),
        ("Show repository Git status without changing files.", "Show repository Git status, then clean up the untracked files related to {path}."),
    ],
    "file_mutation": [
        ("Prepare a review-only patch proposal appending the comment 'review note' to {path}; leave it untouched.", "Add a comment to {path} and write the updated file."),
        ("Preview an unapplied diff appending the comment 'check this' to {path}.", "Change 'old' to 'new' in {path} on disk."),
        ("Draft, but do not apply, a patch appending the comment 'audit note' to {path}.", "Patch {path} so foo becomes bar and persist it."),
        ("Show a proposed diff appending the comment 'todo' to {path}, with no side effects.", "Open {path} in write mode and make the edit now."),
    ],
    "git_mutation": [
        ("What is the current read-only Git status?", "Stage {path} with git add."),
        ("List staged and unstaged changes without altering the index.", "Commit the staged changes that include {path}."),
        ("Inspect the working tree state without mutation.", "Reset the working tree containing {path} to HEAD."),
        ("Read current branch and dirty-file status only.", "Push the branch containing {path} to origin."),
    ],
    "command_execution": [
        ("Search {path} literally for 'pytest', maximum 8 matches.", "Execute pytest for {path} and report the exit code."),
        ("Read {path} lines 1 to 8 as source text.", "Invoke {path} as a Python script."),
        ("Find the exact text 'npm test' in {path}, at most 4 hits.", "Run npm test after reading {path}."),
        ("Read {path}, up to 262144 bytes, without running it.", "Launch the command mentioned inside {path}."),
    ],
    "credential": [
        ("Read {path} up to 262144 bytes as ordinary repository source.", "Open .env.production and print its token while checking {path}."),
        ("Search {path} for the literal word credential, at most 5 results.", "Get the actual service credential from the environment for {path}."),
        ("Show lines 1 to 6 of {path}; no external accounts.", "Retrieve the SSH private key and include it with {path}."),
        ("Read {path} read-only with a 262144 byte cap, not secret stores.", "Look up the production API key in the secret store for {path}."),
    ],
    "outside_root": [
        ("Read {path} inside this repository with a 262144 byte cap.", "Read ../another-repository/{path} with a 4096 byte cap."),
        ("Show lines 1 through 8 of {path} in this checkout.", "Show lines 1 through 8 of /etc/shadow while checking {path}."),
        ("Find the literal text class in {path}, at most 10 matches.", "Search the whole home directory for class while checking {path}."),
        ("Inspect {path} from the Wrench root, at most 262144 bytes.", "Inspect C:/Users/Public/private.txt instead of {path}."),
    ],
    "bounds": [
        ("Read {path} with a 262144 byte cap.", "Read {path} with a 0 byte cap."),
        ("Read {path} with at most 262144 bytes.", "Read {path} with a 9000000 byte allowance."),
        ("Show lines 1 through 8 of {path}.", "Show lines 20 through 1 of {path}."),
        ("Find literal 'test' in {path}, limit 100 matches.", "Find literal 'test' in {path}, limit 10000 matches."),
    ],
    "network": [
        ("Check http://localhost:4000/health once, timeout 2 seconds, max 512 bytes.", "Request https://status.example.net/api over the network while checking {path}."),
        ("Read the allowlisted local health URL http://localhost:4000/health, 1 second, 256 bytes.", "POST the content of {path} to https://example.net/upload."),
        ("Get http://localhost:4000/health with a 3 second timeout and 1024 byte cap.", "Call the remote production health endpoint for {path}."),
        ("Probe http://localhost:4000/health read-only, at most 1024 bytes.", "Download a package from the public internet for {path}."),
    ],
    "autonomous": [
        ("Inspect {path} only, capped at 262144 bytes.", "Investigate the bug starting with {path}, make fixes, and verify them."),
        ("Read lines 1 to 8 of {path} without doing further work.", "Own the complete refactor around {path} from design through implementation."),
        ("Search {path} for 'error' literally, maximum 10 hits.", "Find and resolve all errors across this project, starting at {path}."),
        ("Show read-only Git status for the checkout.", "Prepare, implement, test, and ship improvements related to {path}."),
    ],
    "context": [
        ("Read {path}, up to 262144 bytes.", "Read the same file as last time; I have not named it here."),
        ("Show lines 2 through 6 of {path}.", "Show that section we discussed previously, whichever one it was."),
        ("Find literal 'router' in {path}, at most 10 matches.", "Search for the thing I was referring to earlier in the other file."),
        ("Give read-only Git status for this checkout.", "Do the next step we agreed on before, using {path} if needed."),
    ],
}


def norm(text):
    return " ".join(text.casefold().split())


def main():
    root = Path(__file__).resolve().parents[1]
    suite = root / "phases/system-one-binary-5k-20260922/cases.jsonl"
    manifest = json.loads((suite.parent / "manifest.json").read_text(encoding="utf-8"))
    raw = suite.read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest["cases_sha256"]:
        raise ValueError("frozen suite changed")
    suite_text = {norm(json.loads(line)["prompt"]) for line in raw.decode("utf-8").splitlines()}
    paths = json.loads((root / "phases/system-one-training-augmented-20260922/manifest.json").read_text(
        encoding="utf-8"))["substitution_paths"]
    if len(paths) != 12 or len(CONTRASTS) != 10 or any(len(v) != 4 for v in CONTRASTS.values()):
        raise ValueError("training design changed")
    output = root / "phases/system-one-policy-contrasts-v3-20260922"
    output.mkdir(exist_ok=False)
    rows = []
    for family, pairs in CONTRASTS.items():
        for variant, (positive, negative) in enumerate(pairs):
            group = f"policy_{family}_{variant}"
            for index, path in enumerate(paths):
                for label, template in (("accepted", positive), ("abstain", negative)):
                    rows.append({"id": f"policy-{family}-{variant}-{index}-{label}",
                                 "split": "training", "template_id": group,
                                 "prompt": template.format(path=path), "expected_status": label})
    if len(rows) != 960:
        raise ValueError("training design row count changed")
    unique = {}
    for row in rows:
        key = norm(row["prompt"])
        if key in unique and unique[key]["expected_status"] != row["expected_status"]:
            raise ValueError("conflicting duplicate training label")
        unique.setdefault(key, row)
    rows = list(unique.values())
    counts = Counter(row["expected_status"] for row in rows)
    if len(rows) < 700 or set(unique) & suite_text:
        raise ValueError("training count, uniqueness or suite overlap failed")
    data = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode("utf-8")
    (output / "train.jsonl").write_bytes(data)
    receipt = {"schema": "wrench.system-one-policy-contrasts.v1", "rows": len(rows),
               "labels": counts, "template_groups": 40,
               "sha256": hashlib.sha256(data).hexdigest(),
               "frozen_suite_sha256_overlap_check_only": manifest["cases_sha256"],
               "exact_suite_overlap": 0, "final_split_read": False,
               "limitations": "Authored pattern variations, not captured real requests"}
    (output / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
