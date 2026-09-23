# Verifier-aligned abstain preflight, posthoc regression

This candidate tightens the optional abstain-only preflight against Wrench's
actual health endpoint and limit rules. It also detects explicit follow-up
actions, Git mutations, live secret requests, unresolved references, and
numeric limits in English and Chinese. It never approves a request. The Qwen
layer-8 head still decides every request that passes the preflight.

The [posthoc receipt](posthoc-5k.json) replays the previously recorded layer-8
predictions against the **already consumed** 5,600-case generated suite:

| Outcome | Count |
| --- | ---: |
| False Wrench decisions on 5,000 abstain cases | 0 |
| False abstentions on 600 eligible controls | 125 |
| Balanced accuracy | 89.58% |
| Preflight abstain vetoes, no Qwen forward in the intended runtime path | 3,825 |

The zero false Wrench count was obtained after reviewing failures on this
same suite. It is not a blind result. The other 1,175 abstain cases were left
to the model, which abstained on them in the recorded predictions. All 600
eligible cases passed the preflight; the model accepted 475. The optional
hybrid was then timed end to end on the same generated suite.

The [measured receipt](measured-receipt.json) and
[class-specific summary](measured-summary.json) pin a later full replay on
RTX 5070 Ti with BF16 Qwen. It had zero runtime errors and kept at least
49.4% host RAM and 40.3% VRAM free across 192 resource checks. The measured
decision times include tokenization and Qwen inference when needed:

| Timed group | Requests | Median | p95 |
| --- | ---: | ---: | ---: |
| Correctly continued eligible requests | 475 | 172.93 ms | 217.31 ms |
| All eligible requests | 600 | 171.63 ms | 213.77 ms |
| Requests with a Qwen forward | 1,775 | 177.86 ms | 213.90 ms |
| Explicit preflight abstentions | 3,825 | 0.0275 ms | 0.0587 ms |
| All requests | 5,600 | 0.0379 ms | 197.34 ms |

The all-request median is dominated by fast refusals and is not the speed
of a successfully continued Wrench task. The eligible-task timing is the
relevant comparison for useful routing. These are local decision times, not
hosted Jev end-to-end measurements or full Wrench workflow latency.

A diagnostic threshold sweep on the same consumed suite showed the safety
tradeoff. Lowering the Qwen acceptance threshold from 0.50 to 0.45 would
reduce false abstentions from 125 to 111, but introduce 3 unsafe
continuations. At 0.35 it would leave 74 false abstentions and introduce
30 unsafe continuations. These are hypothetical posthoc decisions from
recorded probabilities, not a new fit or candidate result. The threshold
remains 0.50.

On the previously consumed independent 60-case set, the preflight vetoed 4 of
30 abstain cases and 0 of 30 eligible cases. This checks one false-abstain
regression from Chinese punctuation after an allowlisted health URL. It is
not a new blind estimate. The focused classifier and intake contract run
passed 121 tests after the change.

Provenance:

- Worktree base commit: `875970b1d0acbff44fe9652eb63f3241d6d122df`.
- Preflight source SHA256: `93ccadebebf4a516538fc5024bbca6eebed64496aefb0d023f9a43dac77a4b28`.
- Frozen suite SHA256: `26fafa2e008ed3b6ee1fefd11293802f47dcdd35b44a295cece1c2a301433ec1`.
- Layer-8 prediction SHA256: `a367a1be37d3f2535962b9c7c14325b8118c29fb53009c18cc79c4ab81553f5e`.
- Posthoc receipt SHA256: `e815ff9a5ad06b297f1c4f31a172fde3efe12ff2e85aeee6357f0588d3010238`.
- Measured receipt SHA256: `f0495b5081329979940d8b017792d7c2a99c5a77567d89e4fc6c6d39a13ee976`.
- Measured predictions SHA256: `df261f65c1ebccdadbc02961e38da7065c456c7e736fa9678659867a480133d7`.

No model training or threshold tuning was performed in this change. The
remaining 125 false abstentions, lack of real-workflow accuracy data, and
unmatched Jev timing keep learned routing disabled. The next classifier
fit needs approved, redacted, labeled real Wrench request text through the
[local intake](../REAL_REQUEST_INTAKE.md), followed by a fresh holdout and
matched hardware timing.
