# Iteration 199: hardened OpenCode HTTP hook runtime probe

Date: 2026-09-29  
Disposition: **PASS for the narrow OpenCode v2.0.12 loopback runtime contract**  
Real provider usage, billing, and token savings: **not tested**

## Scope

Iteration 198 exposed two remaining probe issues: output admission was smaller
than retained exploratory artifacts, and the path and correlation assertions
were not strict enough. This run used the corrected source, a fresh one-shot
output directory, an in-process fake OpenAI-compatible endpoint on
`127.0.0.1`, and OpenCode v2.0.12. It did not contact SubRoute or an external
provider.

The runner now requires the output directory to be a new direct child of the
canonical approved artifacts directory, rejects reparse points while walking
output, caps final output at 1 MiB, caps each transient OpenCode profile at 45
MB, caps child output and synthetic receipts, and removes only its own exact
profile directory after each process exits. It compares the complete unique
request-ID set with the response-ID set and verifies projected final bytes
before writing the result.

## Identities and result

- OpenCode `@opencode/cli` version 2.0.12.
- Plugin [plugin.mjs](../../../examples/opencode_v2_http_hook_runtime_probe/plugin.mjs),
  SHA-256 `026E19CE23FAF42014949BE8138089772CBADE322346DB95E3DBBACA0A40EAF8`.
- Runner [run.mjs](../../../examples/opencode_v2_http_hook_runtime_probe/run.mjs),
  SHA-256 `48E8101BD074BDB49148695F86ABB9D54EA5BB72EB54C64D7803646224CCA5B2`.
- Run ID `WRENCH-OPENCODE-HTTP-LOOPBACK-HARDENED-VERIFY-20260929-03`.
- Result `C:\wrench-slm-data\artifacts\WRENCH-OPENCODE-HTTP-LOOPBACK-HARDENED-VERIFY-20260929-03\result.json`,
  6,182 bytes, SHA-256
  `7985B3CA703C620AC97CC576111BEB3A1AAE04773D1C17E80499EBAE85E6E72E`.
- Request/response receipts `hook-receipts.jsonl`, 720 bytes. The two IDs
  match exactly, corresponding to OpenCode `title` and `primary` request kinds.

| Check | Result |
|---|---:|
| Block arm fake completion POSTs | 0 |
| Observe arm fake completion POSTs | 2 |
| Unique request IDs matched one-to-one to response IDs | 2/2 |
| Synthetic usage per response | 17 input, 2 output, 19 total |
| Final retained output | 6,902 bytes / 1 MiB cap |
| Peak OpenCode profile scratch observed | 19,290,593 bytes / 45 MB cap |
| External provider calls | 0 |

Block mode exited with code 1 after the `http.request` hook rejected the
request; the local endpoint saw no completion POST. Observe mode exited with
code 0. The fake server echoed the unique request ID in each response, and
both actual OpenCode `http.response` events wrote the expected fixture usage.
The response bodies used a synthetic SSE stream. OpenCode's official v2 plugin
documentation describes native HTTP request/response hooks and says native
WebSocket traffic bypasses them:
[OpenCode v2 HTTP hooks](https://opencode.ai/v2/docs/build/plugins#native-http).

## Admission, failures, and limits

The final run had a fresh 50,000,000-byte reservation. At admission, the host
had 29.95% free RAM, 15,198/16,311 MiB free VRAM, and more than 129 GB free on
C:. The run remained provider-free. Each temporary profile was deleted after
its OpenCode process terminated; only the receipts and result remain.

Hardened attempt 01 stopped when the runner accidentally applied its 1 MiB
final-output cap to OpenCode's transient SQLite profile. Its incomplete
profile output is retained and counted at 19,290,594 bytes. The cap was
separated into a measured 45 MB transient-scratch limit and 1 MiB retained
output limit before attempts 02 and 03. Attempts 02 and 03 passed; attempt 03
is the final identity above. The earlier Iteration 198 reservation undercount
is recorded in that report and is not treated as admitted evidence.

These results verify a narrow hook and usage-parser behavior on this exact
OpenCode build with a local fixture. They do not establish response usage or
billing semantics for real providers, retries, concurrent load, every provider
transport, token savings, task quality, or the 95/5 product target. All usage
and cost fields remain synthetic, provider-null, and billing-unverified.
