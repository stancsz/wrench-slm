# Phase 73: LoRA/router quality probe

Status: `NEGATIVE_PROBE_NOT_SELECTED`

A 100-step development calibration was run against the existing BF16 v7
Safety checkpoint using the v8 balanced development data. The probe used
rank-8 LM-head LoRA plus trainable router rows and completed on CUDA.

The real 220-case diagnostic produced 86/220 correct outcomes, 29/120 exact
eligible accepts, and 24 prohibited accepts. The historical v7 diagnostic was
90/220, 30/120, and 15 prohibited accepts. This adapter is rejected and is not
part of the portable candidate.
