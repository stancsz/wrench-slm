# Read-lines operation screen 03 evaluation

Status: completed; independent receipt review PASS.
Date: 2026-09-25 (America/Edmonton)
Evaluated revision: `10bb51539ed860cd55bdf311aa67e223b9c10a41`
Worker report: [local read-lines acceptability screen](../../reports/wrench-local-acceptability/local-read-lines-acceptability-03.md)

## Claims checked

The content-free receipt identifies protocol-03 job `LOCAL-READLINES-ACCEPT-20260925-03`, nonce `RL03-E1F6`, the pinned runner and the embedded fixture. It contains six cases. Route status, action and required abstention reason match the frozen oracle on 6/6. Exactly two completed cases call the core executor, and both executor observations match. Four missing/stale/out-of-range/ambiguous cases abstain correctly without executor dispatch. Every case's pre/post fixture-tree digest, file count and byte count match.

The measured result is limited to exact line-range retrieval and the four
listed abstention mechanics on an exposed Wrench-authored synthetic fixture.
It does not establish local SLM task acceptance, semantic coding completion,
generalization, real-work utility or frontier-token savings. The receipt
records null frontier savings and zero frontier-usage pairs.

## Receipt identity and limits

- Receipt SHA-256 claimed: `051eec3d5643d8b1fc98d1305cfa3f29525d51476b2297b115b5bd8cc718d94d`.
- Receipt path: `C:\wrench-slm-data\artifacts\wrench-local-acceptability\read-lines-acceptability-20260925-03.json`.
- The runner produced the receipt locally; it is not a signed attestation. The independent reviewer checked its structure and identities without rerunning the measurement.
- No client, provider, tokenizer, model, training, network or real repository task was used.

`readlines_runner_review` recomputed the receipt digest, repository head,
runner digest, embedded fixture digest, all six route outcomes, the two
executor observations and each case-tree identity. Counts matched: 6 exact
routes, 2 exact executor results, 4 correct abstentions and zero unresolved
cases, mutations, runtime errors or unsafe dispatches. The review did not
rerun the measurement. No findings remain.
