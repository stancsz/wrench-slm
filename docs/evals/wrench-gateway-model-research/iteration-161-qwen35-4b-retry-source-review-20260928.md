# Iteration 161: Qwen3.5-4B trainer retry source review

- Assignment: `WRENCH-QWEN35-4B-TRAINER-REVIEW-RETRY-ITER161-20260928`
- Nonce: `77cb3cdd-e073-4a09-b38f-a03f1768305a`
- Verdict: **CONDITIONAL for attempt-02's one-step preflight only.** No full fit authorization.
- Expected HEAD before/after: `af01304824f079a64b6c3902397a2034b843511a`
- Active gateway goal hash before/after: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

| Identity | SHA-256 before and after |
|---|---|
| `tools/train_gateway_lora_screen_03_4b_gpu.py` | `451C89DD972086312EC69F5DF586B10C9809E679FD41E7804E488AD85B7C05BB` |
| `docs/evals/wrench-gateway-model-research/lora-screen-03-qwen35-4b-gpu-protocol-20260928.md` | `232365B9ADBD8995EA57D6DE410D2D55BACD241A0039E4F70E9A2D35AD1C8D33` |
| Attempt-01 report | `43D908F90F4DBB50679CDB7F80E31918E34B4B7BEBFABE6525021DE456E40F0B` |
| `tools/wrench_windows_pinned_tree.py` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |
| Pinned Qwen3.5-4B config | `DDC63E1C717AFA86C865BB5E01313D89D72BB53B97AD4A8A03BA8510C0621670` |

The reviewer confirmed the specific attempt-01 defect is fixed: `AutoTokenizer.from_pretrained(...)` assigns `tokenizer` before the chat-template hash reads it. Attempt 02 uses a distinct job ID, log path, and job-specific claim/scratch path. Attempt-01 outputs remain untouched. Static review found no other source issue blocking the one-step preflight; live PEFT matching, BF16 model load, and the finite update remain unverified and must be shown by that preflight.

Reviewer resource samples: start RAM 20.50%, VRAM 15,191/16,311 MiB free; end RAM 20.46%, VRAM 15,206/16,311 MiB free. These do not replace a fresh run-admission sample.

Allowed review scope was source inspection only. Commands were `git rev-parse HEAD`, before/after `Get-FileHash` of the six assigned identities, live RAM/VRAM queries, bounded `Get-Content`, and `rg` restricted to assigned source/protocol files. No tests, Python/AST execution, model/runtime, preflight, training, inference, benchmark, provider/network/SubRoute call, credential access, held-out access, or edits were performed. No reviewer output artifact was written.

## Remaining gates

1. Obtain fresh storage status and reserve at least 250,000,000 bytes for exact job ID `WRENCH-GATEWAY-LORA-SCREEN-03-QWEN35-4B-PREFLIGHT-20260928-02`; include all external Wrench paths and confirm at least 5 GiB destination headroom beyond the reservation.
2. Require at least 10% free RAM and VRAM at start and throughout the preflight; preserve any failure receipt. Never reuse attempt-01 outputs.
3. For any later 96-step fit, require a successful matching attempt-02 preflight, a fresh 2,000,000,000-byte fit reservation, and at least 25% free system RAM at fit start plus 10% RAM/VRAM throughout.

