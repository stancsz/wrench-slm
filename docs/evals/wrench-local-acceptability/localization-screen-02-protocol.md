# Localization screen 02: E0 tokenizer profile

Status: **attempt stopped at runtime identity gate; no tokenizer cases scored**

- Profile ID: `localization-screen-02`
- Job ID: `WRENCH-E0-LOCAL-MEASURE-20260926-03`
- Nonce: `E0M-3C-91`
- Fixture: `tests/fixtures/localization_screen_02.json`
- Fixture canonical SHA-256: `b7bc026058361e70edcafcb230f8427a8f9a55630510fdef1323674bd7b0c368`
- Runner: `tools/measure_synthetic_context_token_reduction.py`
Runner SHA-256: `74326ef888892934dc514bdb353fe63e230f2a537a5c081b7126d18ddbbe42c2`
The runner hash is over UTF-8 source with CRLF normalized to LF.
- Runtime lock SHA-256: `0ed35342ae184741886fff2764f87c44df8babfde3912c54a9e1cd73ffbf2420` (CRLF normalized to LF)

## Question and claim boundary

For four fresh Wrench-authored synthetic source-localization tasks, how many
complete MiniMax M3 tokenizer input tokens does the E0 route-to-context path
prepare, compared with supplying every source file in the same complete prompt?
The four positives have exact host-side path, function, source-line, and quote
oracles. Four separate cases exercise missing path, stale post-snapshot source,
unsupported route, and E0 context-token-budget rejection.

This is a **tokenizer-only synthetic context reduction profile**. It loads no
model weights, generates no answer, contacts no client/provider/endpoint, and
does not measure downstream usage, billed cost, real work, generalization, or
frontier-token savings. The receipt must keep
`frontier_token_savings_percent` null and frontier usage counts zero. A token
reduction can be claimed only for a positive case where the route and
preparation identities join and every required source path and exact oracle
quote is visible in its snapshot-bound prepared context.

Luna consultation was reported as 186 completion / 434 prompt / 620 total
tokens. These counts are advisory and unverified because no retained
consultation receipt was available for this review. The recommendation was to
use a separate offline tokenizer-only E0 profile and explicit fixture
identity, with inference left outside the decision. `decision_changed=true`:
the planned measurement work is now constrained to this profile and does not
attempt client/generation capture.

## Frozen inputs and prompt arms

The fixture is independently authored synthetic Python and configuration-like
source text. Admission is a new one-entry structural pin in
`src/wrench_harness/synthetic_fixture_admission.py`; it is separate from and
does not alter the legacy matched-task schema, manifest hash, or review-receipt
validation. The fixture declares open-development usage, fresh synthetic
provenance, no parent manifest, no sealed/final split, and no utility claim.
Each source file has an exact UTF-8 SHA-256. The host derives all line text from
those bytes and verifies the required line quote against the exact numbered
source line.

For each positive case use the fixed system instruction in the profile runner
and the fixture's `task` as the user question. The baseline inserts every
complete snapshot source file, sorted and identity-labeled, into one untrusted
context message. The E0 arm sends the fixture's frozen `route_prompt` only to
the local snapshot-bound deterministic E0 route and context preparation path,
then inserts the resulting context message beside the identical system and
user messages. It does not invoke the fixture's `expected_function`, expected
path, line, or quote as route inputs. Count each full message list through the
generation prefix using the MiniMax M3 chat template.

Before a positive case is eligible, require exact route status/action/reason and
path set, route-to-preparation source-hash equality, a ready preparation, exact
complete context-section bytes for each required evidence source, selected
snapshot-derived evidence IDs, and each host-derived source-line quote within
the corresponding path/hash-bound section. Require tokenizer count parity
between the complete rendered prompt and the gate's recorded count. Any
failure excludes that task from both aggregate statistics and fails the
positive acceptance gate.

## Cases and boundary rules

