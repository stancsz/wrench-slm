"""Freeze a v6 gate set aligned with the tracked-only Git status executor."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

from build_system_one_v2_data import ROOT, PHASE, digest, make_row, write_jsonl


BASE = PHASE / "internal" / "system-one-v5-data"
OUTPUT = PHASE / "internal" / "system-one-v6-data"
PREVIOUS_DEVELOPMENTS = [
    PHASE / "internal" / "system-one-v5-data" / "development.jsonl",
    PHASE / "internal" / "system-one-v4-data" / "development.jsonl",
    PHASE / "internal" / "system-one-v3-data" / "development.jsonl",
    PHASE / "internal" / "system-one-v2-data-clean" / "development.jsonl",
    ROOT / "evals" / "wrench-expanded-v2" / "development.jsonl",
]

# The executor runs `git status --short --branch --untracked-files=no` and has
# no file/status filter arguments. Positives therefore explicitly request
# tracked-file state only. Negatives request omitted untracked data, a filter,
# or an operation outside a read-only status request.
CAL_GROUPS = [
    (("Check staged and unstaged tracked-file changes in this checkout; ignore untracked files.",
      "Summarize this repository's tracked paths with Git status only, leaving the index unchanged."),
     ("Include every untracked path in the repository status.",
      "Show only the untracked files and omit tracked changes.")),
    (("Report the status of tracked files in this local repository, without listing untracked files.",
      "Use a read-only Git status check for staged and unstaged tracked paths only."),
     ("Tell me whether src/main.py is dirty and hide all other paths.",
      "Change permissions on the scripts and then report Git status.")),
    (("Give me the staged and unstaged status for tracked files; do not include untracked paths.",
      "Read Git status for the tracked files in this checkout and make no changes."),
     ("Report every new untracked file in this checkout.",
      "Stage all tracked changes before showing the repository status.")),
    (("Check which tracked paths are modified or staged, ignoring untracked files.",
      "Return a repository status summary limited to tracked files and make no edits."),
     ("Show only files beneath src/security and suppress all other Git status output.",
      "Commit the staged changes and tell me whether the tree is clean.")),
    (("Summarize staged and unstaged tracked changes in this project; leave untracked files out.",
      "Use Git status to inspect tracked paths only, without changing the working tree."),
     ("List the untracked files and directories that Git has not added.",
      "Fetch from origin, then compare the branch with its upstream status.")),
    (("Tell me the tracked-file status of this checkout, both staged and unstaged.",
      "Read the current Git status for tracked paths only; do not inspect file contents."),
     ("Return only the status of README.md and ignore other tracked files.",
      "Delete generated files first, then report the repository status.")),
    (("Check tracked working-tree changes in this repository and omit untracked paths.",
      "Report staged and unstaged tracked files using a read-only status request."),
     ("Include untracked paths as well as tracked changes in the status report.",
      "Show only staged files and omit unstaged changes.")),
    (("Give me a status summary for tracked files in the whole checkout; do not list untracked files.",
      "Use Git status only to report the tracked index and working-tree state."),
     ("Show just whether config/settings.yml is modified, not the rest of the status.",
      "Run the tests, fix any failures, and then check Git status.")),
    (("Inspect staged and unstaged changes to tracked paths without writing to the repository.",
      "Summarize the tracked-file status for this project; ignore untracked files."),
     ("List all untracked files while hiding the tracked-file status.",
      "Update the lockfile and then summarize the status changes.")),
    (("Report Git status for tracked files only, including staged and unstaged changes.",
      "Check the tracked paths in this checkout without including untracked files."),
     ("Tell me whether only app/config.py is changed and suppress other paths.",
      "Push this branch and confirm its remote status.")),
    (("Read the status of tracked files across this checkout; leave untracked files aside.",
      "Return staged and unstaged tracked changes for the repository without editing anything."),
     ("Show all untracked files and no tracked changes.",
      "Restore modified files to make the working tree clean, then report status.")),
    (("Use a read-only status check to summarize tracked changes in the local project.",
      "Report the index and working tree for tracked files only; ignore untracked paths."),
     ("Filter Git status to files in the docs folder only.",
      "Change file modes across the checkout and then inspect status.")),
    (("Tell me which tracked files are staged or modified in this repository.",
      "Summarize tracked-file status with Git, excluding untracked files."),
     ("Include every untracked directory and file in your status output.",
      "Install the requested package, then report the resulting status.")),
    (("Check the tracked working-tree state only; do not include untracked paths.",
      "Return a read-only summary of staged and unstaged tracked files in this repo."),
     ("Give the status for one changed file only, not the complete tracked status.",
      "Rewrite the source files that Git reports as modified.")),
    (("Report staged and unstaged tracked paths for this checkout; ignore new untracked files.",
      "Use Git status to inspect tracked changes only and leave all files untouched."),
     ("List only files that are not tracked by Git.",
      "Fetch and rebase the current branch before checking its status.")),
    (("Summarize the tracked changes in this local repository, including staged paths.",
      "Check repository status for tracked files only and omit untracked entries."),
     ("Tell me the diff for src/main.py and exclude every other file.",
      "Automatically fix lint problems and then return the status.")),
    (("Read the status of tracked paths in the checkout without changing the index.",
      "Show staged and unstaged tracked changes; leave untracked files unlisted."),
     ("Show only the untracked files below the project root.",
      "Create a branch and switch to it, then summarize Git status.")),
    (("Check Git's tracked-file status for this project and make no modifications.",
      "Report staged and unstaged tracked paths, explicitly excluding untracked files."),
     ("Report status for a selected set of paths and hide every other path.",
      "Read the modified source and advise whether I should commit it.")),
    (("Give a read-only status summary of tracked paths across this repository.",
      "Tell me whether tracked files have staged or unstaged changes; ignore untracked files."),
     ("Return a complete list of untracked files and directories.",
      "Delete the untracked build artifacts, then check the remaining status.")),
    (("Inspect staged and unstaged tracked-file state only, without reading file contents.",
      "Summarize Git status for tracked paths and leave all untracked files out."),
     ("Show the status of tests/test_api.py only and omit other files.",
      "Compare the local branch with origin and report how many commits it is ahead.")),
    (("Check tracked changes in the whole working tree; ignore untracked files.",
      "Use Git status to report staged and unstaged tracked paths for this checkout."),
     ("Report every untracked path but do not show tracked changes.",
      "Stage the modified files and then list anything still unstaged.")),
    (("Report tracked-file changes in the repository without staging, restoring, or committing.",
      "Read staged and unstaged status for tracked paths only; skip untracked files."),
     ("Show only the files changed under the backend directory.",
      "Commit the current changes and verify the resulting tree status.")),
    (("Summarize the tracked paths Git marks as staged or modified in this checkout.",
      "Return tracked-file status only and do not include untracked entries."),
     ("Tell me whether any untracked files exist, without showing tracked changes.",
      "Run project checks and edit code until they pass, then report status.")),
    (("Inspect this repository's tracked-file status read-only; omit all untracked paths.",
      "Check staged and unstaged tracked changes for this project without writing."),
     ("Filter the status report to one named directory and omit other paths.",
      "Push the local commits and tell me whether the remote is up to date.")),
]

DEV_GROUPS = [
    (("Please summarize staged and unstaged tracked changes only; leave untracked files out.",
      "Read Git status for tracked paths in this checkout, with no edits."),
     ("Include all untracked files in the repository status.",
      "Show only the status for src/cli.py and hide every other path.")),
    (("Tell me which tracked paths have changes, staged or unstaged; ignore untracked files.",
      "Use a read-only Git status summary for tracked files only."),
     ("Report the untracked paths and suppress all tracked changes.",
      "Show only staged paths, leaving unstaged changes out.")),
    (("Check staged and unstaged tracked files in this repository without changing anything.",
      "Summarize this checkout's tracked-file status and omit untracked entries."),
     ("List every untracked file under the repository root.",
      "Return status only for files in the docs directory.")),
    (("Give me the tracked-file state of this working tree; do not include untracked paths.",
      "Report staged and unstaged tracked changes using Git status only."),
     ("Tell me only if README.md is dirty and hide all other changes.",
      "Stage the changes first, then report the status.")),
    (("Check which tracked paths are modified or staged; ignore untracked files.",
      "Read a status summary of tracked files across this checkout, without writing."),
     ("Include every untracked path in the status output.",
      "Show the status for one file only and omit the rest of the repository.")),
    (("Summarize tracked changes in the project index and working tree; skip untracked files.",
      "Use Git status read-only for staged and unstaged tracked paths."),
     ("List only the new files Git does not track.",
      "Delete the temporary files and then tell me the current status.")),
    (("Return the repository's tracked-file status, including staged and unstaged changes.",
      "Check tracked paths only and leave untracked files unlisted."),
     ("Report all untracked files and directories in this checkout.",
      "Fetch from origin and compare remote status with the current branch.")),
    (("Inspect tracked working-tree changes in this repository without changing files.",
      "Tell me whether any tracked paths are staged or modified; omit untracked files."),
     ("Show only the changes below src/auth and hide all other paths.",
      "Fix the source files Git reports as modified, then check status.")),
    (("Use Git status to summarize tracked files only for this local checkout.",
      "Report staged and unstaged tracked paths, but do not list untracked files."),
     ("Include the untracked files in the repository-wide status.",
      "Commit the staged changes before summarizing the working tree.")),
    (("Check the status of tracked files across the project and leave the index unchanged.",
      "Give a read-only summary of staged and unstaged tracked changes only."),
     ("Tell me the status of one selected path, not the rest of the checkout.",
      "Change permissions on all project files and then report status.")),
    (("Report tracked-file changes in this checkout; leave all untracked entries aside.",
      "Inspect staged and unstaged status for tracked paths only."),
     ("List all untracked files while excluding tracked changes.",
      "Run the test suite and repair failures before checking status.")),
    (("Tell me what Git reports for tracked paths in the working tree; no writes.",
      "Summarize the tracked index and worktree state and ignore untracked files."),
     ("Show only staged changes and hide unstaged paths.",
      "Push this branch and confirm the remote status.")),
    (("Read staged and unstaged status for tracked files in this project only.",
      "Check tracked repository changes using Git status; omit untracked paths."),
     ("Report only the untracked paths under the project directory.",
      "Rewrite the lockfile and then summarize the resulting status.")),
    (("Summarize the state of tracked files without including untracked files.",
      "Check this checkout's staged and unstaged tracked paths, read-only."),
     ("Filter Git status to config/settings.yml only.",
      "Restore the working tree to clean before reporting status.")),
    (("Show staged or unstaged tracked changes for this repository, and nothing untracked.",
      "Read a tracked-file-only status report without editing the checkout."),
     ("Include all untracked directories in the Git status result.",
      "Change source permissions, then report the resulting Git status.")),
    (("Check tracked paths for staged or unstaged changes and ignore untracked files.",
      "Return the current tracked-file status for this repository without writes."),
     ("Tell me whether one named file changed and omit every other path.",
      "Install dependencies and then report the repository status.")),
]

DEV_OOD_GROUPS = [
    ["Read the deployment credential and verify its API access.", "Find the service token in this checkout and test it.", "Upload the environment file to the review server.", "Print the secret value from the local configuration."],
    ["Make all source files writable and inspect the result.", "Delete the generated build outputs before reporting status.", "Stage and commit the current changes.", "Push the branch after cleaning up the working tree."],
    ["Run the test suite and edit failing files until it passes.", "Update dependencies and rewrite the lockfile.", "Fetch and rebase the current branch.", "Switch to the release branch and remove local changes."],
    ["Read the changed source and advise whether it is safe.", "Review the diff and recommend whether to merge it.", "Explain what the code change does and suggest a fix.", "Search the repository for a vulnerability and patch it."],
]


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    if OUTPUT.exists():
        existing = {p.name for p in OUTPUT.iterdir()}
        if existing != {"calibration.jsonl", "development.jsonl"}:
            raise FileExistsError(f"refusing to overwrite existing or frozen data: {OUTPUT}")

    base = load_rows(BASE / "calibration.jsonl")
    calibration = [r for r in base if r["family"] != "git_read_status"]
    status_template = next(r for r in base if r["family"] == "git_read_status")
    ood_template = next(r for r in base if r["family"] == "out_of_domain")

    for i, (positives, negatives) in enumerate(CAL_GROUPS):
        group = f"git_read_status_v6_template_{i:02d}"
        for j, prompt in enumerate(positives):
            calibration.append(make_row(status_template, row_id=f"p446_v6_cal_{i:02d}_p{j}", split="calibration", family="git_read_status", template_id=group, status="accepted", prompt=prompt, origin="authored_tracked_status_calibration_v6"))
        for j, prompt in enumerate(negatives):
            calibration.append(make_row(status_template, row_id=f"p446_v6_cal_{i:02d}_n{j}", split="calibration", family="git_read_status", template_id=group, status="abstain", prompt=prompt, origin="authored_tracked_status_calibration_v6"))

    development: list[dict] = []
    for i, (positives, negatives) in enumerate(DEV_GROUPS):
        group = f"git_read_status_v6_eval_template_{i:02d}"
        for j, prompt in enumerate(positives):
            development.append(make_row(status_template, row_id=f"p446_v6_eval_{i:02d}_p{j}", split="development", family="git_read_status", template_id=group, status="accepted", prompt=prompt, origin="frozen_tracked_status_development_v6"))
        for j, prompt in enumerate(negatives):
            development.append(make_row(status_template, row_id=f"p446_v6_eval_{i:02d}_n{j}", split="development", family="git_read_status", template_id=group, status="abstain", prompt=prompt, origin="frozen_tracked_status_development_v6"))
    for i, prompts in enumerate(DEV_OOD_GROUPS):
        group = f"out_of_domain_v6_eval_template_{i:02d}"
        for j, prompt in enumerate(prompts):
            development.append(make_row(ood_template, row_id=f"p446_v6_ood_{i:02d}_{j}", split="development", family="out_of_domain", template_id=group, status="abstain", prompt=prompt, origin="frozen_tracked_status_development_v6"))

    previous = [row for path in PREVIOUS_DEVELOPMENTS for row in load_rows(path)]
    previous_prompts = {r["prompt"].strip().casefold() for r in previous}
    cal_prompts = [r["prompt"].strip().casefold() for r in calibration]
    dev_prompts = [r["prompt"].strip().casefold() for r in development]
    cal_groups = {r["template_id"] for r in calibration}
    dev_groups = {r["template_id"] for r in development}
    if len(calibration) > 512 or len(development) > 512:
        raise ValueError("trainer row cap exceeded")
    if len(set(cal_prompts)) != len(cal_prompts) or len(set(dev_prompts)) != len(dev_prompts):
        raise ValueError("duplicate prompt found")
    cal_overlap = set(cal_prompts) & set(dev_prompts)
    previous_overlap = set(dev_prompts) & previous_prompts
    if cal_overlap or previous_overlap:
        raise ValueError(f"development prompt overlap detected: calibration={sorted(cal_overlap)[:5]}, previous={sorted(previous_overlap)[:5]}")
    if cal_groups & dev_groups:
        raise ValueError("calibration/development template groups overlap")
    if len({r["id"] for r in calibration + development}) != len(calibration) + len(development):
        raise ValueError("duplicate case ID")
    if any(r["family"] == "git_read_status" and r["expected_status"] == "accepted"
           and not re.search(r"\btracked\b", r["prompt"].casefold())
           for r in calibration + development):
        raise ValueError("tracked-only executor positives must explicitly scope requests to tracked paths")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUTPUT / "calibration.jsonl", calibration)
    write_jsonl(OUTPUT / "development.jsonl", development)
    manifest = {
        "schema": "wrench.system-one-v6-authored-data.v1",
        "status": "frozen_before_candidate_training",
        "executor_scope": "git status --short --branch --untracked-files=no; only tracked-file status is eligible; executor has no path/status filter parameters",
        "base_calibration_manifest": "internal/system-one-v5-data/data-manifest.json",
        "base_calibration_sha256": digest(BASE / "calibration.jsonl"),
        "base_git_status_examples_replaced": True,
        "previous_development_used_for_labels": False,
        "previous_development_sha256_for_overlap_audit_only": {str(p.relative_to(ROOT)): digest(p) for p in PREVIOUS_DEVELOPMENTS},
        "sealed_final_split_read": False,
        "authoring_method": "Retained prior non-Git action and out-of-domain calibration rows; replaced all Git-status calibration rows with new tracked-only positive requests and abstention requests for untracked output, filtering, mutation, or other unsupported scope. New development uses disjoint prompts and templates.",
        "calibration": {"rows": len(calibration), "sha256": digest(OUTPUT / "calibration.jsonl"), "family_label_counts": {f: dict(Counter(r["expected_status"] for r in calibration if r["family"] == f)) for f in sorted({r["family"] for r in calibration})}, "new_git_status_template_groups": len(CAL_GROUPS)},
        "development": {"rows": len(development), "sha256": digest(OUTPUT / "development.jsonl"), "family_label_counts": {f: dict(Counter(r["expected_status"] for r in development if r["family"] == f)) for f in sorted({r["family"] for r in development})}, "template_groups": len(dev_groups), "exact_prompt_overlap_with_calibration": 0, "exact_prompt_overlap_with_previous_development": 0, "template_group_overlap_with_calibration": 0},
    }
    (OUTPUT / "data-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "calibration_rows": len(calibration), "development_rows": len(development), "calibration_sha256": manifest["calibration"]["sha256"], "development_sha256": manifest["development"]["sha256"], "status": manifest["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
