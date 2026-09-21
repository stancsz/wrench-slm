# Phase 300: 2M and 4M model-local context under concurrent work

## Result

The current materialized portable package passed a local model-local raw intake
shadow while ordinary requests were sent concurrently:

- requested raw points: 2,000,000 and 4,000,000 tokens
- actual estimated raw points: 1,996,181 and 3,996,531 tokens
- both requests returned HTTP 200 through the package-local OpenAI endpoint
- both were hash-bound and compacted to a 19-token effective working context
- working-context budget remained 64,000 tokens
- both used the embedded mechanical route with zero model calls
- ordinary probes recovered during monster request processing: 3/3 accepted
- ordinary-probe p95 was 82.59 ms, maximum 115.429 ms
- RAM availability stayed above 47 percent before and after the run
- no CUDA device was visible, so VRAM reserve was not applicable

Receipt: `monster-context-shadow-receipt.json`

## Important boundary

This proves a model-local 4M-configured raw intake and deterministic reduction
path in the portable package. It does not prove dense native 4M attention,
retrieval quality, learned MiniMax parity, or production readiness. The 4M
request uses a 4,096-token admission margin so the generated payload remains
inside the server's hard 4,000,000-token limit.

## Reproduction

```powershell
python tools/run_monster_context_shadow.py `
  --package-dir D:\models\_wrench-current-client-20260921 `
  --output phases\phase-300-monster-context-shadow\monster-context-shadow-receipt.json
```
