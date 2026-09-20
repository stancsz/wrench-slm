# Phase 193: 2M and 4M staged handoff latency after bounded verification

Date: 2026-09-20

## Change

The package-local native handoff previously passed the complete monster prompt
to semantic verification and TTC. Those paths repeatedly case-folded the raw
4M string even though old material is reference-only. The verifier now sees
the same bounded current-intent suffix as the mechanical router, while the raw
payload remains preserved and hash-bound in the prefill receipt.

The historical lookup route also refuses a generic request without an explicit
path or symbol anchor and uses exact C-level string lookup before any bounded
case-insensitive fallback. This prevents an ambiguous request from starting a
multi-million-token regex scan.

## Repeated source-runtime probe

Command:

```text
python tools/probe_native_handoff_prefill.py --payload-tokens 2000000 ...
python tools/probe_native_handoff_prefill.py --payload-tokens 4000000 ...
```

The native backend in this probe is a local protocol stub. It proves intake,
staging, verification, and accounting, not MiniMax or dense-native model
quality.

| raw input | runs | raw token estimate | staged tokens | end-to-end p50 | p95 | staging p50 |
|---:|---:|---:|---:|---:|---:|---:|
| 2,000,000 | 3 | 1,999,942 | 1,955 | 152.768 ms | 162.178 ms | 74.27 ms |
| 4,000,000 | 3 | 3,999,942 | 1,955 | 261.682 ms | 299.537 ms | 149.61 ms |

All six runs returned `PASS_NATIVE_HANDOFF_STAGED_4M`, made one verified
upstream call, and kept the staged prompt below 64K. The earlier 4M run was
about 7.4 seconds before the verifier-boundary fix, so that number is retained
only as the failure diagnosis, not as current performance.

## Interpretation

This is a material improvement for the actual raw-input path. The current 4M
staged p50 is still above the earlier aspirational 100 ms target, so this phase
does not close the absolute latency gate. The product claim remains practical
fast hybrid serving, not a claim of dense native attention over all 4M tokens.

## Regression evidence

- `pytest -q`: `163 passed, 14 warnings`;
- the monster-handoff test asserts verifier prompt length is at most 16,000
  characters and smaller than the raw historical payload;
- no mutation authority was added.
