# Pro training V4 boundary correction budget

Execution update: paused at saved step 300 of 450 at the user's request.
See [MODEL_TRAINING_NEXT_STEPS.md](MODEL_TRAINING_NEXT_STEPS.md) for verified
checkpoint hashes and exact resume instructions. The original budget below is
preserved; the remaining work is 150 steps, not a new 450-step run.

Prepared 2026-09-09. Release thresholds and inference contract remain unchanged.
No sealed release or independent challenge model evaluation has run.

V3 steps 100 and 200 each achieved 112/112 exact supported development tasks
and actual outcomes, but failed unsupported Chinese requests and some invalid
line boundaries. All V3 checkpoints must finish development evaluation before
selecting the initialization checkpoint under the existing exact-rate rule.

## Data and rationale

The V3 training corpus contains only four distinct unsupported-request prompts.
data/pilots/release-boundary-v4 retains all 4,548 V3 records, adds 768 examples
from 32 new English/Chinese unsupported-request prompts, and adds 768 examples
from 12 new paired range wordings. Range pairs include valid positive bounds,
zero, reversed bounds, and negative starts; valid labels have actual fixture
lines. This teaches the declared tool scope and one-based range semantics.

There are 6,084 training rows in 100 training families, equally split by language.
The training SHA-256 is
61643804bae59e6b70fd194fbeac65014eca788402fd62345e8d0bcbb0e5f4ac.
Development and evaluation files are byte-identical to the prior versions.
No scored development example or independent challenge example is copied into
training. The data preflight passes; 12 representative positive range families
pass real fixture outcome checks, including rejection of an overbroad read.

## Bounded run

- Initialize from the V3 checkpoint selected after all three development runs.
  Record its exact adapter hash in the V4 run receipt and reset the optimizer.
- Preserve base revision, tokenizer, prompt formatter, LoRA configuration,
  unconstrained greedy inference, and all numeric release thresholds.
- At most 450 optimizer steps, microbatch 2, accumulation 8, learning rate
  0.00002, seed 42, BF16, maximum length 1536: 7,200 presentations at most.
- GPU allocator cap 55%, local RTX 5070 Ti, zero cloud calls, no automatic retry.
  Maximum 60 minutes including checkpoint writes and validation.
- Save checkpoints at 150, 300, and 450 steps. Evaluate all on unchanged
  development data, then select by highest exact rate, lowest validation loss,
  and earliest step. Do not select by training loss or omit a failed case.
- Require all fixed development gates, at least 95% exact on the 37 context
  development probes, and the packaged quickstart before independent evaluation.
- Further training requires another recorded budget. A failed scored independent
  test used to guide changes must be retired before a fresh release decision.

Completing the run does not approve the weights for release.
