# Phase 374: Current Package Size Audit

Date: 2026-09-21

Status: `PASS_PACKAGE_SIZE_AUDIT_NO_SMALLER_VALIDATED_CANDIDATE`

## Scope

This phase records the size boundary of the current release candidate. It is
an audit, not a promotion of a new package and not evidence that the package
is production-ready.

## Current candidate

- Package: `D:\models\_wrench-release-candidate-59b8b7c`
- Total package bytes: `3,423,698,468` (`3.189 GiB`)
- Weight shard bytes: `3,403,035,760` (`3.170 GiB`)
- Weight format: `NVFP4-W4A16-ModelOpt`
- Verified parameters: `3,881,244,016`
- Parameter ceiling: `4,250,000,000`
- Weight shards: `2`

The remaining package bytes are the tokenizer, runtime, configuration,
client adapters, verifier, and receipts. The large download is therefore
primarily the quantized model weights, not duplicated context data.

## Local candidate scan

The local `D:\models` package scan found no safetensors candidate below 3 GiB
that was both present and verifiable. The standard BF16 candidate is about
7.35 GiB. No smaller candidate is promoted from this audit.

## Interpretation

The current artifact is materially smaller than BF16, but it is still a large
download for casual copy-paste use. The next size-reduction work must produce
a new, independently verified lower-bit or smaller-parameter artifact and
rerun the full package, client, 4M intake, retrieval, and 220-case gates. A
smaller file alone is not sufficient for release.

This phase does not claim stock Ollama native checkpoint loading, dense-native
attention quality, MiniMax parity, independent RTX 5060 Ti verification, or
production readiness.

## Receipt

See `receipt.json` for the byte counts, hashes, and scan boundary.
