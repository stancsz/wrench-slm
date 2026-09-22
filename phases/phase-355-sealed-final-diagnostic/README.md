# Phase 355: sealed-final diagnostic replay

Status: preregistered diagnostic, pending human approval

This run is an evaluation-only replay of the sealed `final.jsonl` split. It
must not be used for training, LoRA fitting, prompt tuning, router selection,
or verifier changes. The suite manifest remains
`DRAFT_PENDING_HUMAN_APPROVAL`, so this run cannot authorize release.

Frozen protocol:

- Cases: `evals/wrench-expanded-v2/final.jsonl`
- Expected canonical case hash:
  `3e24ba47b78a99b1ef81bb8ea269e4377ca45097186812ce71aa99bb2c2f222b`
- Wrench package: `D:\models\_wrench-release-candidate-8d9ea2c`
- Runtime source commit: `8d9ea2c`
- Teacher: local MiniMax-compatible endpoint, model `minimax`, temperature 0,
  streaming, `max_tokens=768`, proposal capture only
- Wrench replay: package-local HTTP endpoint, client mechanical shortcut
  disabled, isolated health fixture, identical verifier and fallback policy
- No source or evaluation input changes are permitted after this receipt

The receipt will report all four arms, per-case raw hashes, final success,
verifier success, fallback, frontier and local tokens, latency, prohibited
accepts, unexpected mutations, and paired uncertainty. Any input hash
mismatch, prohibited accept, unexpected mutation, verifier bypass, or
transport failure invalidates the paired result and is a stop condition.

Raw teacher and replay traces remain outside Git under
`D:\models\wrench-phase-355-sealed-final-diagnostic`.

## Result

The first concurrent teacher capture had seven HTTP errors and was rejected by
the preregistered stop condition. A bounded single-worker retry then completed
`44/44` traces with zero transport failures. The paired replay completed all
`44/44` rows, including `24` eligible rows:

| Arm | Weighted final success | Weighted verifier success | Frontier tokens | Local tokens | Fallbacks | Median / p95 ms | Prohibited accepts | Mutations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MiniMax teacher only | 0.972588 | 1.0 | 7,447 weighted | 0 | 0 | 5,238.106 / 10,386.799 | 1 | 0 |
| Rules + identical fallback | 0.972588 | 1.0 | 7,729 total | 0 | 20 | 0.565 / 33.581 | 1 | 0 |
| Wrench + identical fallback | 1.0 | 1.0 | 0 | 4,805 | 0 | 172.941 / 266.582 | 0 | 0 |
| Wrench only diagnostic | 1.0 | 1.0 | 0 | 4,805 | 0 | 172.941 / 266.582 | 0 | 0 |

The paired Wrench workflow gates all passed: weighted frontier-token coverage
`1.0`, net frontier-token savings `1.0`, teacher final-success
non-inferiority `true`, zero Wrench prohibited accepts, and zero mutations.
The paired final-success difference was `0.027412` with a 95% bootstrap
interval of `[0.0, 0.068182]`. The one teacher prohibited accept remains
visible in the receipt and is not counted as a Wrench violation.

The direct package retrieval probe also passed all six 2M/4M placement cases
with zero model calls. This remains deterministic hybrid retrieval evidence,
not dense-native attention or learned MiniMax parity.

External receipt hashes:

- teacher retry: `519BF32CF84E6EEA79C999232345C915617D714701636BEAD25A321DBFF7C9B1`
- replay evaluation: `3B293FA7C8D9C5EAD47A82A029A42872C1518916EC07EA09B0708BFD12149DDB`
- replay trace manifest: `A61AD755A888F884D4042A927F08E033E21687044CD1188143B9C2438EFEF0C8`
- 2M/4M retrieval: `CF9E8E71A6BD68C7EB8E1DF0F499B0033927767FAFA72EFE64FA3FA42885FBCE`

This is the strongest current paired workflow result, but it is not release
approval. Human approval, current-head independent 5060TI attestation, and
the learned route remain open.
