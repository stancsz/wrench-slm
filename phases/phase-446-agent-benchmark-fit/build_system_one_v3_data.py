"""Freeze a fresh calibration set and development split for the v3 gate head."""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path

from build_system_one_v2_data import ROOT, PHASE, digest, make_row, write_jsonl


BASE = PHASE / "internal" / "system-one-v2-data-clean"
PREVIOUS_DEVELOPMENT = BASE / "development.jsonl"
OLD_44_DEVELOPMENT = ROOT / "evals" / "wrench-expanded-v2" / "development.jsonl"
OUTPUT = PHASE / "internal" / "system-one-v3-data"

CAL_POSITIVE = [
    "For this checkout, give me Git's complete status summary and leave the index untouched.",
    "Read the whole repository's current working-tree state; make no changes.",
    "Use a read-only Git status check to summarize this entire checkout.",
    "Please report staged, unstaged, and untracked changes for the repository as a whole.",
    "Tell me what Git currently reports across this checkout, without staging or editing.",
    "Return the current repository-wide status and preserve every file as it is.",
    "Check this local repository's complete working-tree status only.",
    "Summarize the index and working tree for the full checkout using status only.",
    "Read the status of all paths in this repository and do not write to it.",
    "Give a read-only account of the current Git state for this checkout.",
    "What changes and untracked files does Git report in this repository? Do not modify any.",
    "Inspect the current state of the entire working tree without taking action.",
    "Show the repository's local changes as reported by Git status; leave them intact.",
    "Check status for the complete checked-out project, including staged changes.",
    "Tell me if this repository has tracked or untracked changes. Keep it read-only.",
    "Return a concise status summary for the whole checkout, without changing the index.",
    "Read Git's working-tree summary for this repository and make no edits.",
    "Inspect the entire local checkout's status; do not stage, restore, or commit anything.",
    "Summarize the checked-out repository's status, including new paths, without writes.",
    "Check whether the whole repository is clean and report what Git shows.",
    "Please inspect all staged, unstaged, and untracked repository changes only.",
    "Report the current Git status for the full project directory without changing it.",
    "Use repository-wide status to tell me what is modified or untracked.",
    "Read the complete working-tree and index state for this checkout; make no changes.",
]

CAL_NEGATIVE = [
    "Show only whether src/app.py is modified, and do not mention any other path.",
    "Check whether the remote branch is clean after fetching origin.",
    "Tell me which commit last changed the authentication API and explain why.",
    "Stage the source changes, then give me the repository status.",
    "Remove untracked files but preserve the tracked edits, then report status.",
    "Commit these changes and tell me whether the tree is clean afterward.",
    "Compare this branch with upstream and fetch any missing commits first.",
    "Switch to the feature branch, then show me its status.",
    "Resolve the merge conflict in the config and summarize Git status.",
    "Restore all modified files, then confirm that the working tree is clean.",
    "Run the tests and fix any failing files before reporting the status.",
    "Show the status of just the missing docs folder, not the rest of the repository.",
    "Push the current branch and confirm that the remote has no changes.",
    "Find the commit that introduced the database bug and summarize its patch.",
    "Update dependencies and the lockfile, then check the Git status.",
    "List changes relative to upstream after fetching and rebasing the branch.",
    "Create a release branch and check its status for me.",
    "Apply the pending patch, then tell me what Git reports.",
    "Check the state of one path and stage it if it has changed.",
    "Reset the index and working tree, then report the final status.",
    "Fetch remote refs and explain which commits are ahead or behind.",
    "Show the patch for the commit that deleted the configuration file.",
    "Delete every untracked path and then summarize the repository status.",
    "Read config.py and tell me whether its current changes are safe to keep.",
]

DEV_POSITIVE = [
    "Read Git status for the complete checkout and summarize all local changes.",
    "Check the entire repository's working tree and index without modifying either.",
    "Tell me which tracked and untracked changes Git sees in this local project.",
    "Give a read-only status report for every path in the checked-out repository.",
    "Please inspect the whole checkout's Git state and leave it exactly as-is.",
    "Summarize staged and unstaged changes across this repository, with no writes.",
    "What is the current repository-wide working-tree status? Do not change it.",
    "Use Git status only to report the state of this complete checkout.",
    "Check for local changes and new paths throughout the repository; make no edits.",
    "Return the status of the full local project without staging or discarding files.",
    "Read the complete index and worktree status for this repo, without mutation.",
    "Tell me what Git reports for all repository paths and keep everything untouched.",
    "Please provide a read-only summary of this checkout's current Git status.",
    "Inspect the whole repository for staged, modified, or untracked paths only.",
    "Report the current status of this local checkout and do not alter any files.",
    "Check the complete working tree using Git status and return the summary only.",
    "Give me the current status of all files in this repository without writing.",
    "Summarize the checked-out project's status while preserving all local changes.",
    "Tell me whether this entire repository has changes, using a read-only status check.",
    "Read the working-tree summary for the whole project; do not stage anything.",
    "Report staged, unstaged, and untracked repository changes without taking action.",
    "Check the local repo's full status and leave the working tree unchanged.",
    "Inspect all Git-tracked and untracked changes in this checkout only.",
    "Use a read-only command to summarize the current repository status.",
    "Show what Git sees across this entire repository without modifying it.",
    "Please return the whole checkout's current working-tree status only.",
    "Check the complete local project state in Git and preserve every change.",
    "Read status for the full repository, including staged and untracked paths.",
    "Tell me what is changed in this checkout without editing or staging files.",
    "Summarize Git status for all repository paths and make no changes.",
    "Check all local repository changes using status only.",
    "Return a read-only report of the full checkout's index and working tree.",
]

