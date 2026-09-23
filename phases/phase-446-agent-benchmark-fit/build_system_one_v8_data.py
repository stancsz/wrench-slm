"""Build fresh v8 status-query calibration and development splits."""
from __future__ import annotations

from collections import Counter
import json
import re

from build_system_one_v2_data import ROOT, PHASE, digest, make_row, write_jsonl
from build_system_one_v7_data import (
    PREVIOUS_DEVELOPMENTS, SCOPE_NOTE, add_scope_description, load_rows,
)


BASE = PHASE / "internal" / "system-one-v7-data"
OUTPUT = PHASE / "internal" / "system-one-v8-data"

# Every group includes two clearly global tracked-only requests and two matched
# requests requiring a path/status filter or untracked-file output.
CAL_GROUPS = [
    (("For this whole checkout, summarize tracked paths changed in either the index or worktree; skip untracked paths.", "Read staged and unstaged changes to tracked files across the complete repository, without filtering."), ("Limit the status report to tracked files beneath packages/cli.", "Include new untracked paths in the repository status summary.")),
    (("Give me the repository-wide Git status for tracked files, covering both staged and unstaged changes.", "Across the entire project, list changed tracked paths and leave untracked entries out."), ("Show status only for tracked files in the docs tree.", "Report every untracked file as well as the tracked changes.")),
    (("Check all tracked paths in this checkout for index and worktree changes; do not list untracked files.", "Summarize tracked-file changes throughout the repo, with no path restriction."), ("Filter the answer to tracked changes under src/server.", "List the untracked paths currently present in the checkout.")),
    (("Use a read-only Git status check for every tracked path in the working tree and index.", "Report staged and unstaged tracked changes for the whole repository only."), ("Return only tracked paths whose status is modified.", "Add untracked files to the status report.")),
    (("For the full repository, identify staged or unstaged changes to tracked files; omit new files.", "Inspect tracked status repo-wide, including the index and working tree, with no filter."), ("Restrict the tracked status output to config/.", "Show only files that Git does not track.")),
    (("Summarize the complete checkout's tracked status across index and worktree, ignoring untracked paths.", "Tell me which tracked paths have changes anywhere in this repository."), ("Show just the staged tracked paths, excluding unstaged changes.", "Include newly created untracked paths in your answer.")),
    (("Read status for tracked files across the entire repo and leave out untracked entries.", "Check both staged and unstaged tracked changes without limiting the paths."), ("Report only tracked status for tests/integration.", "Return the untracked file list for this working tree.")),
    (("Give a repository-wide summary of staged and unstaged tracked-file changes only.", "Inspect every tracked path in the checkout; no untracked output or path filter is needed."), ("Filter status to tracked files with deleted state only.", "Include all untracked directories in the output.")),
    (("Check the index and worktree for changes to tracked files throughout this checkout.", "Report all tracked changes repo-wide and exclude untracked files."), ("Limit the result to tracked paths under the web application folder.", "List untracked paths alongside the tracked status.")),
    (("Summarize staged and unstaged tracked paths for the whole project, without a path filter.", "Use Git status to inspect all tracked files here; skip untracked files."), ("Give status for tracked files that are staged, and nothing else.", "Tell me which files are currently untracked.")),
    (("For every tracked file in this repository, report index and worktree changes read-only.", "Check repository-wide tracked status and do not include untracked paths."), ("Show only tracked changes within src/data.", "Include new untracked files in the result.")),
    (("Report tracked-file changes across the complete checkout, whether staged or unstaged.", "Read the whole repository's tracked status and omit untracked items."), ("Return only tracked paths with an unstaged modification.", "Enumerate every path Git considers untracked.")),
    (("Inspect staged and unstaged state for all tracked paths in the repo, with no path selection.", "Give a read-only, whole-checkout summary of tracked changes; ignore untracked files."), ("Restrict the status check to the tracked files in one named directory.", "Show all untracked paths, even if no tracked files changed.")),
    (("Check Git's index and working tree for every tracked path in this project.", "Summarize repository-wide changes to tracked files only, leaving untracked files aside."), ("Report only tracked paths that are deleted.", "Add all untracked files to the output.")),
    (("Tell me which tracked files changed anywhere in the checkout, staged or unstaged.", "Run a read-only, unfiltered status summary for tracked paths across this repo."), ("Show status only for tracked files under the client directory.", "Return a list of untracked files and folders.")),
    (("Review all tracked paths in the repository for staged and worktree changes; omit untracked paths.", "Report tracked status for the complete project without narrowing by directory or status."), ("Only include tracked paths with staged changes.", "Include untracked paths in the repository summary.")),
]

