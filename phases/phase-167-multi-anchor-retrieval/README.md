# Phase 167: bounded multi-anchor retrieval

The MapReduce query path now extracts path-like, symbol-like, and error-code
anchors from the newest intent. It keeps the first hit for each distinct
anchor, up to eight bounded evidence windows. This recovers multiple relevant
signals without repeatedly scanning a multi-million-token reference for the
same term.

## Verification

- 220-case retrieval diagnostic: target reference recall `1.0`, evidence-window
  recall `1.0`, current-intent preservation `1.0`, hash-bound reference rate
  `1.0`.
- 4M estimated-token retrieval diagnostic: target reference recall `1.0`,
  evidence-window recall `1.0`, current-intent preservation `1.0`, hash-bound
  reference rate `1.0`, raw tokens `3,999,951`, staged tokens `52`.
- 4M cold ingest: `65.469 ms`.
- 4M hot selection: `21.185 ms`.
- full regression: `153 passed, 14 warnings`.
- the new multi-anchor test confirms distinct path and error hits survive into
  the staged evidence windows.

The retrieval receipt is mechanical evidence only. It does not prove model
quality, MiniMax parity, dense native 4M attention, or production enablement.

## Hashes

- `src/wrench_harness/prefill.py`:
  `450703306a8d5f1f5976c48df1a4dc44ed8b311ea358755afcbcb33bfe9b6533`
- `tests/test_prefill.py`:
  `d2fecd6a4be7710ec43ac2477b06160017934306d0bf34b30306f62219b9676e`

The rebuilt v68 package passed structural validation. It was published at Hub
revision `33341a7551b4fd4e3cee9ef3a4b2baa28832e407`. A fresh download matched
the local hashes for `wrench_runtime/prefill.py`, `wrench_runtime/worker.py`,
and `wrench-package.json`, and contained `_QUERY_ANCHOR_RE`.
