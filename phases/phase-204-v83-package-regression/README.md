# Phase 204: v83 fast first-layer package regression

Date: 2026-09-20

## Change

The source runtime now uses bounded head/tail sampling for token estimates on
monster payloads and skips a redundant full code-fence scan for unbounded old
references. Exact SHA-256 payload binding, query-specific lookup windows,
small-fragment AST extraction, and proposal-only verification remain intact.

The portable package was materialized at:

`D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v83-fast-first-layer`

## 4M model-local handoff

The package's own Ollama-shaped `/api/chat` endpoint accepted a 4M raw logical
payload and staged it before the local native protocol stub. Three fresh runs:

| run | server staging | complete stub round trip | staged tokens |
| --- | ---: | ---: | ---: |
| 1 | 97.351 ms | 214.542 ms | 1,955 |
| 2 | 81.003 ms | 186.708 ms | 1,955 |
| 3 | 99.029 ms | 214.256 ms | 1,955 |

The worker-only probe reported 3,999,547 raw estimated tokens, 1,966 staged
tokens, and two evidence windows. The complete round trip includes transfer
and JSON processing of the roughly 35 MB request body. The upstream was a
local protocol stub, so this is intake and staging evidence, not model quality
or dense native attention evidence.

## 220-case package replay

The package-local HTTP endpoint was exercised with client mechanical fast-path
bypass and an isolated health fixture:

- weighted mechanical frontier-token coverage: 94.5411%;
- net frontier-token savings: 95.5310%;
- Wrench-plus-identical-teacher-fallback weighted final success: 99.6503%;
- teacher-only weighted final success: 78.9959%;
- Wrench-plus-fallback median / p95: 184.658 ms / 350.017 ms;
- Wrench-plus-fallback local tokens: 23,643;
- fallbacks: 5;
- prohibited accepts: 0;
- unexpected mutations: 0.

This remains diagnostic evidence. It does not establish dense-native 4M
attention quality, learned MiniMax parity, family-disjoint final approval,
independent 5060Ti verification, or production enablement.

Receipts:

- `replay-220/evaluation.json`
- `replay-220/trace-manifest.json`
- `phases/phase-204-v83-package-validation.json`
- `phases/phase-204-v83-prefill-package.json`
- `phases/phase-204-v83-handoff-1.json`
- `phases/phase-204-v83-handoff-2.json`
- `phases/phase-204-v83-handoff-3.json`
