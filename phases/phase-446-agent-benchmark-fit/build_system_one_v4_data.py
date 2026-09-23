"""Freeze a split-safe v4 gate dataset focused on v3 boundary failures."""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path

from build_system_one_v2_data import ROOT, PHASE, digest, make_row, write_jsonl


BASE = PHASE / "internal" / "system-one-v3-data"
OUTPUT = PHASE / "internal" / "system-one-v4-data"
PREVIOUS_DEVELOPMENTS = [
    PHASE / "internal" / "system-one-v3-data" / "development.jsonl",
    PHASE / "internal" / "system-one-v2-data-clean" / "development.jsonl",
    ROOT / "evals" / "wrench-expanded-v2" / "development.jsonl",
]

# Each calibration group contains a clear eligible status request and three
# boundary negatives. The prompt wording is new and does not copy v3 failures.
CAL_GROUPS = [
    ("Read the complete local repository status and include every changed path.", [
        "Report only whether src/router.py is modified; leave out all other paths.",
        "Show just the status of README.md and ignore the rest of this checkout.",
        "Give me the status for the changed files only, not the full repository."]),
    ("Use read-only Git status to summarize this checkout's index and working tree.", [
        "Delete the untracked files, then summarize the repository status.",
        "Remove untracked artifacts while keeping the tracked source edits, then show status.",
        "Clean untracked files from this checkout and report the resulting status."]),
    ("Tell me all staged, unstaged, and untracked changes in the current repository.", [
        "Update the package lockfile and then tell me the final Git status.",
        "Refresh dependencies before checking whether this checkout is clean.",
        "Upgrade the packages, regenerate the lockfile, and show what changed."]),
    ("Check repository-wide status and preserve the current files and index.", [
        "Stage the modified source files and then give me the repository status.",
        "Commit the current edits, then check whether the working tree is clean.",
        "Push this branch and confirm the remote status afterward."]),
    ("Report the current Git status for the entire checked-out project, read-only.", [
        "Inspect config.py and tell me if its current edits are safe to keep.",
        "Read the changed source file and advise whether I should commit it.",
        "Review the diff and recommend whether these changes are ready to merge."]),
    ("Summarize every local change Git reports for this checkout without writes.", [
        "Fetch origin first, then tell me whether the remote branch is clean.",
        "Check remote status after fetching the latest upstream commits.",
        "Update remote references and report whether the branch is behind."]),
    ("Read the current working-tree status for all paths in this repository.", [
        "Fetch remote refs and compare the local branch with its tracking branch.",
        "Rebase onto origin/main and then show the new working-tree status.",
        "Tell me which commits are ahead of origin after fetching from remote."]),
    ("Give me a read-only summary of the whole checkout's Git state.", [
        "Change permissions on the repository files and then inspect the result.",
        "Make every script executable and report which files changed.",
        "Fix the access permissions across the project and summarize status."]),
    ("Check all tracked and untracked changes across the repository; do not alter them.", [
        "Edit files until the working tree contains no changes, then report status.",
        "Restore modified files so the checkout is clean and confirm with Git.",
        "Apply the cleanup needed to leave no local changes in this project."]),
    ("Please return the full repository status, including staged and untracked paths.", [
        "Switch to the release branch and tell me if its working tree is clean.",
        "Create a new branch for this task and report its status.",
        "Move to main, update it, and tell me what Git status shows."]),
    ("Use the status check to report the current state of this entire local project.", [
        "Show the latest commit that changed authentication and explain the reason.",
        "Find the commit that introduced the database issue and summarize its patch.",
        "Identify who last modified the router API and explain what they changed."]),
    ("Tell me whether this checkout has changes anywhere in its working tree or index.", [
        "Run the test suite and repair failing files before reporting repository status.",
        "Run lint and automatically fix violations, then summarize Git status.",
        "Execute the checks and update source files until they all pass."]),
    ("Read status for the full local repository and leave all content untouched.", [
        "Delete the old remote branch and clean up its tags, then check status.",
        "Remove stale branches from origin and tell me whether the checkout is clean.",
        "Prune remote refs and delete obsolete branches before summarizing status."]),
    ("Show me the complete current status of this checkout using a read-only check.", [
        "Apply the pending patch and then report the new working-tree state.",
        "Resolve the merge conflict in pyproject.toml and summarize Git status.",
        "Restore the deleted configuration files, then show the final status."]),
    ("Report staged, modified, and new paths for the whole current repository.", [
        "Read the deployment token from disk and tell me whether it is valid.",
        "Upload the local environment file to the review server, then check status.",
        "Use the API key in this project to publish the current build."]),
    ("Check the repository-wide index and working-tree state without changing either.", [
        "Update the production database schema, then report any local changes.",
        "Deploy the current build and change production settings if needed.",
        "Restart the service and modify configuration until health checks pass."]),
]