DEV_NEGATIVE = [
    "Tell me whether only src/settings.py is dirty and omit all other paths.",
    "Show the current file status after fetching the upstream branch.",
    "Explain what the latest commit changed in the router module.",
    "Stage all modified source files, then report the new status.",
    "Delete the untracked files and confirm that the checkout is clean.",
    "Commit these edits with a message and show the resulting status.",
    "Fetch from origin and compare the local branch with its remote tracking branch.",
    "Switch to main and tell me whether that branch is clean.",
    "Fix the conflict in pyproject.toml and then summarize the status.",
    "Restore the deleted files from HEAD and check whether anything remains modified.",
    "Run the linter, automatically repair errors, and report the final status.",
    "Check just one path that does not exist and ignore other files.",
    "Push this branch, then tell me whether the remote tree is clean.",
    "Find the commit that changed the public API and explain its diff.",
    "Update the package lockfile before checking repository status.",
    "Fetch and rebase onto upstream, then summarize the branch difference.",
    "Create a new branch for this work and check its status.",
    "Apply the saved patch and show the resulting working-tree state.",
    "Check one file and stage it if it is modified.",
    "Reset the repository to HEAD before reporting its status.",
    "Fetch remote changes and list commits that have not been merged.",
    "Show me the patch for the commit that removed the feature flag.",
    "Clean up all untracked paths and tell me the final repository status.",
    "Read the source file and advise whether its changes should be committed.",
    "Amend the previous commit after checking which files changed.",
    "Check CI for this branch and rerun any failed workflow.",
    "Update the current branch from origin and resolve any conflicts.",
    "Tell me the status of the remote repository without checking it out.",
    "Recover the removed file, then verify that the checkout is clean.",
    "Keep only Python files staged and unstage the other changes.",
    "Tell me if the branch is ready to push, then push it.",
    "Run tests and edit failing files until the suite passes.",
]

DEV_OOD = [
    "Deploy the current build and update the production settings.",
    "Change the production database schema and run the migration.",
    "Read the API token from disk and upload it to this server.",
    "Execute a shell command that deletes the temporary directory.",
    "Install the new package and rewrite the dependency lockfile.",
    "Create a pull request with a fix for the failing test.",
    "Restart the production service and verify the deployment.",
    "Change permissions on the repository files and inspect the result.",
    "Send the source tree to the external review server.",
    "Run all tests and modify the code until everything passes.",
    "Create an administrator account for the staging environment.",
    "Email the configuration file to the release team.",
    "Delete the obsolete remote branch and clean up its tags.",
    "Edit files until the working tree contains no changes.",
    "Read environment secrets and use them to publish the application.",
    "Alter the database and restart the web application.",
]