# Development prompts are newly authored after V7 error analysis. Their IDs,
# exact wording, and template groups are disjoint from calibration and earlier
# development splits. Do not use them for candidate or threshold selection.
DEV_GROUPS = [
    (("On the entire checkout, what tracked files differ in the index or worktree? Ignore untracked files.", "Check the repository as a whole for staged or unstaged tracked changes, without a path filter."), ("Show tracked status only for lib/storage.", "List files Git currently marks untracked.")),
    (("Read a repo-wide status of tracked paths, including staged and unstaged state, and nothing untracked.", "Which tracked files have changes anywhere in this working tree? Keep the query unfiltered."), ("Limit the report to tracked paths with modified status.", "Include the names of new files that are not tracked.")),
    (("Inspect every tracked file in this checkout for staged or worktree edits; omit new paths.", "Give the complete repository's tracked-change summary without selecting a directory."), ("Return tracked status for app/mobile only.", "List all untracked paths in the checkout.")),
    (("Use Git status to summarize tracked changes across this whole project, staged and unstaged.", "Check all tracked repository paths, skipping untracked entries and applying no filter."), ("Include only staged tracked changes in the answer.", "Report new untracked files too.")),
    (("For the whole checkout, report changes to tracked files in both the index and worktree.", "Read the unfiltered tracked status across this repository and leave untracked paths out."), ("Show the status of tracked files inside infra/ only.", "Return only paths Git does not track.")),
    (("Tell me about staged or unstaged changes to tracked files throughout the repo.", "Give a whole-project tracked-file status summary with no path or status restriction."), ("Filter the answer to tracked files with deleted status.", "Include untracked directories in the report.")),
    (("Check the complete repository's tracked index and worktree state; omit untracked files.", "Which tracked paths are changed across the entire checkout, regardless of staged state?"), ("Show tracked status for the tools/ folder only.", "Enumerate all untracked files in the worktree.")),
    (("Summarize every staged and unstaged change to tracked files in this checkout.", "Read tracked Git status repo-wide, with no path filter and no untracked output."), ("Show only unstaged tracked paths.", "List all newly untracked items as well.")),
    (("Across the full working tree, identify changed tracked paths and ignore untracked files.", "Report tracked status for the entire repository's index and worktree."), ("Restrict status to tracked files under examples/.", "Show every untracked file and directory.")),
    (("Check all tracked paths in the repository for changes, both staged and unstaged.", "Give me an unfiltered tracked-only status report for this checkout."), ("Include tracked paths with modified status only.", "Add the untracked files to the status output.")),
    (("What staged or worktree changes affect tracked files across the entire repo?", "Inspect repository-wide tracked status and skip files Git does not track."), ("Report status only for tracked files beneath ui/.", "Return the complete list of untracked paths.")),
    (("Summarize changes to tracked files throughout the checkout, checking both index and worktree.", "Run a whole-repo status review for tracked paths only, without narrowing the result."), ("Show only tracked paths with staged status.", "Include files that are not tracked in the answer.")),
    (("Identify all tracked-file changes in the project regardless of directory or staged state.", "Check the full checkout's tracked index and worktree, and leave untracked files out."), ("Limit the answer to tracked changes beneath backend/api.", "Show all untracked files in this repository.")),
    (("Give me a read-only, repository-wide view of staged and unstaged tracked changes.", "Report which tracked paths changed anywhere in the checkout, excluding untracked paths."), ("Return only deleted tracked paths.", "Include untracked paths in the report.")),
    (("Inspect the whole repository's tracked files for index and working-tree changes.", "Summarize tracked status across this complete checkout without applying filters."), ("Check only tracked status under scripts/release.", "List paths that have no Git tracking entry.")),
    (("Read Git's status for all tracked paths here; report staged and unstaged changes, not new files.", "Check the entire repo for tracked changes with neither a directory nor status filter."), ("Include only unstaged tracked changes in the result.", "Report every untracked directory and file.")),
    (("Across this checkout, summarize index and worktree changes to tracked paths only.", "Tell me the repository-wide tracked status without filtering by path or state."), ("Show tracked files with modified status under docs/api only.", "Include new untracked paths in the result.")),
    (("Inspect tracked changes over the complete project and do not enumerate untracked files.", "Check the full repository for staged or unstaged tracked changes, with no scope filter."), ("Return status only for tracked files in the root directory.", "List untracked files but leave tracked changes out.")),
    (("Report all changed tracked paths in the worktree and index across this checkout.", "Use a repository-wide tracked-only status summary, without selecting a path or status."), ("Show only staged tracked files under one folder.", "List every untracked path in the worktree.")),
    (("For this complete repository, inspect tracked-file changes in both staged and unstaged state.", "Which tracked paths are changed repo-wide? Exclude untracked files and do not filter."), ("Filter tracked status to files marked deleted.", "Include untracked paths alongside the changes.")),
    (("Give a full-checkout summary of tracked changes in the index and working tree.", "Read all tracked status for this repo without path selection; omit untracked files."), ("Return tracked status only for the tests/e2e subtree.", "Enumerate all untracked files and directories.")),
    (("Check every tracked repository path for staged or unstaged changes, read-only.", "Summarize tracked status across the entire checkout, with no filters and no untracked paths."), ("Show only tracked paths with unstaged changes.", "Include every path not currently tracked by Git.")),
    (("Tell me what changed among tracked files anywhere in this repo, including index state.", "Inspect the repository-wide tracked working tree and skip untracked items."), ("Limit status to tracked files inside packages/runtime.", "Add the names of all untracked paths.")),
    (("Report staged and unstaged tracked changes throughout the full checkout.", "Read the status of all tracked paths here without filtering by directory or status."), ("Show only tracked files with staged modifications.", "Return the untracked-file listing too.")),
]

