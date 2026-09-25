# Synthetic M3 context-token reduction protocol

Status: preregistered offline tokenizer study; no inference or provider use.

## Question

How many input tokens does the current deterministic E0 context path remove
from small Wrench-authored source tasks, compared with giving the same task's
complete synthetic source snapshot directly to the downstream prompt?

This is a synthetic prompt-size diagnostic. It is not observed frontier usage,
task utility, paid-cost savings, or an OpenCode runtime result.

## Frozen tasks and arms

- Fixture: `tests/fixtures/e0_synthetic_matched_tasks_v1/manifest.json`, pinned
  by its existing canonical SHA-256 in the fixture runner.
- Candidate cases: answerable `loc-a`, `loc-b`, `triage-a`, `triage-b`,
  `context-a`, `context-b`, and `evidence-specific`. Missing, stale, and
  ambiguous cases are outcome checks, not savings pairs.
- Baseline input: the frozen MiniMax M3 template receives the unchanged
  challenge system message and user question, plus every source file in that
  case's supplied synthetic snapshot as one context message.
- Wrench input: the same system message, user question, and model settings,
  with the context message emitted by the existing snapshot-bound E0
  route-to-preparation/materialization path from the same source snapshot.
- Count only exact tokenizer IDs for the complete rendered input through the
  generation prefix. Keep all non-context messages identical. Do not count
  generated output because no model call is made.
- Count a pair only if E0 preparation is ready and the prepared context
  contains every exact path and source quote required by the frozen host-side
  answer oracle. Failed or incomplete contexts are reported as excluded, not
  as token savings.

## Tokenizer identity and storage

Use the official `MiniMaxAI/MiniMax-M3` repository at immutable revision
`f0e1c1e04d40177e4673a22097036854f536e9c0`: tokenizer JSON/configuration,
special tokens, vocabulary, merges, chat template, model config, and license.
The selected nine files total 16,884,564 bytes. The complete model repository
has 82 files and 59 weight shards totaling 854,200,504,173 bytes, so the model
weights are out of scope and must not be downloaded. Keep tokenizer artifacts
and receipts under `C:\wrench-slm-data`; no Hugging Face cache copy is created.

Use the installed Transformers 5.17.0 and Tokenizers 0.23.2 runtime, verify
every selected file against the pinned repository inventory and byte size, and
load the tokenizer from the local snapshot only. Freeze the actual tokenizer
template hash and runtime lock identity in the receipt. A local model template
does not prove how OpenRouter's selected provider counts requests.

## Metric and reporting

For eligible task `i`, report prompt-input reduction
`100 * (1 - W_i / B_i)`, where `B_i` and `W_i` are exact MiniMax-tokenizer
counts for the baseline and Wrench rendered inputs. Report every paired task,
the arithmetic mean per task, the ratio-of-sums, the valid-pair count, and all
excluded tasks. A zero baseline or missing arm count is unavailable.

Report the result as a **synthetic M3-tokenizer input reduction**. Keep
`frontier_token_savings_percent` null and do not add this proxy to the paired
frontier-savings report. Real frontier savings require complete matched
provider usage receipts for both arms, full request lifecycle accounting,
an authorized route, and independent task outcomes.

## Stop conditions

Stop before scoring if the fixture hash, model revision, selected file
inventory, tokenizer/runtime lock, or request identities differ. Exclude a
task if its E0 context misses required answer evidence or either exact prompt
cannot be rendered. Do not train or tune on these open-development fixtures.
Retain only per-task token counts, outcome classes, identities, and
content-free hashes; do not persist rendered task prompts or tokenizer ID
sequences.
