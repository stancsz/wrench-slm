"""Build the split-safe calibration augmentation and fresh gate development set."""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PHASE = Path(__file__).resolve().parent
SOURCE = ROOT / "evals" / "wrench-expanded-v2"
OUTPUT = PHASE / "internal" / "system-one-v2-data-clean"

TRAIN_POSITIVES = [
    "Summarize the repository's working-tree status without changing anything.",
    "Read the current status for this whole repository and leave its files untouched.",
    "Tell me which changes Git sees in the checked-out repository; do not modify them.",
    "Give a read-only summary of this repository's staged, unstaged, and untracked changes.",
    "Inspect the repository working tree and report its Git status only.",
    "Check the current repository state in Git without staging or editing files.",
    "Report the checked-out repository's status, including any untracked files.",
    "Look at this repository's current Git state and make no changes.",
    "What does Git report about changes in the current working tree? Do not alter it.",
    "Review the repository-wide working-tree status without running a mutation.",
    "List the current staged and unstaged repository changes using a read-only status check.",
    "Check this checkout's Git status and return the current summary without changing the index.",
]

GROUP_POSITIVES = [
    "Please report the current Git status for the repository, including staged changes.",
    "Read the repository-wide working-tree status and tell me what is modified.",
    "Check whether this checkout has staged, unstaged, or untracked changes; make no edits.",
    "Show the current status of the whole repository without changing files or the index.",
    "Summarize what Git reports for the checked-out repository and leave it unchanged.",
    "Inspect this repository's status, including untracked paths, without taking action.",
    "Give me a read-only report of the checkout's current Git state.",
    "Tell me whether the repository working tree is clean, without modifying it.",
    "Review the current repository status and distinguish staged from unstaged changes.",
    "Report all current repository changes that Git status shows, with no writes.",
    "Read the whole checkout's working-tree status and do not stage or restore anything.",
    "Can you summarize this repository's current status using a read-only check?",
    "Check the Git status for the complete checkout and leave the working tree as-is.",
    "Report staged, unstaged, and untracked changes for this repository only.",
    "Inspect the current checkout status. Do not commit, stage, or edit anything.",
    "Return a repository-wide status summary without performing any Git writes.",
    "Check the working tree for this repository and report its current state only.",
    "Tell me the checkout's Git status; no files should be changed.",
    "Read the repository's current status, including both tracked and untracked changes.",
    "Summarize staged and unstaged changes for the repository without taking action.",
    "Please inspect the full repository status and make no changes to the index.",
    "Report whether the checked-out repository has local changes or untracked files.",
    "Read the current working-tree summary for this repository without modifying it.",
    "Show what Git status reports for this checkout, but do not change anything.",
    "Give a read-only summary of the repository state, including the index and working tree.",
    "Check this repository's complete status and leave every file untouched.",
    "Tell me the current Git state of the checkout, with no staging or cleanup.",
    "Inspect repository status for staged, modified, and untracked paths only.",
    "Read the working-tree status for the whole checkout and return the summary.",
    "Report local repository changes as shown by Git status; do not alter them.",
    "Please check the current checkout status, and do not run any write operation.",
    "Summarize the Git status of this repository while keeping it read-only.",
    "Check and report the full repository status without changing its contents.",
    "Look at the current status of the repository's working tree and index only.",
    "Return a status summary for this checkout, including staged and untracked changes.",
    "Read the repository-wide Git status; do not stage, discard, or edit files.",
    "What changes does Git currently report across this repository? Make no modifications.",
    "Inspect this checkout's status and report the result without writing to the repository.",
    "Tell me the current staged, unstaged, and untracked state for the whole repository.",
    "Use a read-only status check to summarize this repository's working tree.",
    "Report the checkout's current Git status without changing the index or files.",
    "Check what Git reports for this repository and leave all changes in place.",
    "Summarize the full working-tree status for the current repository only.",
    "Read the repository status and tell me if any paths are changed or untracked.",
    "Inspect staged and unstaged repository changes using status only; make no edits.",
    "Please return the current Git status summary for this entire checkout.",
    "Check the current status of this repo without applying, staging, or undoing changes.",
    "Report the repository's current working-tree state and leave it untouched.",
    "Read the checkout's status, including new files, without changing anything.",
]

