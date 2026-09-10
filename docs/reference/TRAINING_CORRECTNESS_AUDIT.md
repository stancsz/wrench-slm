# Training correctness audit

Date: 2026-09-10
Scope: Historical audit of the V16 training and evaluation design.
Verdict at audit time: training machinery worked, but the V16 data and exposure
did not justify release readiness. V17 through V21 applied the repairs below;
the current closure evidence is recorded in [MODEL_RELEASE_PROGRESS.md](MODEL_RELEASE_PROGRESS.md).

## Critical findings

1. **V8 is no longer independent release evidence.** V14 predictions on V8 were inspected before V15 was authored; V15 predictions then informed V16. Reusing the same challenge and sealed files makes later scores diagnostic. Fresh identifiers or file paths alone also do not establish independent wording families. Earlier progress messages calling V8 fresh for V15 and V16 were incorrect. Freeze a new, independently authored holdout after correcting the training data. Keep it inaccessible to correction and checkpoint selection until the final candidate is frozen.

2. **The selected V16 checkpoint trained exclusively on invalid-range examples.** The loader streams sequentially without shuffling. Step 200 presents 3,200 examples (200 x 2 x 8). The V16 prefix contains 4,096 invalid-range examples before any routine examples, so the selected step 200 saw zero of the advertised routine preservation examples. V15 step 200 saw 2,048 invalid-range, 1,024 git-log, and 128 line examples. Neither selected candidate saw the inherited parent rows during its own run. Their parent weights retain earlier learning, but dataset size is not training coverage. Interleave a balanced, deterministic correction/replay stream and record exposure counts for every selectable checkpoint.

3. **The correction generators omit the actual failing bounds category.** V15 and V16 generate zero-start or reversed intervals. They do not generate positive, increasing bounds beyond the file length, such as the failing 999 through 1004 requests. More repetitions of the wrong category do not directly address the defect. Author observable invalidity: include file length in public context for out-of-file tests, or explicitly state that the request must be rejected. Test numeric boundary reasoning separately from obeying an explicit fallback instruction.

4. **V15 draft targets contain hidden information.** The 64 new draft prompts supply a destination but omit the content string that appears in the target. That content is absent from the public context. The final V15 checkpoint reaches these examples and has a large loss spike near step 290; this is consistent with the defect, although the audit does not prove it caused the regression. The selected step 200 never reached those examples. Remove or repair every such row before future reuse. Syntax preflight cannot detect this problem.

## Additional findings

- V15/V16 invalid-range path construction takes the first resource after resource-order reversal, sometimes selecting a decoy instead of the selected file. The fallback label survives, but the prompt/context relationship is inconsistent.
- New health examples retain the literal __PORT__ placeholder in training prompts and targets. Substitute concrete valid local URLs before training and verify the rendered public input.
- Correction prompts frequently name the exact command or instruct the exact fallback token. This can teach copying and compliance while inflating apparent task understanding. Evaluate natural requests and explicit-instruction requests separately.
- Development remains the same 176 authored cases across many adaptive rounds. Perfect development accuracy and very low teacher-forced loss are increasingly weak evidence of generalization. Family IDs are bookkeeping, not proof of semantic separation.
- V15/V16 outputs named package-context-development were actually evaluations of the ordinary 176-case development split. They did not run the separate context perturbation suite. Earlier wording implying a dedicated context guard was inaccurate.
- V15/V16 clean-CUDA checks used the existing .venv in a fresh interpreter with empty Hugging Face cache and explicit base files. That demonstrates offline loading in that environment, not installation into a newly provisioned environment.
- Each trainer state serializes the full model state, including the frozen base. This explains much of checkpoint size. Adapter-only model state plus optimizer/RNG state and a verified base hash would reduce storage, but needs resume parity tests before adoption.
- Gradient accumulation averages microbatch mean losses. With variable completion lengths this is not the same as one token-weighted effective-batch loss. It is a valid objective if intentional, but should be documented or changed with a focused gradient-equivalence test.

## What is correct and verified

- Completion-only labels, masked padding, attention masks, EOS supervision, and rejection of oversized examples are implemented.
- Training and inference share the prompt formatter. The base revision, adapter identity, source snapshots, and training contracts are recorded.
- Finite-loss and gradient checks, gradient clipping, optimizer state, and RNG checkpointing exist.
- Checkpoint selection follows the recorded development exactness, validation-loss, then earliest-step rule. The selection code is mechanically consistent; the weakness is the data it selects against.
- On this audit, tests/test_sft.py passed all 7 tests. These cover masking, oversized inputs, learning, reload, contract mismatch, periodic resume, and exact LoRA resume with dropout on a tiny model. They do not establish full CUDA reproducibility or release quality.
- V16 completed 300 steps. All three checkpoints scored 176/176 on development. Selected step 200 adapter: 81bb37a7d2b1dfbe7de39dca9e8b1e7ca46a6b7283a863475eed0b536555821a.
- V16 V8 challenge scored 65/66 and failed unsupported/invalid handling. The sealed evaluation receipt still said running when inspected in this audit; no final sealed score is claimed here.

## Required next steps

1. Stop adding correction runs until data semantics and exposure are fixed.
2. Add checks for target information being present in public inputs, concrete URLs, selected-resource consistency, and every invalid-boundary category. Review sampled rendered prompts and labels in both languages.
3. Replace grouped prefixes with deterministic mixed batches covering corrections and routine replay at every checkpoint. Report actual presented rows and task/language counts, not only corpus size.
4. Create new development boundary cases independently of final evaluation. Keep all V8 scores as diagnostic history.
5. Freeze a candidate, then evaluate a genuinely unused holdout with natural phrasing, unseen task families, and observable labels. Preserve raw predictions, tool outcomes, and per-slice failures.
6. Run the actual context perturbation suite, install the package in a fresh environment, verify checksums and licensing, and document supported scope before any release claim.

The V16 weights were trained candidates and remain diagnostic history. The V21
package now has separate release evidence: corrected data, mixed exposure,
unused holdout and context scores, fresh-environment loading, and complete
package documentation. Those receipts support release only within the narrow
authored Wrench-Pro scope.
