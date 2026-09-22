# Phase 353: guided JSON LoRA development diagnostic

Date: 2026-09-21

This is a development-only evaluation of the current attention LoRA adapter
with `lm-format-enforcer` guided JSON decoding. It used the 44-case
development split, not the sealed final split, against the calibrated BF16
base model. The guided decoder improved syntactic containment, but it did not
make the learned fallback production-ready:

| Metric | Result |
| --- | ---: |
| Cases | 44 |
| Outcome matches | 23/44 |
| Exact target matches | 4/44 |
| Verified accepts | 7/44 |
| Median latency | 3,662.212 ms |
| p95 latency | 30,459.054 ms |
| Device | `cuda:0` |

The receipt shows repeated semantic errors such as hallucinated or repeated
paths, wrong action families, invalid health URLs, and malformed or unusable
patch diffs. JSON schema compliance does not establish proposal correctness.
The learned route therefore remains diagnostic only and is not promoted into
the production router. The deterministic mechanical route and its verifier
remain the accepted path for the validated workload.

Evidence: `evaluation.json` in this directory. The complete raw receipt is
kept hashable and includes every case output and latency.
