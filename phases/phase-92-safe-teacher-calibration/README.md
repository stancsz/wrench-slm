# Phase 92: safe teacher calibration probe

Status: rejected development experiment. No checkpoint from this phase is
promoted or published.

## What was tested

The raw teacher-calibration capture contained 224 rows. The builder
`tools/build_safe_teacher_calibration.py` retained only development training
rows whose frozen oracle was an accepted allowlisted action. It excluded all
boundary and invalid rows from training and used the frozen verifier target,
not an unsafe or incomplete teacher proposal.

The resulting training set contains 176 rows. The source capture had 125 exact
teacher-oracle rows, 44 boundary rows, and 4 rows without a usable status.
Receipt: `receipt.json`.

The retained set was used for a 300-step rank-8 LoRA probe on the RTX 5070 Ti.
The training loss fell from `0.0031500002` to `0.0001155123`, but this is only
optimization evidence and is not a quality claim.

## Held-out final split comparison

Both arms used the same 44-case unseen split, adaptive few-shot prompting, and
the mechanical fast path disabled so that the model behavior was measured
directly. The v7 baseline was served separately from the safe-oracle LoRA.

| Arm | Accepted | Correct outcomes | Correct eligible accepts | Prohibited accepts | Transport failures | Elapsed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| v7 safety baseline | 13/44 | 16/44 | 5/24 | 4 | 8 | 256.579 s |
| safe-oracle LoRA v1 | 7/44 | 16/44 | 6/24 | 0 | 7 | 254.970 s |

The LoRA probe therefore did not improve correct outcomes, had only 25.0%
correct eligible accepts, and remained far below a production quality gate.
The baseline also failed the safety gate with four prohibited accepts. Neither
arm is a release candidate. The LoRA checkpoint remains local and is not part
of the public Hugging Face package.

## Evidence

- Safe training receipt: `receipt.json`
- Safe training rows: `train-safe-oracle.jsonl`
- LoRA final split: `final-eval-safe-lora-v1.json`
- Baseline final split: `final-eval-v7-safety-baseline.json`

The public NVFP4 package is unchanged. It remains the canonical experimental
portable artifact. This phase does not establish MiniMax parity, native 4M
retrieval quality, vLLM or Ollama compatibility, GGUF compatibility, or
production readiness.
