# E0 ARB benchmark admission audit
> Supporting record only. Follow the [active goal](../wrench-token30/GOAL.md);
> this file's next-step text has no authority unless that goal's checkpoint
> adopts it as an evidenced dependency or the owner sets a new commitment.


Status: read-only source audit complete; dataset download remains unadmitted
Job: `W2-ARB-READONLY-ADMISSION-AUDIT-20260924`
Nonce: `ARB-SOURCE-AUDIT-7B4D`
Audited repository baseline: `b353e1a3d1bc81e11d08c8bbe7d3d22160694b1e`
Started: 2026-09-24 (America/Edmonton)

## Product outcome

Determine whether Agent Retrieval Bench (ARB) can serve as Wrench's first
external, file-level retrieval diagnostic without using it as training data or
as a substitute for consented end-to-end task outcomes. No archive or dataset
content is downloaded in this slice.

## Acceptance and result

- Current dataset revision and published artifact metadata are recorded in
  the [source audit report](../../reports/wrench-e0-arb-benchmark-admission/arb-source-audit.md).
- The self-contained subset release claim, track inventory, published sizes
  and hashes, license limits, outcome-oracle scope, and split limitations are
  reviewed against primary sources.
- The download decision names any missing evidence and does not infer an
  extracted size from compressed bytes.
- Independent read-only source review passed, and `git diff --check` passed for
  the working tree; user-owned North Star edits remain outside the commit.

Result: ARB is a plausible external retrieval diagnostic. Acquisition is
blocked until the selected archive's expanded inventory/peak and repository
and query-data provenance are established. The [evaluation review](../../evals/wrench-e0-arb-benchmark-admission/review.md)
records the decision.

## Scope and limits

The preferred diagnostic is `v2_trace2code`: 101 samples, 98 corpus rows and
356,074 chunks according to the release manifest, with all gold files reported
in corpus. Its published compressed archive is 39,295,446 bytes. These facts
do not establish an extraction peak, actual content hashes, license clearance,
or suitability as an E4 task-success oracle.

ARB's gold is file-level context relevance. Its token-packing metric uses
ARB's own tokenizer convention. It has no general train/dev/test split and
does not establish Wrench's final utility. Keep the public subset evaluation-
only, report per track and abstention stratum, and keep it quarantined from
training.

## Historical acquisition disposition

The proposed benchmark remains unadmitted and has no current acquisition
action. Its inventory, licensing and provenance findings are reference only.
Do not resume this study unless the [active goal](../wrench-token30/GOAL.md)
checkpoint names it as an evidenced dependency.
