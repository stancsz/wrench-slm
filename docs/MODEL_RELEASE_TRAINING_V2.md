# Pro training V2 budget and decision

Prepared 2026-09-09 from development evidence only. The V1 release evaluation
remains unscored and unchanged. The quality gates in MODEL_RELEASE_PROTOCOL_V1.md
remain binding; this document changes the training data and bounded run budget.

## Why another candidate may be needed

V1 steps 100 and 200 completed development checks and failed config selection
and invalid-range handling. Partial step-300 and step-400 development receipts
also contain failures. Do not start this run until all four V1 development
comparisons are complete and their selection report confirms that no candidate
passes the required quality gates. Do not infer a release verdict from partial
results or choose an easier task slice to remove failures.

The V1 training examples used different wording for valid and invalid line
ranges and for available and missing service selection. This allows wording
shortcuts. V2 introduces contrasting examples with the same wording and different
bounds/selection state, keeping both members in the same training family.

## Data and checks

data/pilots/release-context-v2 contains 3,076 authored training examples in the
same 44 parent training families. It adds minimal-context and available-tool
variants, valid/invalid line-bound pairs, and config reads with/without an
identifiable selected service. Reordered resources and selection of either
service reduce reliance on resource position.

The development and release evaluation files are byte-identical to V1. Additional
context-development-v1 probes are development-only and retain parent families.
The tokenizer/schema/length preflight passed, with no cross-split input or family
overlap. Auditing all 3,200 pre-deduplication derivatives found zero conflicting
labels and 124 identical duplicates. Seventeen focused tests cover contrast-pair
family preservation, selected-resource correctness, actual file outcomes, and
the encountered numeric-range replacement edge case.

## Bounded run

- Start from the same pinned Qwen2.5-0.5B-Instruct base, with fresh LoRA rank 16,
  alpha 32, dropout 0.05. This is not a resume across incompatible datasets.
- Microbatch 2, accumulation 4, constant learning rate 0.0001, seed 42, BF16,
  maximum sequence length 1536, on the RTX 5070 Ti.
- Cap this process's PyTorch CUDA allocator at 55% of device memory (about 9 GB).
  V1 observed peak allocated memory was 6.09 GB. This leaves room for desktop
  applications and a remaining small baseline inference process; it is not a
  promise about total driver/device memory.
- Maximum 600 optimizer steps and 4,800 example presentations, zero cloud calls.
  Save checkpoints and development validation loss at 200, 400, and 600 steps.
- Reserve at most 60 minutes including validation/save overhead. Investigate
  unexpected slow progress against the live handle; never restart on a poll timeout.
- No automatic retry. A failed run is preserved; recovery requires verified
  checkpoint identity and a separately recorded remaining budget.
- Compare all three checkpoints on the unchanged development set. Select highest
  development exact-call rate, then lowest validation loss, then earliest step.
  Evaluate the selected candidate on all 37 additional development context probes;
  require at least 95% exact predictions and a passing documented quickstart.
- If gates still fail, preserve the result and diagnose the specific remaining
  failures. Any further run needs a new recorded budget. Do not expand this into
  an unlimited training loop.

Only a candidate that passes development gates proceeds to the independent
challenge and sealed release evaluation. Clean loading of an earlier checkpoint
does not waive quality or final-package checks.
