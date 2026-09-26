# Localization screen 02: E0 tokenizer profile attempt

Status: **stopped before tokenizer loading and case scoring; no measurement result**

- Date: 2026-09-26
- Goal: [Measure acceptable local work](../../goal/wrench-local-acceptability/GOAL.md)
- Job: `WRENCH-E0-LOCAL-MEASURE-20260926-03` / nonce `E0M-3C-91`
- Revision at start: `7956a77905c4dbb5845ae500d6ebe1a5d525fd1a`

## Deliverable

Added opt-in profile `localization-screen-02` to
`tools/measure_synthetic_context_token_reduction.py`, a separate admission
identity, a fresh synthetic fixture, focused tests, and the frozen protocol at
[`localization-screen-02-protocol.md`](../../evals/wrench-local-acceptability/localization-screen-02-protocol.md).
The profile will compare full-source prompts with E0-prepared context using the
already pinned MiniMax M3 tokenizer. It has four positive source-localization
cases requiring exact path, hash, function, line, and quote evidence. Four
separate boundaries cover missing path, stale snapshot data, unsupported route,
and over-budget required context.

Token reductions are eligible only after route/preparation identity and all
source evidence checks pass. The receipt reports per-case reductions, arithmetic
mean, ratio-of-sums, and boundary outcomes. Frontier-token savings remains
null. The profile performs no model generation.

## Findings and limits

The historical E0 localization cases `loc-a` and `loc-b` each lacked one
required evidence item, so they were excluded from the earlier synthetic
tokenizer reduction. The receipt does not preserve source or prompt text, so a
more specific internal cause is not established. The separate local-model
screen failed to make required evidence-tool calls and asserted unsupported
answers. Neither exposed screen was used to tune the fresh fixture.

The new screen has not produced a token-reduction number. A one-shot attempt
from clean revision `de8bdddf3a30fa93db9c06974f7fb737cbe17743` passed its
fixture and runner pins, then stopped before tokenizer import because
`tools/wrench-local-runtime-windows-cp313.lock` was checked out with CRLF. The
protocol's expected LF-normalized SHA-256 is
`0ed35342ae184741886fff2764f87c44df8babfde3912c54a9e1cd73ffbf2420`; the raw
Windows checkout SHA-256 was `7be9a7de4f27d220a0f07b1711a92e0acae4a748e08c3ead4e24fad4bc8cba2e`.
The runner stopped before tokenizer loading or case iteration. There are no
token counts, scored cases, or receipt. The fixture was loaded during profile
admission and is exposed; do not rerun or tune against it. A future measurement
needs a fresh fixture and a line-ending-stable runtime-lock check. Frozen
protocol 06 and its historical receipt remain unchanged.

No model, training, client, provider, endpoint, network download, or tokenizer
measurement completed. There is still no evidence of semantic SLM task
acceptance or frontier-token savings.

## Review and verification

An independent static critic passed the profile with one evidence limitation:
the Luna consultation token counts recorded in the protocol are advisory and
unverified because a consultation receipt was not retained. The reviewer
confirmed the unchanged legacy no-argument dispatch, the derived over-budget
evidence IDs and fabricated-ID rejection, global worktree cleanliness gate,
source dependency hashes, fresh fixture, and token aggregation.

Root independently invoked all five focused test functions with `python -B`;
all passed. The environment does not have `pytest` installed. `git diff --check`
passed. Canonical fixture SHA-256 matches the protocol pin:
`b7bc026058361e70edcafcb230f8427a8f9a55630510fdef1323674bd7b0c368`.

Storage status after the checks was `WITHIN_LIMIT`: 10,939,360,669 actual
bytes, 22,103,000 bytes reserved, and 39,038,536,330 bytes of remaining
headroom. After the task and consultation stopped, their two reservations were
released. Final status was `WITHIN_LIMIT`: 10,939,362,649 actual bytes,
1,103,000 bytes in other active reservations, and 39,059,534,350 bytes of
headroom.

## Next action

Do not rerun this exposed fixture. First make runtime-lock identity line-ending
stable, then author and freeze a new independent fixture and protocol. Repeat
storage and host-resource admission from a clean source tree before that future
tokenizer-only measurement. Model inference, semantic SLM acceptance, real-task
capture, and provider-backed savings remain outside this profile.
