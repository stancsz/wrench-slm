# Phase 264: current-source 4M prefill receipt

This phase records a fresh local run of the current source tree's deterministic
first-layer reducer. It accepts a 4,000,000 token-equivalent raw payload,
indexes reference-only material, preserves the active intent, and emits a
bounded working context.

This is package-local map-reduce evidence. It does not claim dense native 4M
attention, learned retrieval quality, MiniMax parity, or production release.

Command:

```powershell
python tools/probe_embedded_worker_prefill.py --payload-tokens 4000000 --output <receipt>
```

The fresh receipt is in `receipt.json`. The run used source commit `1c76b56`
on the interactive RTX 5070 Ti development host. The reducer made zero model
calls and produced a 1,966-token staged working context from 3,999,547
estimated raw tokens. The measured first-layer gate latency was 81.818 ms and
the complete probe elapsed time was 163.656 ms.