The frozen positive cases are `loc02-positive-01` through `loc02-positive-04`.
Each has two source files so the baseline includes bounded distractor context;
the E0 route reads only the explicitly requested file. The exact function
identity is recorded host-side and paired with definition and operation
quotes.

Boundaries are excluded from token-saving pairs:

- `loc02-boundary-missing`: the requested path is absent from the supplied
  snapshot and must return `source_not_in_snapshot` with no prepared context.
- `loc02-boundary-stale`: mutate the source only after creating its immutable
  snapshot. The exact read must return `snapshot_read_changed` with no prepared
  context.
- `loc02-boundary-unsupported`: the natural-language inspect request has no
  supported path/action proposal and must abstain as
  `ambiguous_or_unsupported_request`.
- `loc02-boundary-context-budget`: route a required source normally but set the
  actual E0 `context_token_budget` to 1. Preparation must reject with
  `required_evidence_omitted`, omit the required evidence IDs, and return no
  prompt or context message. This uses the supported E0 context budget rather
  than a user-message byte-budget simulation.

Report all four boundaries and their individual outcomes. A boundary mismatch
fails acceptance but does not create a token-reduction pair.

## Tokenizer and accounting

Use only the existing hash-pinned MiniMax M3 tokenizer metadata, already
inventoried at `C:\wrench-slm-data\artifacts\wrench-local-acceptability\minimax-m3-tokenizer-f0e1c1e\tokenizer`, repository revision
`f0e1c1e04d40177e4673a22097036854f536e9c0`. The existing runner verifies all
nine selected metadata assets, source inventory and fetch receipt, the exact
chat-template hash, runtime lock, Python 3.13.15, Transformers 5.17.0,
Tokenizers 0.23.2, and huggingface-hub 1.33.0; it uses offline tokenizer
loading and does not fetch model weights. The fixture manifest and all new E0
profile/mechanics sources are separately hashed in the receipt.

For each eligible task `i`, let `B_i` be full-source baseline input tokens and
`E_i` be E0-prepared input tokens. Report per-case
`100 * (1 - E_i / B_i)`, the arithmetic mean of eligible task percentages, and
the ratio-of-sums `100 * (1 - sum(E_i) / sum(B_i))`. Report every excluded
case and reason, eligible count, positive evidence-quote pass count, and
boundary pass count. A positive token percentage does not imply correctness of
a generated answer or actual avoided frontier calls.

## Execution status and limits

Attempt `WRENCH-LOC02-E0-MEASURE-20260926-D` ran from clean revision
`de8bdddf3a30fa93db9c06974f7fb737cbe17743`, after fresh storage and host
admission. Runner and fixture pins matched, and the fixture was loaded for
admission. Tokenizer initialization then stopped at `runtime_lock_hash_mismatch`:
the frozen LF-normalized lock hash was `0ed35342ae184741886fff2764f87c44df8babfde3912c54a9e1cd73ffbf2420`, while the Windows checkout's raw CRLF hash was
`7be9a7de4f27d220a0f07b1711a92e0acae4a748e08c3ead4e24fad4bc8cba2e`. The
guard runs before importing or loading the tokenizer and before iterating any
case. No tokenizer counts, case scores, or receipt were produced. The fixture
is now exposed and must not be rerun or tuned against; a future profile needs a
fresh independent fixture and the CRLF-normalized lock identity check.

The attempt used no model, client, provider, or endpoint and generated no model
tokens. Its open-development fixture cannot support held-out generalization.

The legacy no-argument invocation, frozen IDs, fixture/admission validation,
and historical receipt contract remain unchanged in source behavior. The
legacy protocol 06 pins the prior complete runner source hash, so it correctly
rejects a repeat under this extended source until that legacy experiment is
separately re-pinned. Protocol 06 and its historical receipt were not modified.

This protocol grants no model inference, training, client installation,
provider traffic, real-task capture, spend, publication, or production
authority.