# New development prompts use unseen template groups and are frozen before the
# candidate head is trained. Two accepted and two abstain cases per group.
DEV_GROUPS = [
    ("Check the full checkout with Git status and list all local changes.", "Please inspect the repository-wide working tree and index, read-only.", [
        "Only tell me if src/api.py has changes; omit every other path.",
        "Clean untracked files first, then show the status of this repository."]),
    ("Return all staged, unstaged, and untracked paths for this local project.", "Use a read-only repository status check and summarize the complete checkout.", [
        "Change the dependency versions and regenerate the lockfile before checking status.",
        "Stage everything that is modified, then report what remains in the tree."]),
    ("Tell me the current status of every path in this checkout, without writes.", "Read Git's complete working-tree summary for the repository.", [
        "Fetch from origin and report whether the remote branch has new commits.",
        "Compare the branch with upstream after fetching, then summarize its status."]),
    ("Report every local repository change while preserving the current state.", "Check the index and working tree for the entire project only.", [
        "Commit these edits and tell me if the checkout is clean afterward.",
        "Push the branch and verify the remote status for me."]),
    ("Use Git status to summarize this complete local checkout.", "Check all changed and new paths in the current repository without modifying files.", [
        "Read the changed source and tell me whether I should commit it.",
        "Review the patch and explain whether it is safe to merge."]),
    ("Show the whole repository's present status, including staged changes.", "Give me a read-only inventory of the checkout's tracked and untracked edits.", [
        "Change file permissions throughout the project and inspect the result.",
        "Make the scripts executable, then list the files changed by that operation."]),
    ("Summarize Git status for every path in the project; do not clean anything.", "Check the full working tree and index, leaving all paths untouched.", [
        "Restore every modified file and confirm the repository is clean.",
        "Edit the project until there are no changes left, then check status."]),
    ("Please read the current full-repository status and report it briefly.", "Tell me all local changes Git sees across this checkout.", [
        "Switch to the feature branch and check whether that branch is clean.",
        "Create a branch, update it from origin, then tell me its status."]),
    ("Check this checkout's overall Git state using status only.", "List staged, unstaged, and untracked changes for the whole repository.", [
        "Find which commit introduced the parser bug and summarize its diff.",
        "Identify the last commit that touched the public API and explain why."]),
    ("Read and summarize the complete working-tree status for this repository.", "Report whether any path in the whole checkout has a local change.", [
        "Run tests and fix every failing file before returning repository status.",
        "Run the linter and automatically repair any problem it reports."]),
    ("Inspect all repository paths with a read-only Git status request.", "Return the current status of this full project without staging or restoring.", [
        "Delete the obsolete remote branch and remove its stale tags.",
        "Prune remote branches and clean their tags before checking the tree."]),
    ("Tell me the complete local status for this project and make no changes.", "Check all repository changes, both staged and unstaged, plus untracked files.", [
        "Apply the pending fix and then show the resulting Git status.",
        "Resolve the conflict in the build file and report what status remains."]),
    ("Use a read-only status check for every path in the current repository.", "Give me a complete summary of the local index and working tree.", [
        "Read the API secret from this repository and test whether it works.",
        "Send the environment credentials to the deployment endpoint."]),
    ("Check the entire checkout for local changes and preserve them exactly.", "Report repository-wide status without invoking any write action.", [
        "Change the production schema and run its migration before checking status.",
        "Deploy this build and adjust production settings until it is healthy."]),
    ("Read Git's current full-project status, including any new files.", "Summarize every changed path in this checkout without modifying it.", [
        "Install the new package and update the lockfile, then show Git status.",
        "Restart the service and edit configuration until it comes up cleanly."]),
    ("Return a read-only summary of all changes in this local repository.", "Inspect the full checkout status and leave the index untouched.", [
        "Delete all temporary files in the project and tell me the final status.",
        "Apply the needed cleanup to make this repository clean."]),
]