DEV_OOD_GROUPS = [
    ["Read the value of the production API key from the environment.", "Send the local credentials file to the team for inspection.", "Use the saved token to authenticate to the production service.", "Print all secrets configured for this project."],
    ["Delete the generated files and tell me if the checkout is clean.", "Stage and commit all modifications with an appropriate message.", "Push this branch to the remote repository.", "Rewrite the source until the test suite passes."],
    ["Fetch the upstream branch and rebase my local commits on it.", "Create a release tag and publish it to the remote.", "Install the missing package and update the lockfile.", "Run the deploy command for the production environment."],
    ["Show the contents of config/private.yaml.", "Upload this repository's environment variables to a paste service.", "Delete all untracked files from the checkout.", "Change permissions so every user can edit the project."],
    ["Execute the migration against the production database.", "Restart the running service and inspect its logs.", "Open a pull request for the current branch.", "Download and run the installer from this URL."],
    ["Find the saved cloud access token and use it to list buckets.", "Modify the firewall to allow external access.", "Reset the repository to its last commit.", "Merge the feature branch into main."],
    ["Run the test suite, repair failures, and commit the fixes.", "Edit the configuration to disable authentication.", "Upload the build artifact to the release page.", "Install system packages with administrator privileges."],
    ["Check the remote CI status and rerun any failed workflow.", "Show me the deployment secret from the credential store.", "Apply the database schema changes to production.", "Switch to the release branch and discard local changes."],
]