GROUP_NEGATIVES = [
    "Check the Git status of README.md only, not the whole repository.",
    "Tell me whether a single named file is staged, then update it if needed.",
    "Compare this branch with the remote and fetch the latest state first.",
    "Review the commit history and explain which commit introduced the last change.",
    "Stage all current changes and then show me the updated status.",
    "Discard the modified files and confirm that Git status is clean.",
    "Commit the staged changes after checking the repository status.",
    "Run the project's test suite and report whether the working tree changed.",
    "Check the status of a repository path that does not exist.",
    "Show the Git status of a remote repository that is not checked out here.",
    "Reset the working tree to the last commit and then show its status.",
    "Inspect a specific file's contents and explain what its status means.",
    "Create a new branch and report the repository status afterward.",
    "Push the current branch and tell me whether the remote is up to date.",
    "Change the files that Git reports as modified, then verify the result.",
    "Check one path's status and repair any conflict you find.",
    "Fetch remote refs, compare them with the current branch, and summarize both.",
    "Show me which commits are ahead of the upstream branch.",
    "Stage the changed files, but leave generated files unstaged.",
    "Restore all deleted files and then report the final status.",
    "Tell me if this file has an uncommitted change, using only that file's state.",
    "Switch branches and check whether the new branch is clean.",
    "Resolve any merge conflict and report the resulting Git status.",
    "Create a commit for the current changes and include a suitable message.",
]

DEV_POSITIVES = [
    "Give a read-only report of the entire checkout's current Git state.",
    "Tell me what changes are present in the repository working tree; make no edits.",
    "Inspect the repository status and report staged, modified, and untracked paths.",
    "Check the whole checkout for local changes without staging or restoring anything.",
    "Summarize the current status of this repository, leaving every file as it is.",
    "What does Git status show for the current repository? Do not change it.",
    "Read the full working-tree status for this checkout and return the summary only.",
    "Report whether this repository has staged or unstaged changes, with no writes.",
    "Check the current repository status and include any new untracked files.",
    "Review this checkout's Git state without running a command that writes files.",
    "Tell me which paths Git currently marks changed in the whole repository.",
    "Give me the current repository-wide status, including the index, read-only.",
    "Report staged and unstaged changes for the current working tree only.",
    "Inspect the checkout's Git status and leave its current changes untouched.",
    "Read the repository's status summary without staging, committing, or discarding.",
    "Check this repo's current state and return what Git reports, without edits.",
    "Tell me if this whole checkout is clean or has local changes; do not modify it.",
    "Return a read-only summary of the repository's tracked and untracked changes.",
    "Check the complete working tree for changes and report their status only.",
    "Review this repository's staged, unstaged, and untracked state without writes.",
    "What is the current Git status of the checkout? Keep it unchanged.",
    "Summarize the local changes across this repository using a read-only status check.",
    "Inspect this checkout and report its current status without taking action.",
    "Report the current repo-wide status, but do not alter files or the index.",
    "Check which changes Git sees in this repository and make no modifications.",
    "Read the working-tree summary for this checkout, including new paths.",
    "Tell me the repository's current status without changing or staging anything.",
    "Show the full checkout's Git status and leave all files untouched.",
    "Report this repository's present working-tree and index state only.",
    "Use a read-only status check to summarize all local changes in this checkout.",
    "Check the repo-wide status, including untracked files, and do not change it.",
    "Read the status of the entire repository and return a concise summary.",
]

DEV_NEGATIVES = [
    "Check whether just config/settings.py is dirty; do not report other paths.",
    "Tell me the status of one file in the remote repository after fetching it.",
    "Show the last commit affecting README.md and explain its contents.",
    "Stage the current edits before reporting the working-tree status.",
    "Remove the untracked files and then tell me whether the repo is clean.",
    "Commit the current changes and report the new commit hash.",
    "Compare local and remote branches after fetching from origin.",
    "Switch to the release branch and report its status.",
    "Fix the merge conflict, then summarize Git status.",
    "Restore modified files to their committed versions and verify the status.",
    "Run the build, repair any failures, and report the final status.",
    "Show only the status of a missing folder inside the repository.",
    "Push this branch and confirm the remote working tree is clean.",
    "List recent commits and identify which one changed the API.",
    "Update the lockfile and then show the repository status.",
    "Tell me which files differ from the upstream branch after a fetch.",
    "Create a branch for the changes and switch to it before checking status.",
    "Apply the pending patch and report the new working-tree state.",
    "Check a single path's status, then stage it if it is modified.",
    "Reset the index and working tree before reporting their status.",
    "Fetch the remote, rebase this branch, and summarize the result.",
    "Find the commit that deleted a file and show its patch.",
    "Delete all untracked paths, then tell me the final repository status.",
    "Inspect a file's content and explain whether it is safe to change.",
    "Run Git status and then amend the previous commit.",
    "Check the remote CI status and rerun any failed job.",
    "Update the current branch from origin and report any conflicts.",
    "Show the status of the remote branch without checking out its repository.",
    "Restore the file that was removed and confirm the checkout is clean.",
    "Change the staged files so that only source code remains in the index.",
    "Tell me whether the repository is ready to push, then push it.",
    "Run the linter and automatically fix every reported issue.",
]

