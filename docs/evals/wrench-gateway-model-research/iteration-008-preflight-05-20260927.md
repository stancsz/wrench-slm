# Iteration 008: attention-only preflight 05

Date: 2026-09-27 (America/Edmonton)

Status: **TRAINING-SOURCE REVIEW 04 PASS FOR ITS HASHED SCOPE; PREFLIGHT COMPATIBILITY PASS; CURRENT FIT-PACKAGE REVIEW PENDING; FIT 03 BLOCKED BY LIVE RAM GATE**

## Scope

This records source review 04 and the one-step attention-only compatibility
preflight for the pinned Qwen3.5-0.8B candidate. Review 04 covered the goal
and iteration 007 hashes that were current at review time; the updated goal
and this iteration 008 record require a fresh exact-hash package review before
fit 03. This evidence does not establish policy
quality, useful coding ability, 95/5/95 results, paid savings, or sustained
engineering behavior. It does not admit the full fit or heldout scoring.

## Independent exact-hash review 04

Assignment `WRENCH-GW-ATTN-FIT-PATH-REVIEW-20260927-04`, nonce
`7e85aed7-6849-4454-b84b-c1061fa45a3e`, returned **PASS** for its static scope
with no P1/P2 findings. Repository HEAD was
`af01304824f079a64b6c3902397a2034b843511a` before and after. The reviewer
verified unchanged before/after hashes for the trainer, pinned-tree helper,
focused tests, training protocol, goal, iteration 007, and storage policy.
The review confirmed reservation plus 5 GiB headroom is enforced at admission
and checkpoint, output finalization uses no-replace rename, and resource
minima are recomputed from the hash-bound log. This review did not run tests or
authorize a workload by itself.

## Preflight 05 result

The user-authorized local compatibility check ran using the pinned Python
3.13.15 / Torch 2.14.0+cu132 environment, Qwen3.5-0.8B revision
`2fc06364715b967f1860aea9cf38778875588b17`, and profile
`softmax-attention-only`. It used eight synthetic train rows and exactly one
optimizer step. It matched 24 `self_attn` q/k/v/o modules and instantiated
540,672 trainable parameters. The manifest reports finite mean loss
`1.7103413194417953` and finite gradient norm `3.2710537910461426`.

| Measure | Observed |
|---|---:|
| Minimum free RAM | 10.9850% |
| Minimum free VRAM | 54.4663% |
| Runtime scratch peak/final | 0 / 0 bytes |
| Adapter output | None (`output_dir` is null) |
| Heldout opened by runner | No |
| Provider/generation calls | None |

The 10% RAM/VRAM runtime floors were maintained. RAM was close to the floor.
The manifest's preflight-start observation was 17.5017% free RAM, below the
fit's separate 25% start requirement. A fresh read after the run was 17% free
RAM. Fit 03 therefore remains blocked. No application was terminated.

## Identity and receipts

| Item | Identity |
|---|---|
| Job ID | `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-05-ATTN` |
| Trainer SHA-256 | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` |
| Protocol SHA-256 | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5` |
| Manifest SHA-256 | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` |
| Resource log SHA-256 | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` |
| Claim SHA-256 | `68B7BD7F746419F88EE717C4B238DAA9328663B947992642C95F85193F82EDC0` |
| Reservation receipt SHA-256 before release | `9692D2D80AE42A070139E2BEF4E45E3BBC3B0E613122EACC92C2FF2A1DFBC601` |
| Dataset manifest SHA-256 | `11683129106ff2448930818d6631b8e76201798893e7587ecb0872cbf6bcebed` |
| Base model inventory SHA-256 | `64c38776f5d208c666e7033a0e121a63a240538f1f55b8865b5d31fddc474519` |

The finalized log contained 23,967 bytes; the manifest contained 5,622 bytes;
the claim contained 260 bytes. The fit-03 adapter and staging paths were absent.
The one-step job stopped, all outputs were accounted, and its
250,000,000-byte reservation was released. The subsequent storage report was
`WITHIN_LIMIT`: 10,955,471,440 actual bytes, 6,103,000 active reserved bytes,
and no storage-checker errors. C: had approximately 156 GB free at the earlier
admission sample; this does not replace a fresh pre-fit disk and memory check.

## SubRoute boundary

The requested existing endpoint remains `http://127.0.0.1:4000`; the saved
read-only configuration has force-routed alias `openrouter` and the prior
audited mapping to OpenRouter/MiniMax M3. No route configuration changed and
this iteration sent no generation request. The aggregate USD cap and actual
per-generation provider/usage receipts are still missing, so paid arms remain
closed.

## Next gates

1. Before fit 03, obtain a fresh storage status and 1,500,000,000-byte unique
   reservation, recheck destination free space, and start only if live free RAM
   is at least 25%. Preserve the 10% RAM/VRAM runtime floors and the hash-bound
   preflight/protocol identities.
2. Revise the screen-02 scorer to verify fit 03's job ID, paths, source and
   adapter. Independently review the exact scorer hash and run only its
   separate dev-only inference preflight before any heldout access.
3. Keep the sealed heldout data unopened until all scorer gates pass. No
   adapter activation is included in this diagnostic.
4. Keep SubRoute generation disabled until the owner sets a numeric aggregate
   USD cap and the caller can fail closed on missing or mismatched provider,
   token-usage, and cost receipts.

The preflight validates code/model/runtime compatibility only. No decision
quality, coding, context-compression, token-savings, cost-savings, or all-day
engineering claim is supported by this run.
