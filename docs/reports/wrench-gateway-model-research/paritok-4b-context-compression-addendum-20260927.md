# Research addendum: coding-agent context compression LoRA (2026-09-27)

## Decision

Paritok-4B is the closest published task match found so far for a Wrench LoRA
that selects and compresses coding-agent context. Treat it as an external
method and evaluation reference, not as evidence that Wrench reaches its
95/5, 95%-cheaper, or all-day engineering goals, and not as the selected Wrench
checkpoint. Keep the current staged 0.8B Wrench-specific candidate first; use
the 2B candidate only as a capacity challenger when an admitted 0.8B run shows
a specific failure. Paritok's 4B setup has a reported single-24-GB-GPU target,
while this host has a 16-GB RTX 5060 Ti.

## Evidence

The authors describe Paritok as an intent-conditioned, extractive LoRA
compressor based on Qwen3-4B. Their paper says a GPT-4.1-mini teacher was
distilled over 67,074 OpenHands trajectories into 40,606 validated examples.
On all 300 SWE-bench Lite instances, compressed context was 25.7% of raw
context, a 74.3% content reduction, while the reported solve-quality retention
was 86.5%. With line-numbered tool input, context was 27.8% of raw (72.2%
reduction) and solve-quality retention was 89.3%; 30 instances were solved
only without compression and 17 only with compression, with exact McNemar
`p=0.079`. That failure to reject a difference at this sample size is not a
non-inferiority result and does not prove equal solve quality. The authors
report that 96.2% of identifiers, paths, and numbers emitted on held-out
SWE-bench Lite were present in the input, and describe the adapter as 264 MB
with a single 24-GB GPU self-host target. [Paper](https://arxiv.org/abs/2608.24188)

The model card identifies the base as `Qwen/Qwen3-4B-Instruct-2507`, Apache
2.0 adapter, LoRA rank 32 / alpha 64, 2,000 selected training steps, bf16,
8-bit AdamW, sequence length 16,384, and GPT-4.1-mini as teacher. It explicitly
warns that solve quality trades off by about six percentage points for the
compression, that rare identifier preservation falls to about 40% on hard
out-of-distribution segments, and that the training distribution is
English- and Python-heavy. It recommends identifier checks and raw-context
fallback. Those figures reinforce Wrench's requirement to keep exact originals
retrievable and validate every compressed result. [Model card](https://huggingface.co/paritok/paritok-4b-v1)

The repository's session-savings table reports 25% at turn one and 39% over
five turns. Values after that are projections: it estimates about 72% for its
default configuration, about 78% for an MCP-heavy configuration, and 85%+
against a context-saturated, compacted baseline. These figures combine its
tool filtering and content compressor under the stated assumptions. They are
not 95% savings, a Wrench evaluation, or a measured all-in cost reduction
including local compute, training, hardware, latency, and human rescue.
[Author evaluation and calculation](https://github.com/Paritok-official/paritok-4b-v1)

## Implication for Wrench

The research supports the narrow division of labor already in the experiment:
use a small LoRA for task-conditioned selection of source-backed spans, while
deterministic Wrench code retains the original tool output, performs exact
span retrieval, validates identifiers and references, assembles context, and
falls back to the original on uncertainty. It does not support asking a small
compressor to implement features, debug a repository, or sustain a workday by
itself. Evaluate mechanical coverage separately from end-to-end repository
completion.

Do not download or train Paritok as part of this research update. It requires
its exact Qwen3-4B-Instruct-2507 base; its adapter cannot be assumed compatible
with Wrench's different Qwen3.5-4B snapshot. Any later candidate proposal
needs a pinned full-file inventory, revision and license review, storage
reservation, runtime/resource admission, and separate authorization before
training.

## SubRoute boundary observed this iteration

At the owner's direction, read-only GETs to `http://127.0.0.1:4000/v1/models`
and `/api/active-model` both returned HTTP 200. The active-model endpoint
reported `active_model=openrouter`, `mode=force`, and `policy_version=4`.
This establishes local route availability only. It does not show which upstream
provider/model a generation would select, billed usage, or an aggregate budget.
No generation request was sent. Keep paid calls closed until a numeric
campaign cap is provided and the caller-side guard and durable usage/billing
receipt path are verified.

## Sources

- Shi and Chen, [Paritok-4B: Intent-Conditioned Context Compression for Coding Agents](https://arxiv.org/abs/2608.24188), 2026-08-25.
- [Paritok-4B-v1 model card](https://huggingface.co/paritok/paritok-4b-v1).
- [Paritok-4B-v1 evaluation, code, and session-savings calculation](https://github.com/Paritok-official/paritok-4b-v1).
- [Qwen3-4B-Instruct-2507 base model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507).