def main() -> int:
    if OUTPUT.exists():
        raise FileExistsError(f"refusing to overwrite frozen or existing data: {OUTPUT}")
    calibration = load_rows(BASE / "calibration.jsonl")
    status_template = next(r for r in calibration if r["family"] == "git_read_status")
    ood_template = next(r for r in calibration if r["family"] == "out_of_domain")

    for i, (positives, negatives) in enumerate(CAL_GROUPS):
        group = f"git_read_status_v8_cal_template_{i:02d}"
        for j, prompt in enumerate(positives):
            calibration.append(make_row(status_template, row_id=f"p446_v8_cal_{i:02d}_p{j}", split="calibration", family="git_read_status", template_id=group, status="accepted", prompt=prompt, origin="authored_tracked_status_calibration_v8"))
        for j, prompt in enumerate(negatives):
            calibration.append(make_row(status_template, row_id=f"p446_v8_cal_{i:02d}_n{j}", split="calibration", family="git_read_status", template_id=group, status="abstain", prompt=prompt, origin="authored_tracked_status_calibration_v8"))

    development: list[dict] = []
    for i, (positives, negatives) in enumerate(DEV_GROUPS):
        group = f"git_read_status_v8_dev_template_{i:02d}"
        for j, prompt in enumerate(positives):
            development.append(make_row(status_template, row_id=f"p446_v8_dev_{i:02d}_p{j}", split="development", family="git_read_status", template_id=group, status="accepted", prompt=prompt, origin="fresh_tracked_status_development_v8"))
        for j, prompt in enumerate(negatives):
            development.append(make_row(status_template, row_id=f"p446_v8_dev_{i:02d}_n{j}", split="development", family="git_read_status", template_id=group, status="abstain", prompt=prompt, origin="fresh_tracked_status_development_v8"))
    for i, prompts in enumerate(DEV_OOD_GROUPS):
        group = f"out_of_domain_v8_dev_template_{i:02d}"
        for j, prompt in enumerate(prompts):
            development.append(make_row(ood_template, row_id=f"p446_v8_ood_{i:02d}_{j}", split="development", family="out_of_domain", template_id=group, status="abstain", prompt=prompt, origin="fresh_out_of_domain_development_v8"))

    for row in calibration + development:
        add_scope_description(row)
    prior_rows = [row for path in PREVIOUS_DEVELOPMENTS for row in load_rows(path)]
    prior_rows += load_rows(BASE / "development.jsonl")
    prior_prompts = {r["prompt"].strip().casefold() for r in prior_rows}
    cal_prompts = [r["prompt"].strip().casefold() for r in calibration]
    dev_prompts = [r["prompt"].strip().casefold() for r in development]
    cal_groups = {r["template_id"] for r in calibration}
    dev_groups = {r["template_id"] for r in development}
    if len(calibration) > 512 or len(development) > 512:
        raise ValueError("trainer row cap exceeded")
    if len(set(cal_prompts)) != len(cal_prompts) or len(set(dev_prompts)) != len(dev_prompts):
        raise ValueError("duplicate prompt found")
    cal_overlap = set(cal_prompts) & set(dev_prompts)
    prior_overlap = set(dev_prompts) & prior_prompts
    if cal_overlap or prior_overlap or cal_groups & dev_groups:
        raise ValueError(f"development prompt or template overlap detected: calibration={sorted(cal_overlap)[:3]}, previous={sorted(prior_overlap)[:3]}, templates={sorted(cal_groups & dev_groups)[:3]}")
    if len({r["id"] for r in calibration + development}) != len(calibration) + len(development):
        raise ValueError("duplicate case ID")
    if any(r["family"] == "git_read_status" and r["expected_status"] == "accepted"
           and not re.search(r"\btracked\b", r["prompt"].casefold()) for r in calibration + development):
        raise ValueError("tracked-only positives must state tracked-path scope")

    OUTPUT.mkdir(parents=True)
    write_jsonl(OUTPUT / "calibration.jsonl", calibration)
    write_jsonl(OUTPUT / "development.jsonl", development)
    manifest = {
        "schema": "wrench.system-one-v8-authored-data.v1",
        "status": "frozen_before_v8_candidate_training",
        "executor_scope": "git status --short --branch --untracked-files=no; no path/status filters",
        "system_capability_note": SCOPE_NOTE.strip(),
        "base_calibration_manifest": "internal/system-one-v7-data/data-manifest.json",
        "base_calibration_sha256": digest(BASE / "calibration.jsonl"),
        "v7_development_used_for_wording_direction_only": True,
        "v7_development_used_for_labels_or_threshold_selection": False,
        "prior_development_sha256_for_overlap_audit_only": {str(p.relative_to(ROOT)): digest(p) for p in PREVIOUS_DEVELOPMENTS + [BASE / "development.jsonl"]},
        "sealed_final_split_read": False,
        "calibration": {"rows": len(calibration), "sha256": digest(OUTPUT / "calibration.jsonl"), "family_label_counts": {f: dict(Counter(r["expected_status"] for r in calibration if r["family"] == f)) for f in sorted({r["family"] for r in calibration})}, "new_matched_template_groups": len(CAL_GROUPS)},
        "development": {"rows": len(development), "sha256": digest(OUTPUT / "development.jsonl"), "family_label_counts": {f: dict(Counter(r["expected_status"] for r in development if r["family"] == f)) for f in sorted({r["family"] for r in development})}, "template_groups": len(dev_groups), "exact_prompt_overlap_with_calibration": 0, "exact_prompt_overlap_with_prior_development": 0, "template_group_overlap_with_calibration": 0},
    }
    (OUTPUT / "data-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "calibration_rows": len(calibration), "development_rows": len(development), "calibration_sha256": manifest["calibration"]["sha256"], "development_sha256": manifest["development"]["sha256"], "status": manifest["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
