# Phase 315: current-head release candidate

This phase rematerializes the portable candidate from a clean detached
worktree at source commit `a8a75c323a7c42e4758f318f05e625565c6b9acf`.

## Candidate identity

- Package: `D:\models\_wrench-release-candidate-a8a75c3`
- Package manifest SHA256:
  `d037dbccbeba4e7258466751952c409beac5104df1b556398f141b0c0b8894de`
- Packed package bytes: `3,423,306,231`
- Parameter count: `3,881,244,016`, below the `4,250,000,000` ceiling
- Declared raw input context: `4,000,000` tokens
- Default effective working context: `64,000` tokens
- Native dense context: optional and not verified

## Passed checks

- All eight source-to-package core runtime pairs matched the current clean
  source snapshot.
- Structural Safetensors package validation passed.
- HF-shaped package mechanical smoke passed.
- Package-local Ollama-shaped `/api/chat` accepted the 4M raw-input route.
- OpenCode and DeepSeek Harness completed read-only structured reads.
- Claude Code completed a read-only `Read` through the Anthropic Messages
  route.
- Client traces recorded zero model calls and no mutation claim.
- Release candidate manifest passed with `all_local_checks_pass: true`.

This is the current hash-bound experimental artifact. It is not an HF upload,
independent RTX 5060 Ti result, learned MiniMax parity result, dense-native 4M
decoder result, or production release authorization.
