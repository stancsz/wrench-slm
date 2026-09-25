# Local task acceptance envelope

Date: 2026-09-25 (America/Edmonton)

## Decision

Current local acceptance covers deterministic retrieval and observation
mechanics on explicit synthetic snapshots, plus four bounded review-only patch
draft operations under exact textual instructions. No semantic local SLM task
class is accepted. These mechanics results do not count as completed coding
work or real-work utility.

| Work family | Current evidence | Accepted scope |
| --- | --- | --- |
| Bounded exact file read | Route and independent executor matched 7/7 completed fixture observations; missing, stale, and ambiguous cases abstained correctly. | Exact requested file bytes on the supplied snapshot, within the tested byte limit. |
| Bounded line-range read | Route matched 6/6 cases; executor returned exact lines for 2/2 answerable cases; 4/4 boundary cases abstained. | Exact requested line ranges on the supplied snapshot. |
| Literal search | Included in the 7/7 read/search executor observations, including a positive and an empty result. | Exact literal results over the bounded supplied snapshot, not repository-wide or semantic search. |
| Review-only patch-operation drafts | Screen 01 matched exact diffs and independent target application on 12/12 positives: replacement 3/3, append 3/3, insert-after 3/3, and explicit whole-line removal 3/3. All 9/9 boundaries abstained and all fixture trees stayed unchanged. | Exact replacement of one unique literal, append as a new final line ending in LF, insertion after one unique single-line anchor, or removal of one uniquely matched whole line when explicitly requested. Small UTF-8 LF files only; draft mechanics only. See [screen 01](patch-operations-screen-01.md). |
| Git status, health read | Proposal recognition only in the 176-case route screen. | Not accepted for local execution yet. |
| Open-ended or multi-file review-only patch work | Screen 02 produced 3/4 exact positive drafts and passed all 6/6 deterministic boundary abstentions. One positive failed the exact diff and target oracle despite a deep TTC pass. | Not accepted. Screen 01 covers only its four explicit single-operation forms; it does not establish semantic patch correctness or accept open-ended or multi-file drafting. See [screen 02](patch-draft-screen-02.md) and [operations screen 01](patch-operations-screen-01.md). |
| Semantic work by the pinned Qwen 0.8B SLM | Run 02 scored 0/10; every measured class scored 0/2, with no required evidence-tool calls. | No accepted local SLM task class. Training stays stopped. |

## Acceptance rule

For deterministic operation mechanics, require exact frozen outcomes for every
answerable case, correct evidence-based abstention on every boundary case, and
zero unsafe dispatches, source mutations, or unresolved runtime errors. Keep
proposal recognition separate from executor behavior. For a review-only patch
screen, additionally require the exact allowed file list and diff, a verifier
pass, `review_only=true`, `applied=false`, and an unchanged source tree. Such a
pass would establish draft mechanics only, not a correct fix or completed
coding task.

For an SLM task class, require every held-out case to complete with the exact
independent outcome, use required evidence tools, ground claims in those tool
results, and produce no prohibited actions. Any failed member leaves the class
unaccepted. The exposed fixture used by the current Qwen run cannot be reused
to tune or train.

## Evidence and limits

- Deterministic reads and searches: [operation screen 02](local-exec-acceptability-02.md).
- Line ranges: [operation screen 03](local-read-lines-acceptability-03.md).
- Proposal-only families: [work envelope 01](local-work-envelope-20260924-01.md).
- Local SLM: [Qwen run 02](local-slm-run-02.md).
- Generic review-only patch draft: [screen 01](patch-draft-screen-01.md) failed its
  exact positive-oracle rule at 1/3; its route repairs were followed by screen
  02. Screen 02 passed 3/4 positive drafts and all 6/6 boundaries, but its
  removal case failed the exact oracle. Generic patch drafting remains
  unaccepted. The separate explicit whole-line screen matched 3/3 positives,
  independently applied 3/3 exact diffs, and passed 6/6 boundaries; it accepts
  only that narrow draft operation. See the
  [repair follow-up](patch-draft-screen-01-followup.md) and
  [screen 02](patch-draft-screen-02.md) and
  [whole-line screen 01](patch-whole-line-screen-01.md). The fresh
  [patch-operations screen 01](patch-operations-screen-01.md) matched all 12
  positive diff/application oracles and passed all 9 boundaries across the
  four explicitly supported operations. Its scope is deterministic draft
  mechanics only.
- Real utility and observed frontier savings remain unmeasured. The paired
  reporter has zero eligible matched usage pairs, so the average per-task
  frontier-token savings is **N/A**, not zero.

The separate M3 tokenizer proxy compares synthetic prompt sizes. It does not
measure these acceptance outcomes and is not a gate for which work can run
locally. Its current unrun protocol is under review for evidence-binding and
route-oracle gaps; no M3 proxy result is used here.

## Next measurement

The fresh operation screen completes the predeclared replacement, append,
insert-after and explicit whole-line removal mechanics matrix. Its narrow
acceptance boundary is recorded above; open-ended and multi-file patch work
remain unaccepted. Further local work should first preregister a separate
operation with an exact executor oracle and boundary cases. No semantic local
SLM task class is accepted; run 02 failed every measured class, and training
stays stopped. An SLM screen still needs separate authority for inference and
a task hypothesis with cases not exposed to training or tuning.
