# CodeScaleBench pinned release and comparison runbook

## Selection fit

CodeScaleBench is selected because its paired design asks a question directly relevant to Wrench: what changes when the same coding agent gets an additional retrieval/context tool? Wrench can participate as a bounded, read-only context tool while the benchmark's downstream coding agent retains its existing sandbox permissions. The public Claude Code plus Haiku 4.5 results are outside references, not Wrench results.

## Frozen source identity

- Repository: https://github.com/sourcegraph/CodeScaleBench
- Release tag: `v1-mixed371`
- Resolved commit: `cac154c9384a78702092aaad76d29b1ac50d2982`
- Suite: `benchmarks/suites/csb-v1-mixed371.json`
- Suite SHA-256: `81f372bf5180de364a0411adfa25844ca35240e76a54bcfc4f351d2af0fc8db0`
- Suite counts: 372 JSON rows, 251 active, 120 backup, 1 missing; baseline and MCP result flags each cover 371 rows, with 370 rows in both.
- Checked-in snapshot: `runs/snapshots/csb-v1-mixed371--haiku45--030326/SNAPSHOT.json`, SHA-256 `e658484d51df88af722945a0b9fc926a8bd0b618cd0d91960edb560c52edd5da`.

The pinned README describes 275 tasks, which conflicts with the frozen suite JSON and checked-in snapshot. Treat the suite JSON and snapshot artifacts as authoritative for this release, and retain the README mismatch as a lineage note. The two unmatched suite rows are a baseline-only active element-web task and an MCP-only missing webclients task.

## Outside reference results

The checked-in snapshot aggregate has 371 results per configuration. It reports mean reward 0.5357 for local-direct baseline and 0.5647 for Sourcegraph MCP, with mean agent time 267.7 s and 158.1 s respectively. Its aggregate file SHA-256 is `bd6c919630e5561afd113e8672fdccc9dd2c7a0e237d5d911fc47112e56897a9`.

The current official technical report presents different analysis populations: 370 matched reward pairs, paired reward delta +0.0349 (95% CI +0.0130 to +0.0579), and 392 cost pairs with estimated cost $0.7333 vs $0.5121 per task (-30.16%). Its curated retrieval set has 329 rows and P@10 0.095 vs 0.313, R@10 0.120 vs 0.272, and F1@10 0.091 vs 0.240. These are distinct report views and denominators. Do not combine snapshot reward means with technical-report cost estimates into a synthetic matched result.

Source for the current technical report: https://github.com/sourcegraph/CodeScaleBench/blob/public/docs/technical_reports/TECHNICAL_REPORT.md

## Wrench comparison protocol

A valid direct comparison needs the same outside coding agent/model, prompt, task IDs, sandbox image, verifier, and scoring implementation across local baseline and Wrench-tool arms. Report task-level reward and safety with paired intervals, retrieval precision/recall/F1, wall and agent time, and cost. Label unmatched tasks and missing result records explicitly. Preserve Wrench's read-only authority; do not give it shell, credentials, or file-write permission.

Current state: release source is pinned and published references are recorded. Wrench has no adapter or matched run yet. A direct same-model run may incur provider cost, so it requires separate user authorization. No paid provider was called in this phase.

## Local checkout note

The ignored `upstream/` checkout is sparse and contains the pinned suite and evaluator sources. The snapshot identity above was verified from the upstream Git tree. Do not treat inner checkout working-tree status from the interrupted initial Windows long-path checkout as a result artifact; the outer phase records immutable commit and file hashes instead.

The pinned tree's `Dockerfile.eval` and `docs/EVAL_KIT.md` do not currently
form a runnable kit: `Dockerfile.eval` copies `configs/csb_quick.json`, but
that path is absent from the pinned Git tree. The selected v1 suite JSON and
Harbor task definitions are present. Until a complete pinned runner and
matched Wrench tool adapter are available, treat CodeScaleBench as a selected
comparison design with a published outside reference, not as a completed
Wrench score. No API-backed solver run has been made.
