# Owner-approved binary System 1 training

The owner approved using the original 5,000-abstain suite for training by
answering "the 5000 ones". That suite contains 5,000 authored abstain cases
and 600 authored eligible Wrench controls. It is now training material, and
its earlier test score is historical only. These are repository-grounded
synthetic requests, not captured real workflow requests.

The frozen Qwen backbone was encoded at layer 8. A char TF-IDF plus layer-8
logistic readout was fitted on 6,528 rows: the approved 5,600 and 928 corrected
legacy training rows. The old suite was split by pattern group for candidate
selection. The chosen internal slice had 0/1,000 unsafe continuations and
10/120 false abstentions. That slice is part of training, not an independent
test. The packaged [head](qwen-abstain-head.json) is 358,728 bytes. Its base
weights are unchanged. See the [encoding receipt](encoding-receipt.json) and
[fit receipt](fit-receipt.json) for hashes and selection details. The sealed
`evals/wrench-expanded-v2/final.jsonl` split was not read.

The [replacement 5,600-case suite](../system-one-replacement-5k-20260923/README.md)
was frozen before fitting and scored once with the head and the then-current
preflight. The [first-pass receipt](replacement-evaluation-receipt.json) and
[predictions](replacement-predictions.jsonl) record **80/5,000 unsafe
continuations**, **30/600 false abstentions**, 98.04% overall accuracy, and
96.70% balanced accuracy. Abstain recall was 98.40% and eligible coverage was
95.00%. There were no runtime errors. The predeclared diagnostic target
failed because unsafe continuations remained.

On an RTX 5070 Ti with BF16 weights, complete warm decision latency was
170.33 ms median and 223.15 ms p95 over all 5,600 cases. For the 3,150
decisions that actually used Qwen, median/p95 was 187.70/237.06 ms. The
2,450 preflight abstentions took 0.027/0.063 ms median/p95. Fast refusals
are not fast successful Wrench work. The Qwen backbone allocated about 7.77
GB of VRAM, separate from the 359 KB head. During the measured run, minimum
free host RAM was 26.45 GB and minimum free VRAM was 6.15 GB, above the
required 10% reserves.

Review of the 80 failures found explicit compound followups and invalid
bounds. The abstain-only preflight now catches those forms. The
[posthoc regression](replacement-posthoc-regression.json) recomputes the
stored predictions with the revised preflight: 0/5,000 unsafe continuations,
30/600 false abstentions, 99.46% overall and 97.50% balanced accuracy.
It does not measure latency after the change, and it is **not** a fresh
holdout. The 43 focused preflight contracts pass. The revised rules cannot
approve a request or grant tool authority.

Production routing remains disabled. The replacement suite was authored and
its structural audit still awaits human label review. Real redacted Wrench
requests with reviewed binary labels and a new untouched holdout are needed
to estimate field accuracy. Jev/OpenJev use different tasks and hardware, so
their published speed and accuracy figures do not establish parity here.
The project's paired workflow, verifier, and operational gates remain open.
