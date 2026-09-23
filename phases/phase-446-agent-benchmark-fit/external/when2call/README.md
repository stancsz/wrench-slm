# NVIDIA When2Call input

This folder contains the public MCQ test input from the NVIDIA When2Call
repository at immutable commit
`ecc8d42388e91ab37e7e737d48e16e8ecea3d1dc`.

## Pinned input

- File: `data/when2call_test_mcq.jsonl`
- Bytes: `20424385`
- Records: `3652`
- SHA-256: `8c3694e583eeeb8dbc297e6cd90da70efc68efa4b6adb7227523e828c6b7b14c`
- Repository license: Apache-2.0, copied to `LICENSE.txt`
- Dataset source: BFCL v2 Live Simple and Multiple

The test rows are public and were not used to train or tune the Wrench head.
Rows are not interchangeable with the authored Wrench development set. The
benchmark's correct labels are three of the four response choices:
`tool_call`, `request_for_info`, and `cannot_answer`. `direct` is an available
choice but not a gold label in this file.

## Wrench projection

The Wrench System One gate is binary. Preserve all official labels in the raw
receipt, then report two distinct views:

- The abstract call-decision projection maps `tool_call` to `not_abstain`,
  and `request_for_info` or `cannot_answer` to `abstain`. `direct` is a
  distractor label in this file, not a gold label. This is a gate-component
  score, not an end-to-end action result.
- The Wrench policy view counts a call as eligible only when a separately
  audited mapping proves that it is one of the six authorized Wrench actions.
  No arbitrary external API is eligible by default. Report `not_abstain` on
  unsupported API requests as an unsupported-call false continuation.
- Wrench abstention escalates to the stronger model; it does not answer the
  user directly. Keep that distinct from When2Call's `direct` option.
- Report over-limit inputs separately. The head contract caps inputs at
  8,192 characters and 512 tokens; do not shorten benchmark tool menus to
  force a pass.

Because the data was built from BFCL v2 Live, keep a case-level overlap audit
with BFCL V4. Treat this as a cross-benchmark decision diagnostic, not as a
second independent tool-call accuracy dataset.

The input file is ignored by Git to avoid committing benchmark data. Run
`fetch.ps1` to download the exact pinned file and verify its SHA-256.

## Frozen Wrench gate run

`runs/wrench-qwen-head-v2/` is the completed run of the frozen Qwen binary
abstention gate. It scored all 3,652 rows with 3,652 unique IDs against the
unchanged data SHA-256 above and the saved head SHA-256
`e33e28af544be5eaf156ff42dbe47d2098a36939bb4b0cfd0222d378d4ee3b0b`.
Per-case decisions are in `predictions.jsonl`; the original execution receipt
is `summary.json`; derived subset calculations are in
`component-analysis.json`.

| Wrench gate metric | Result |
| --- | ---: |
| Binary projection macro-F1, all rows | 44.3% |
| False continuation on 258 no-tools cases | 20.9% (54/258) |
| Over-limit cases safely abstained | 2,381/3,652 (65.2%) |
| Gold tool-call targets mapping to Wrench's six actions | 0/1,295 |
| Model-inference latency p50/p95 (over-limit rows excluded) | 191.5/255.4 ms |

The no-tools false-continuation metric is the direct reference point here:
NVIDIA reports 20% tool hallucination for Qwen 2.5 0.5B on no-tools cases.
Wrench's 20.9% is close, but not a measured win. The published overall
When2Call Macro-F1 is a three-way metric; do not compare it with Wrench's
binary projection. The tool menus also fall outside Wrench's action allowlist,
and 65.2% exceed the Wrench head input cap. Treat this as a bounded abstention
stress test, not end-to-end developer-tool success.

An earlier `runs/wrench-qwen-head-v1/run.json` records a pre-load failure from
the missing optional `psutil` dependency. It has zero rows, tokens, provider
calls, and resource samples. The retry used the Windows-native RAM check and
completed. Keep both receipts as the execution history.
