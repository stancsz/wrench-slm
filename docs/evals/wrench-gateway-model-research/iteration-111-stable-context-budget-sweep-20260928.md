# Iteration 111: stable-root context-budget sweep

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-E0-CONTEXT-REPRO-SWEEP-ITER111-20260928`  
Status: **reproducible synthetic prompt-input maximum found; product acceptance not demonstrated**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Result

The stable-root scan evaluated every integer context budget from 128 through
1024, or 897 settings. The maximum successful pooled prompt-input reduction
was **89.227021%**, at budgets 154 through 170: baseline 19,289 tokens and
prepared prompt 2,078 tokens over three synthetic code/tool cases. At budget
154, all seven required quotations remained visible. Three independent
repeats produced the same aggregate counts, snapshot identity, and all three
prepared-prompt hashes.

This improves the previous E0 maximum of 86.4327% on the same three-case
synthetic demo by 2.7943 percentage points. Budget 154 is the smallest setting
on the maximum-reduction plateau. This is a deterministic context compiler
measurement, not a LoRA result, a generated-code task success, an OpenCode
provider receipt, or a frontier-token saving. The three fixtures contain
repetitive authored health logs, so this is a bounded mechanics result only.
The 95% frontier-token, 95% task-success retention, all-in-cost, local
completion, and all-day engineering claims remain unproven.

## Sweep completeness and failures

| Measure | Result |
|---|---:|
| Tested budgets | 897 (128-1024 inclusive) |
| Successful context preparations | 824 |
| Rejected context preparations | 73 |
| Rejection ranges | 128-153 and 171-217 |
| Rejection cause | `session-lifetime` omitted required evidence; fail-closed prompt rejection |
| Successful reduction range | 86.468972%-89.227021% |
| Maximum plateau | budgets 154-170, all 89.227021% |
| Required quote check at selected budget | 7/7 visible in each of 3 cases |
| Independent best-budget confirmations | 3/3 exact prompt-hash matches |

The non-monotonic failure regions matter: shrinking the budget is not a smooth
quality/cost dial. Every failed setting remains in the denominator; no fallback
or evidence omission was counted as a successful prepared prompt.

## Identity and reproducibility

The fixed source tree and stable artifact-store roots removed the random
temporary-directory identity that invalidated the exploratory [Iteration 110
repeats](iteration-110-context-budget-random-root-diagnostic-20260928.md).
The stable snapshot hash was
`2f7dd68f4b336e1b30769685d26c857634fed353edd57ce3c292d7c67e8e9256`.
Tokenizer: `MiniMaxAI/MiniMax-M3@f0e1c1e04d40177e4673a22097036854f536e9c0`.
Tokenizer inventory SHA-256:
`86d0d4866b4278ce7957644e81e43ce90da356fdd434abfa8c928b4f1adfcc9c`.
Chat-template SHA-256:
`11421244f67553498e5c8112dae02802025bcc4305ec45ad380af95c96f9fe64`.
Synthetic fixture SHA-256:
`92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.

The machine-readable receipt is
`C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\context-budget-sweep-iter111.json`,
834,362 bytes, SHA-256
`09bc1254cbc8dbb244eaee87c79849fe66fcd7bbfff5272734613811dac3de61`.
It records all 897 rows, the exact input identities, errors, selected case
counts, and the three repeat prompt hashes. Its source-code SHA-256 map binds
the exact pipeline and context files; the receipt is the authoritative full
identity record.

## Resource and storage accounting

No model inference, LoRA fitting, network request, frontier call, or held-out
access occurred. The Python process ended normally. During the observed scan,
the lowest sampled free RAM was 16.90%; final free RAM was 21.69%. GPU memory
was not used; samples remained above 15,180 MiB free of 16,311 MiB. Storage
checks included the repository, approved data root, Docker Desktop WSL model
volume, and hourly automation directory and remained `WITHIN_LIMIT`. The scan
used its 100,000,000-byte reservation; the report/update job used a separate
2,000,000-byte reservation. Destination C: had over 140 GB free. Reservations
are released only after output counts and final status are recorded.

## Decision and next step

The next measurable frontier-token gain must come from evaluating full matched
episodes with task outcomes and exact provider usage, not raising the prompt
proxy. First continue the provider-free engineering path: preserve the stable
receipt, fix the minimum-budget edge behavior without tuning on sealed data,
and prepare a frozen comparison for deterministic context versus an admitted
Wrench-specific LoRA. Do not train Fit-03 while free RAM is below its 25%
launch requirement. Do not call SubRoute until a numeric campaign cap is
present and enforced. Resume the local end-to-end demo and existing engineering
queue separately from this synthetic mechanics measurement.
