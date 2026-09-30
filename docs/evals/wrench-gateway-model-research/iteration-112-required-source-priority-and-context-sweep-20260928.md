# Iteration 112: required-source priority and stable context sweep

Date: 2026-09-28 (America/Edmonton)  
Assignments: `WRENCH-E0-REQUIRED-SOURCE-PRIORITY-ITER112-20260928`, `WRENCH-E0-CONTEXT-REPRO-SWEEP-ITER112-RETRY-20260928`  
Status: **required-source priority regression passed; stable synthetic prompt-input maximum is 90.621598%; product gates remain unproven**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Finding and implementation change

`required_source_paths` were included in the final prompt compiler's required
evidence check, but were not put into the context ledger's mandatory selection
queue. The ledger could spend the small active context budget on higher-ranked
optional retrieval results first. If required evidence did not fit afterward,
the prompt gate correctly rejected the entire preparation. This caused
non-monotonic accept/reject regions in Iteration 111.

The E0 pipeline now places available required evidence IDs and required source
path IDs into the mandatory queue before preservation hints and optional
retrieval candidates. The final prompt gate remains authoritative and still
fails closed if a required item is missing or cannot fit. The code fix is in
`src/wrench_harness/e0_context_pipeline.py`; a focused regression was added to
`tests/test_e0_context_pipeline.py`.

The passing deterministic check used two source units, a context budget of 3
ledger word-estimate tokens, and a query matching the optional distractor. The
required configuration line remained in the serialized prompt while the
optional line was omitted. Snapshot SHA-256:
`5baea0c589a2a98b6fd98d702428b766dbd0403b5d12f36551242710002cfb74`.
Prompt SHA-256:
`65cceb82e521c3bff617a0fa89f3b9adc663cc2e10d0a08a1081ca75d11a8830`.
The machine receipt is
`C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\iter112-required-source-regression-v2.json`,
515 bytes, SHA-256
`a9b07d188b947a77a591b6e34eb8cb120edcb69deb662d8fa4a913151be4548c`.

One earlier assertion attempt used budget 35. It returned `READY` and retained
the required line, but the test assumed both ledger units would exceed the
budget; the ledger uses a word estimate, so both fit. That assertion failed
and was not counted as a pass. Its receipt is
`C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\iter112-required-source-regression.json`,
517 bytes, SHA-256
`41397389940fb9938608b27a78b20f0d0d3df581a008485648d10cfc7cf93f94`.
The later budget-3 fixture reproduced the intended competition and passed.
The installed base Python and the approved
synthetic runtime environment both lack `pytest`; no dependency was installed.
The regression was executed directly through `prepare_e0_context`, so the
committed pytest test still needs a normal CI run.

## Stable budget sweep after the change

The same fixed three-case synthetic repository and pinned MiniMax M3 chat
template were evaluated at every integer context budget from 128 through
1024. All 897 settings prepared successfully, and all seven required quotes
remained visible. The maximum pooled final-prompt input reduction was
**90.621598%** at budgets 134 and 135: 19,289 baseline tokens to 1,809 prepared
tokens. Budget 134 is the smallest setting on the maximum plateau. Each of
three confirmation runs exactly matched baseline/prepared counts, snapshot
hashes, and all three prepared-prompt hashes.

| Measure | Result |
|---|---:|
| Settings evaluated | 897 |
| Successful preparations | 897 |
| Failed preparations | 0 |
| Final serialized input reduction range | 86.401576%-90.621598% |
| Maximum reduction | 90.621598% |
| Maximum plateau | context budgets 134-135 |
| Baseline and prepared prompt tokens | 19,289 and 1,809 |
| Required quotations visible | 7/7 at every setting |
| Best-setting confirmations | 3/3 exact identity and count matches |

Per-case best-setting counts were: retry policy 6,433 to 613; session lifetime
6,428 to 608; retry function 6,428 to 588. The stable snapshot SHA-256 is
`f98c7c8fbf2f3613ccf7dee75ad15729d3cc112cb7a2c62c3481358a201b672b`.
Fixture SHA-256:
`92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.
Tokenizer: `MiniMaxAI/MiniMax-M3@f0e1c1e04d40177e4673a22097036854f536e9c0`.
Tokenizer inventory SHA-256:
`86d0d4866b4278ce7957644e81e43ce90da356fdd434abfa8c928b4f1adfcc9c`.
Chat-template SHA-256:
`11421244f67553498e5c8112dae02802025bcc4305ec45ad380af95c96f9fe64`.
The tested E0 source file SHA-256 is
`4ea3e320eaba9dfa0fcbc3686e4ededc432ac7b06631a9132a06219f9c463c04`.

The full machine receipt is
`C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\context-budget-sweep-iter112-retry.json`,
816,935 bytes, SHA-256
`d5d8d6c0751a5ce89884f28c62168b157d4e4ddef01be3c64b12886ca107d776`.
The receipt binds all budget rows, failures, prompt identities, exact source
hashes, and repeats. Recalculation from the receipt found 897 complete rows,
zero failures, one snapshot hash, and byte-identical best-setting confirmations.
The last atomic progress checkpoint is
`C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\context-budget-sweep-iter112-retry.progress.json`,
812,888 bytes, SHA-256
`11092f877d459b9a8c0ef3ca80050d00c8300cc946560813d3b00a23d5f33132`.
It contains all 897 sweep rows; the final receipt additionally binds the three
confirmation repeats.

## Limits and rejected runs

These counts use the pinned target chat template for final prompt tokenization.
The E0 selection budget itself uses the runtime's default `word_estimate_v1`
counter, not the model's tokenizer. Treat 90.62% as a deterministic synthetic
context-preparation proxy only. The fixtures contain 240 repetitive authored
health-log lines. No model inference, LoRA, provider call, verified code
completion, paid-token receipt, dollar cost, or real-repository episode was
measured. It is not the 95% frontier-token claim and does not demonstrate
95/5 completion, retained task success, or all-day engineering.

The first Iteration 112 full sweep completed its 897 settings but its wrapper
failed while building the final receipt because it looked up Python's built-in
`__import__` on the demo module. That run produced no final receipt and is
rejected. The corrected retry added an atomic progress checkpoint every 64
settings and produced the receipt cited above. No held-out data was accessed.

## Resource and storage

The retry performed no model inference and used no GPU compute. The lowest
sampled free system RAM during the retry was 16.40%; GPU free memory remained
above 15,200 MiB of 16,311 MiB. The process exited normally. Storage admission
and final checks included the repository, approved Wrench data root, Docker
Desktop WSL model volume, and hourly automation directory; the checker
reported `WITHIN_LIMIT`. The retry used a 100,000,000-byte reservation. The
separate code/regression job used 25,000,000 bytes. C: had more than 140 GB
free. Release reservations only after outputs and retained source/store bytes
are included in the final inventory.

## Next gate

Run the committed focused test under a pinned environment that includes
pytest, then repeat the demo and a representative held-out development
battery with correctness oracles. Next compare deterministic-only against
the admitted Wrench LoRA on identical frozen episodes. Keep the 95/5/95,
95%-cheaper, confidence-bound, and eight-hour engineering requirements
unchanged. Fit-03 still requires at least 25% free RAM at launch; the current
host sample does not meet that threshold. SubRoute `:4000` remains closed to
completion calls until the numeric campaign cap is enforced.