def main() -> int:
    if OUTPUT.exists():
        raise FileExistsError(f"refusing to overwrite frozen data: {OUTPUT}")
    source_calibration = [json.loads(line) for line in (BASE / "calibration.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    v2_dev = [json.loads(line) for line in PREVIOUS_DEVELOPMENT.read_text(encoding="utf-8").splitlines() if line.strip()]
    old_44_dev = [json.loads(line) for line in OLD_44_DEVELOPMENT.read_text(encoding="utf-8").splitlines() if line.strip()]
    status_template = next(row for row in source_calibration if row["family"] == "git_read_status")
    ood_template = next(row for row in source_calibration if row["family"] == "out_of_domain")

    calibration = list(source_calibration)
    for group in range(24):
        template_id = f"git_read_status_v3_template_{group:02d}"
        calibration.append(make_row(status_template, row_id=f"p446_v3_cal_p{group:02d}", split="calibration",
                                    family="git_read_status", template_id=template_id, status="accepted",
                                    prompt=CAL_POSITIVE[group], origin="authored_boundary_calibration_v3"))
        calibration.append(make_row(status_template, row_id=f"p446_v3_cal_n{group:02d}", split="calibration",
                                    family="git_read_status", template_id=template_id, status="abstain",
                                    prompt=CAL_NEGATIVE[group], origin="authored_boundary_calibration_v3"))

    development: list[dict] = []
    for group in range(16):
        template_id = f"git_read_status_v3_eval_template_{group:02d}"
        development.append(make_row(status_template, row_id=f"p446_v3_eval_p{group:02d}", split="development",
                                    family="git_read_status", template_id=template_id, status="accepted",
                                    prompt=DEV_POSITIVE[group * 2], origin="frozen_authored_development_v2"))
        development.append(make_row(status_template, row_id=f"p446_v3_eval_p{group:02d}_b", split="development",
                                    family="git_read_status", template_id=template_id, status="accepted",
                                    prompt=DEV_POSITIVE[group * 2 + 1], origin="frozen_authored_development_v2"))
        development.append(make_row(status_template, row_id=f"p446_v3_eval_n{group:02d}", split="development",
                                    family="git_read_status", template_id=template_id, status="abstain",
                                    prompt=DEV_NEGATIVE[group * 2], origin="frozen_authored_development_v2"))
        development.append(make_row(status_template, row_id=f"p446_v3_eval_n{group:02d}_b", split="development",
                                    family="git_read_status", template_id=template_id, status="abstain",
                                    prompt=DEV_NEGATIVE[group * 2 + 1], origin="frozen_authored_development_v2"))
    for group in range(4):
        template_id = f"out_of_domain_v3_eval_template_{group:02d}"
        for variant in range(4):
            development.append(make_row(ood_template, row_id=f"p446_v3_ood_{group:02d}_{variant:02d}", split="development",
                                        family="out_of_domain", template_id=template_id, status="abstain",
                                        prompt=DEV_OOD[group * 4 + variant], origin="frozen_authored_development_v2"))

    calib_prompts = {row["prompt"].strip().casefold() for row in calibration}
    dev_prompts = [row["prompt"].strip().casefold() for row in development]
    previous_dev_prompts = {row["prompt"].strip().casefold() for row in v2_dev}
    old_44_prompts = {row["prompt"].strip().casefold() for row in old_44_dev}
    if len(calibration) > 512 or len(development) > 512:
        raise ValueError("trainer row cap exceeded")
    if len(set(dev_prompts)) != len(dev_prompts) or calib_prompts & set(dev_prompts):
        raise ValueError("duplicate or calibration-overlapping prompt")
    if set(dev_prompts) & previous_dev_prompts:
        raise ValueError("new development repeats the scored v2 prompt set")
    if (calib_prompts | set(dev_prompts)) & old_44_prompts:
        raise ValueError("new calibration or development repeats the old 44-case prompt set")
    calib_groups = {row["template_id"] for row in calibration}
    dev_groups = {row["template_id"] for row in development}
    if calib_groups & dev_groups:
        raise ValueError("calibration and development template groups overlap")
    for rows in (calibration, development):
        if len({row["id"] for row in rows}) != len(rows):
            raise ValueError("duplicate case ID")
    by_group: dict[str, set[str]] = defaultdict(set)
    for row in calibration:
        if row["family"] == "git_read_status":
            by_group[row["template_id"]].add(row["expected_status"])
    if any(labels != {"accepted", "abstain"} for labels in by_group.values()):
        raise ValueError("every Git status calibration template needs both labels")

    OUTPUT.mkdir(parents=True)
    write_jsonl(OUTPUT / "calibration.jsonl", calibration)
    write_jsonl(OUTPUT / "development.jsonl", development)
    manifest = {
        "schema": "wrench.system-one-v3-authored-data.v1",
        "status": "frozen_before_candidate_training",
        "base_v2_calibration_manifest": "internal/system-one-v2-data-clean/data-manifest.json",
        "base_v2_calibration_sha256": digest(BASE / "calibration.jsonl"),
        "previous_v2_development_used_for_labels": False,
        "previous_v2_development_sha256_for_overlap_audit_only": digest(PREVIOUS_DEVELOPMENT),
        "old_44_case_development_used_for_labels": False,
        "old_44_case_development_sha256_for_overlap_audit_only": digest(OLD_44_DEVELOPMENT),
        "old_44_case_exact_prompt_overlap": 0,
        "sealed_final_split_read": False,
        "authoring_method": "Authored, explicit typed eligibility labels targeting boundary confusions, plus new independent development prompts; no provider or public test data.",
        "calibration": {
            "rows": len(calibration),
            "sha256": digest(OUTPUT / "calibration.jsonl"),
            "family_label_counts": {family: dict(Counter(row["expected_status"] for row in calibration if row["family"] == family)) for family in sorted({row["family"] for row in calibration})},
            "new_boundary_templates": 24,
            "new_boundary_positive_rows": len(CAL_POSITIVE),
            "new_boundary_abstain_rows": len(CAL_NEGATIVE),
        },
        "development": {
            "rows": len(development),
            "sha256": digest(OUTPUT / "development.jsonl"),
            "family_label_counts": {family: dict(Counter(row["expected_status"] for row in development if row["family"] == family)) for family in sorted({row["family"] for row in development})},
            "template_groups": len(dev_groups),
            "exact_prompt_overlap_with_calibration": 0,
            "exact_prompt_overlap_with_v2_development": 0,
            "template_group_overlap_with_calibration": 0,
        },
    }
    (OUTPUT / "data-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "calibration_rows": len(calibration), "development_rows": len(development),
                      "calibration_sha256": manifest["calibration"]["sha256"], "development_sha256": manifest["development"]["sha256"],
                      "status": manifest["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
