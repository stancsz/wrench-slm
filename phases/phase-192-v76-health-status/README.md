# Phase 192: current portable package 4M intake verification

Date: 2026-09-20

The earlier attempt to make the health verifier status-first was not retained.
The live Docker health service can time out before returning HTTP headers, so
the held-out health case remains an environment-bound diagnostic miss rather
than a reason to weaken the bounded verifier.

## Current package

The source tree was materialized as:

`D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v77-current`

Structural validation passed with `PASS_STRUCTURAL_PACKAGE`.

The package-local model server accepted an exact 4,000,000-token estimated raw
payload through the OpenAI-compatible endpoint:

- status: `PASS_MODEL_LOCAL_SERVER_4M`;
- raw payload characters: `32,000,075`;
- HTTP 200 with embedded mechanical backend;
- request elapsed: `120.177 ms`;
- zero model calls;
- the current intent was recovered as a bounded `read_file` proposal.

This is direct model-directory raw intake plus embedded MapReduce. It is not a
dense-native attention claim.

## Held-out boundary

The v76 health-status package replay remained `43/44` outcome matches and
`23/24` eligible exact accepts. The one miss was the live
`localhost:4000/health` service timing out before headers. The v2 final slice
remains diagnostic-only until it runs against an isolated deterministic health
fixture without changing the sealed prompt or oracle.