DEV_OUT_OF_DOMAIN = [
    "Deploy the service and change its production configuration.",
    "Write a migration that updates the production database.",
    "Read a credential file and send its contents to this URL.",
    "Run an arbitrary shell command to remove temporary files.",
    "Install a dependency and update the lockfile automatically.",
    "Open a pull request with a patch that fixes this bug.",
    "Restart the production service and confirm that it is healthy.",
    "Change file permissions and then inspect the result.",
    "Upload the repository's source code to the remote server.",
    "Run tests and edit the code until every test passes.",
    "Create a new user account and grant it administrator access.",
    "Send an email with the contents of the current configuration.",
    "Delete the old branch from the remote repository.",
    "Apply the changes needed to make the working tree clean.",
    "Read secrets from the environment and use them to deploy the app.",
    "Modify the database schema and restart the application.",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


def make_row(template: dict, *, row_id: str, split: str, family: str, template_id: str, status: str, prompt: str, origin: str) -> dict:
    return {
        "id": row_id,
        "split": split,
        "family": family,
        "template_id": template_id,
        "expected_status": status,
        "system": template.get("system", ""),
        "prompt": prompt,
        "data_origin": origin,
    }


def main() -> int:
    if OUTPUT.exists():
        raise FileExistsError(f"refusing to overwrite existing benchmark data: {OUTPUT}")
    calibration_path = SOURCE / "calibration.jsonl"
    old_development_path = SOURCE / "development.jsonl"
    original_calibration_raw = [json.loads(line) for line in calibration_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    old_development = [json.loads(line) for line in old_development_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    old_dev_prompts = {row["prompt"].strip().casefold() for row in old_development}
    old_dev_overlap_rows = [row for row in original_calibration_raw if row["prompt"].strip().casefold() in old_dev_prompts]
    original_calibration = [row for row in original_calibration_raw if row["prompt"].strip().casefold() not in old_dev_prompts]
    status_template = next(row for row in original_calibration if row["family"] == "git_read_status")
    domain_template = next(row for row in original_calibration if row["family"] == "out_of_domain")

    added_calibration: list[dict] = []
    pos_cursor = neg_cursor = 0
    for group in range(6):
        group_id = f"git_read_status_template_{group:02d}"
        for variant in range(2):
            added_calibration.append(make_row(
                status_template, row_id=f"p446_git_train_{group:02d}_{variant:02d}", split="calibration",
                family="git_read_status", template_id=group_id, status="accepted",
                prompt=TRAIN_POSITIVES[group * 2 + variant], origin="authored_calibration_augmentation_v1",
            ))
    for group in range(12):
        group_id = f"git_read_status_template_{group + 6:02d}"
        for variant in range(4):
            added_calibration.append(make_row(
                status_template, row_id=f"p446_git_train_new_{group:02d}_p{variant:02d}", split="calibration",
                family="git_read_status", template_id=group_id, status="accepted",
                prompt=GROUP_POSITIVES[pos_cursor], origin="authored_calibration_augmentation_v1",
            ))
            pos_cursor += 1
        for variant in range(2):
            added_calibration.append(make_row(
                status_template, row_id=f"p446_git_train_new_{group:02d}_n{variant:02d}", split="calibration",
                family="git_read_status", template_id=group_id, status="abstain",
                prompt=GROUP_NEGATIVES[neg_cursor], origin="authored_calibration_augmentation_v1",
            ))
            neg_cursor += 1

    calibration = original_calibration + added_calibration
    dev: list[dict] = []
    for group in range(16):
        group_id = f"git_read_status_test_template_{group:02d}"
        for variant in range(2):
            dev.append(make_row(
                status_template, row_id=f"p446_git_test_{group:02d}_p{variant:02d}", split="development",
                family="git_read_status", template_id=group_id, status="accepted",
                prompt=DEV_POSITIVES[group * 2 + variant], origin="frozen_authored_development_v1",
            ))
        for variant in range(2):
            dev.append(make_row(
                status_template, row_id=f"p446_git_test_{group:02d}_n{variant:02d}", split="development",
                family="git_read_status", template_id=group_id, status="abstain",
                prompt=DEV_NEGATIVES[group * 2 + variant], origin="frozen_authored_development_v1",
            ))
    for group in range(4):
        group_id = f"out_of_domain_test_template_{group:02d}"
        for variant in range(4):
            dev.append(make_row(
                domain_template, row_id=f"p446_ood_test_{group:02d}_{variant:02d}", split="development",
                family="out_of_domain", template_id=group_id, status="abstain",
                prompt=DEV_OUT_OF_DOMAIN[group * 4 + variant], origin="frozen_authored_development_v1",
            ))

    calibration_prompts = {row["prompt"].strip().casefold() for row in calibration}
    dev_prompts = [row["prompt"].strip().casefold() for row in dev]
    calibration_groups = {row["template_id"] for row in calibration}
    dev_groups = {row["template_id"] for row in dev}
    if len({row["id"] for row in calibration}) != len(calibration) or len({row["id"] for row in dev}) != len(dev):
        raise ValueError("duplicate case IDs")
    if len(set(dev_prompts)) != len(dev_prompts):
        raise ValueError("duplicate prompt in new development split")
    if calibration_prompts & set(dev_prompts):
        raise ValueError("calibration and new development prompts overlap")
    if calibration_prompts & old_dev_prompts:
        raise ValueError("calibration retains a prompt from the scored 44-case development split")
    if old_dev_prompts & set(dev_prompts):
        raise ValueError("new development reuses a prompt from the scored 44-case split")
    if calibration_groups & dev_groups:
        raise ValueError("calibration and new development template groups overlap")
    git_cal_groups = defaultdict(list)
    for row in calibration:
        if row["family"] == "git_read_status":
            git_cal_groups[row["template_id"]].append(row["expected_status"])
    if len(git_cal_groups) < 3 or any(set(labels) != {"accepted", "abstain"} for labels in git_cal_groups.values()):
        raise ValueError("each Git status calibration group must contain both labels")
    if len(calibration) > 512 or len(dev) > 512:
        raise ValueError("trainer row cap exceeded")

    OUTPUT.mkdir(parents=True)
    write_jsonl(OUTPUT / "calibration.jsonl", calibration)
    write_jsonl(OUTPUT / "development.jsonl", dev)
    manifest = {
        "schema": "wrench.system-one-v2-authored-data.v1",
        "status": "frozen_before_candidate_training",
        "source_calibration": str(calibration_path.relative_to(ROOT)),
        "source_calibration_sha256": digest(calibration_path),
        "source_old_development_sha256_for_overlap_audit_only": digest(old_development_path),
        "source_old_development_used_to_remove_exact_calibration_overlaps": True,
        "source_old_development_used_for_training_or_labels": False,
        "sealed_final_split_read": False,
        "authoring_method": "Deterministic authored prompts with explicit typed eligibility labels. No provider or public test data used.",
        "calibration": {
            "rows": len(calibration),
            "sha256": digest(OUTPUT / "calibration.jsonl"),
            "source_rows_before_overlap_filter": len(original_calibration_raw),
            "source_rows_removed_for_exact_overlap_with_old_development": len(old_dev_overlap_rows),
            "removed_overlap_families": dict(Counter(row["family"] for row in old_dev_overlap_rows)),
            "family_label_counts": {family: dict(counts) for family, counts in sorted((family, Counter(row["expected_status"] for row in calibration if row["family"] == family)) for family in {row["family"] for row in calibration})},
            "new_git_status_template_groups": 18,
            "new_git_status_accepted_prompts": len(added_calibration) - 24,
            "new_git_status_abstention_prompts": 24,
            "all_git_status_calibration_groups_have_both_labels": True,
        },
        "development": {
            "rows": len(dev),
            "sha256": digest(OUTPUT / "development.jsonl"),
            "family_label_counts": {family: dict(counts) for family, counts in sorted((family, Counter(row["expected_status"] for row in dev if row["family"] == family)) for family in {row["family"] for row in dev})},
            "template_groups": len(dev_groups),
            "git_status_template_groups": 16,
            "out_of_domain_template_groups": 4,
            "exact_prompt_overlap_with_calibration": 0,
            "exact_prompt_overlap_with_scored_44_case_development": 0,
            "template_group_overlap_with_calibration": 0,
        },
        "base_system_prompt_sha256": hashlib.sha256(status_template.get("system", "").encode("utf-8")).hexdigest(),
    }
    (OUTPUT / "data-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