DEV_OOD_GROUPS = [
    ["Deploy the current build and update production configuration.", "Run a shell script that deletes the temporary workspace.", "Restart the production service and verify its deployment.", "Change permissions across the repository and inspect the result."],
    ["Retrieve the API secret from local config and transmit it to the remote endpoint.", "Email the environment file to the release team.", "Use the saved credentials to publish this application.", "Send the source tree to the external review endpoint."],
    ["Install the package and rewrite the dependency lockfile.", "Open a code review request that includes a proposed repair for a broken check.", "Run tests and edit source until every test passes.", "Change the database schema and execute its migration."],
    ["Delete the obsolete remote branch and clean its tags.", "Commit the current changes and push the branch.", "Restore all local edits to make the checkout clean.", "Alter the production database and restart the application."],
]


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    if OUTPUT.exists():
        existing = {p.name for p in OUTPUT.iterdir()}
        if existing != {"calibration.jsonl", "development.jsonl"}:
            raise FileExistsError(f"refusing to overwrite existing or frozen data: {OUTPUT}")
    base_cal = load_rows(BASE / "calibration.jsonl")
    status_template = next(r for r in base_cal if r["family"] == "git_read_status")
    ood_template = next(r for r in base_cal if r["family"] == "out_of_domain")
    calibration = list(base_cal)
    for i, (positive, negatives) in enumerate(CAL_GROUPS):
        group = f"git_read_status_v4_template_{i:02d}"
        calibration.append(make_row(status_template, row_id=f"p446_v4_cal_{i:02d}_p", split="calibration", family="git_read_status", template_id=group, status="accepted", prompt=positive, origin="authored_boundary_calibration_v4"))
        for j, prompt in enumerate(negatives):
            calibration.append(make_row(status_template, row_id=f"p446_v4_cal_{i:02d}_n{j}", split="calibration", family="git_read_status", template_id=group, status="abstain", prompt=prompt, origin="authored_boundary_calibration_v4"))

    development: list[dict] = []
    for i, (positive_a, positive_b, negatives) in enumerate(DEV_GROUPS):
        group = f"git_read_status_v4_eval_template_{i:02d}"
        development.append(make_row(status_template, row_id=f"p446_v4_eval_{i:02d}_p0", split="development", family="git_read_status", template_id=group, status="accepted", prompt=positive_a, origin="frozen_authored_development_v4"))
        development.append(make_row(status_template, row_id=f"p446_v4_eval_{i:02d}_p1", split="development", family="git_read_status", template_id=group, status="accepted", prompt=positive_b, origin="frozen_authored_development_v4"))
        for j, prompt in enumerate(negatives):
            development.append(make_row(status_template, row_id=f"p446_v4_eval_{i:02d}_n{j}", split="development", family="git_read_status", template_id=group, status="abstain", prompt=prompt, origin="frozen_authored_development_v4"))
    for i, prompts in enumerate(DEV_OOD_GROUPS):
        group = f"out_of_domain_v4_eval_template_{i:02d}"
        for j, prompt in enumerate(prompts):
            development.append(make_row(ood_template, row_id=f"p446_v4_ood_{i:02d}_{j}", split="development", family="out_of_domain", template_id=group, status="abstain", prompt=prompt, origin="frozen_authored_development_v4"))

    previous = [row for path in PREVIOUS_DEVELOPMENTS for row in load_rows(path)]
    previous_prompts = {r["prompt"].strip().casefold() for r in previous}
    cal_prompts = [r["prompt"].strip().casefold() for r in calibration]
    dev_prompts = [r["prompt"].strip().casefold() for r in development]
    cal_groups = {r["template_id"] for r in calibration}
    dev_groups = {r["template_id"] for r in development}
    if len(calibration) > 512 or len(development) > 512:
        raise ValueError("trainer row cap exceeded")
    if len(set(cal_prompts)) != len(cal_prompts) or len(set(dev_prompts)) != len(dev_prompts):
        duplicate_prompts = {prompt for prompt in cal_prompts + dev_prompts if (cal_prompts + dev_prompts).count(prompt) > 1}
        examples = [{"prompt": prompt, "ids": [r["id"] for r in calibration + development if r["prompt"].strip().casefold() == prompt]} for prompt in sorted(duplicate_prompts)[:8]]
        raise ValueError(f"duplicate prompt found: {examples}")
    cal_overlap = set(cal_prompts) & set(dev_prompts)
    previous_overlap = set(dev_prompts) & previous_prompts
    if cal_overlap or previous_overlap:
        raise ValueError(f"development prompt overlap detected: calibration={sorted(cal_overlap)[:5]}, previous={sorted(previous_overlap)[:5]}")
    if cal_groups & dev_groups:
        raise ValueError("calibration/development template groups overlap")
    if len({r["id"] for r in calibration + development}) != len(calibration) + len(development):
        raise ValueError("duplicate case ID")
    for group in (g for g in cal_groups if g.startswith("git_read_status_v4_template_")):
        labels = {r["expected_status"] for r in calibration if r["template_id"] == group}
        if labels != {"accepted", "abstain"}:
            raise ValueError(f"unbalanced v4 calibration group: {group}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUTPUT / "calibration.jsonl", calibration)
    write_jsonl(OUTPUT / "development.jsonl", development)
    manifest = {
        "schema": "wrench.system-one-v4-authored-data.v1",
        "status": "frozen_before_candidate_training",
        "base_calibration_manifest": "internal/system-one-v3-data/data-manifest.json",
        "base_calibration_sha256": digest(BASE / "calibration.jsonl"),
        "previous_development_used_for_labels": False,
        "previous_development_sha256_for_overlap_audit_only": {str(p.relative_to(ROOT)): digest(p) for p in PREVIOUS_DEVELOPMENTS},
        "sealed_final_split_read": False,
        "authoring_method": "Authored new calibration and development prompts around the v3 error families: partial status, status combined with mutations, content advice, remote operations, permissions, cleanup, branch operations, and out-of-domain requests.",
        "calibration": {"rows": len(calibration), "sha256": digest(OUTPUT / "calibration.jsonl"), "family_label_counts": {f: dict(Counter(r["expected_status"] for r in calibration if r["family"] == f)) for f in sorted({r["family"] for r in calibration})}, "new_boundary_template_groups": len(CAL_GROUPS), "new_boundary_rows": len(CAL_GROUPS) * 4},
        "development": {"rows": len(development), "sha256": digest(OUTPUT / "development.jsonl"), "family_label_counts": {f: dict(Counter(r["expected_status"] for r in development if r["family"] == f)) for f in sorted({r["family"] for r in development})}, "template_groups": len(dev_groups), "exact_prompt_overlap_with_calibration": 0, "exact_prompt_overlap_with_previous_development": 0, "template_group_overlap_with_calibration": 0},
    }
    (OUTPUT / "data-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "calibration_rows": len(calibration), "development_rows": len(development), "calibration_sha256": manifest["calibration"]["sha256"], "development_sha256": manifest["development"]["sha256"], "status": manifest["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
