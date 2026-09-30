# Iteration 039: SubRoute OpenCode setup and fresh admission (2026-09-27)

## Objective

Use the owner's existing SubRoute at `http://127.0.0.1:4000` as the designated
frontier route for future Wrench comparisons, and provide a version-matched
OpenCode configuration without sending a generation request.

## Setup added

Added an OpenCode v2.0.12 custom-provider example and setup notes:

- `examples/opencode_v2_subroute_capture/opencode.subroute.example.json`
  defines provider `wrench-subroute`, base URL
  `http://127.0.0.1:4000/v1`, and the gateway alias `openrouter`.
- The model becomes `wrench-subroute/openrouter`; the sample does not set a
  default model. It uses a process environment variable for the optional
  gateway key and stores no credential.
- The sample's 32,768 context and 8,192 output limits are configuration hints,
  not a hard aggregate token or cost budget.
- `examples/opencode_v2_subroute_capture/SUBROUTE_SETUP.md` explains how to
  merge the provider object and how the existing no-provider synthetic hook
  behaves.

The field names match the exact OpenCode v2.0.12 custom-provider docs. The
sample was not copied into a user's active OpenCode configuration, resolved by
the CLI, or used to issue a model request. The local Wrench campaign caller
remains the only intended paid-test path.

## Fresh read-only SubRoute snapshot

Read-only GETs to `http://127.0.0.1:4000/health/liveliness`, `/models`, and
`/model/info` returned HTTP 200. `/models` listed `openrouter` as an available
alias. The `openrouter` model-info entry reported:

| Field | Observed value |
| --- | --- |
| LiteLLM route model | `openrouter/minimax/minimax-m3` |
| Mode | `chat` |
| Advertised maximum input/output | 1,048,576 / 512,000 tokens |
| Advertised input/output cost | `$0.30/M` / `$1.20/M` |
| `supports_function_calling` | `true` |
| `supports_tool_choice` | `true` |

These are current gateway metadata fields, not a selected-provider, billed
usage, or successful-tool-call receipt. They differ from the earlier
iteration-015 metadata snapshot and its source-based tool-support conclusion.
That historical record remains unchanged; the discrepancy now needs an
explicitly capped end-to-end test before routing or compatibility claims.
Earlier `/api/active-model` reads reported alias `openrouter`, force mode, and
policy version 4; this turn did not change route configuration.

## Wrench fit state and host admission

The hash-bound preflight-05 receipt at
`C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\run-manifest.json`
records one preflight-only optimizer step over eight synthetic train rows for
`Qwen/Qwen3.5-0.8B`, with no adapter output, no fit mode, and no held-out read.
It matched 24 attention projection modules and 540,672 trainable parameters.
The resource log's minimum free RAM fraction was 10.985% and minimum free VRAM
fraction was 54.466%; fit admission began at 17.502% free RAM. This is only
runtime compatibility evidence; the full 96-step fit-03 has not run.

At this iteration's fresh sample, system RAM was 2,863.9/32,701.8 MiB free
(8.76%), below the 10% runtime floor and fit-03's 25% start gate. The RTX 5060
Ti reported 15,147/16,311 MiB free VRAM. C: had 132.13 GiB free. No Wrench
trainer, inference, benchmark, or test job was admitted. The running Codex Node
helper processes are unrelated and were left untouched.

Storage was `WITHIN_LIMIT` at 10,990,166,668 actual bytes and 8,303,000 bytes
in active reservations before this documentation job. This job reserved
200,000 bytes. No model download, adapter, runtime, or provider artifact was
created.

## Exact identities and limits

| Artifact | SHA-256 |
| --- | --- |
| `tools/train_gateway_lora_screen_02_gpu.py` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` |
| `tools/score_gateway_lora_screen_02.py` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` |
| `docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md` | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A6E75EE12DACE33B5` |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\run-manifest.json` | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\resources.jsonl` | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` |
| `examples/opencode_v2_subroute_capture/opencode.subroute.example.json` | `58586D2A51A9F90BA4737DEC69034430AE9B822127B97479E5443713095D2D48` |
| `examples/opencode_v2_subroute_capture/SUBROUTE_SETUP.md` | `BDB4AAFFB2EA53C58308FD46AF7FA37E1E56C9A95A6428176C58FC758A9E81BC` |

The fit protocol is hash-bound and retains an obsolete closing sentence that
says preflight 05 has not run. It was not edited because that would invalidate
the exact-hash review. The manifest and iteration-008 receipt establish that
preflight 05 completed; add an explicit reviewed protocol amendment before
the next fit admission.

No POST reached port 4000. No provider call, generation, bill, user config
change, test, model inference, or fit occurred. The numeric aggregate spend
cap is still absent. The research target remains unproven: this setup does not
establish local completion rate, escalation rate, frontier-token savings,
all-in cost reduction, tool-call reliability, or all-day engineering.

## Next gates

1. Wait until RAM and VRAM exceed their required floors; update the hash-bound
   fit protocol with a reviewed amendment and fresh fit-03 admission.
2. Run the focused local campaign-ledger and OpenCode hook tests only after
   the 10% resource floor is available.
3. Keep provider traffic closed until a numeric aggregate cap is supplied and
   the exact-route caller enforces it with durable usage and bill receipts.
4. Exercise the installed OpenCode runtime against a loopback-only mock before
   any capped provider request.
5. Compare the full Wrench workflow against frontier-only on frozen tasks;
   do not infer success or savings from the setup or metadata.

## Sources

- [OpenCode v2.0.12 custom-provider docs](https://github.com/anomalyco/opencode/blob/v2.0.12/packages/web/src/content/docs/providers.mdx#custom-provider)
- [OpenCode v2.0.12 request hook source](https://github.com/anomalyco/opencode/blob/v2.0.12/packages/core/src/session/model-request.ts#L1497-L1518)
- [Earlier SubRoute boundary snapshot](iteration-015-subroute-mock-boundary-20260927.md)
- [Preflight 05 receipt and exact trainer protocol](iteration-008-preflight-05-20260927.md), [LoRA fit protocol](lora-screen-02-gpu-protocol-20260927.md)
