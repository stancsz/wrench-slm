# Iteration 198: OpenCode HTTP hook loopback runtime probe

Date: 2026-09-29  
Disposition: **PASS for the narrow OpenCode v2.0.12 loopback runtime contract**  
External provider, SubRoute, and billing claims: **not tested**

## Question

The prior JavaScript observer tests invoked hook callbacks directly. They did
not show whether OpenCode itself stops HTTP transport when an `http.request`
hook throws, or whether the registered response hook can read usage from a
real response stream. This iteration exercises both behaviors through the
installed OpenCode CLI and a fake server bound only to `127.0.0.1`.

## Frozen identities

- OpenCode: `@opencode/cli` 2.0.12 at
  `C:\Users\stanc\.local\tools\node-v24.19.0-win-x64\node_modules\@opencode\cli\bin\opencode.exe`.
- Runtime probe source: [run.mjs](../../../examples/opencode_v2_http_hook_runtime_probe/run.mjs),
  SHA-256 `450E462DE65238D4A87D2358C47EB423BCD619A9008CF8370288A4E15A043716`.
- Hook plugin source: [plugin.mjs](../../../examples/opencode_v2_http_hook_runtime_probe/plugin.mjs),
  SHA-256 `BD5BD351C70A33B8BC48A0E3A8CC76E81B713AC166E69F1EE62F677D899BF9D0`.
- OpenCode project configuration was created in a fresh run directory and
  pointed to the local fake OpenAI-compatible endpoint. The child environment
  did not inherit provider credentials.
- Final run ID: `WRENCH-OPENCODE-HTTP-LOOPBACK-RUNTIME-VERIFY-20260929-05`.
- Final result: `C:\wrench-slm-data\artifacts\WRENCH-OPENCODE-HTTP-LOOPBACK-RUNTIME-VERIFY-20260929-05\result.json`,
  1,725 bytes, SHA-256
  `1A5905E88CAD8B2D037D755A5295EE6556B6E91ADF3B1217BD10308B57D26FC5`.
- Final response receipts: two rows, one `title` event and one `primary` event.
  Each carried a distinct request ID echoed by the fake server and matched to
  one response receipt.

## Results

| Check | Result |
|---|---:|
| Throwing request hook, fake completion POSTs observed | 0 |
| Normal arm, fake completion POSTs | 2 |
| Response-hook receipt rows with matched request IDs | 2/2 |
| Fake usage in each response receipt | 17 input, 2 output, 19 total |
| External provider calls | 0 |
| Provider-reported or billed usage | None |

The blocking process exited with code 1 after the hook rejected the request.
The normal local fake arm exited with code 0. Both fake completions returned a
small synthetic SSE stream containing usage. The response hook cloned and read
the stream; it did not consume or replace the response. The hook also receives
auxiliary `title` requests, so accounting must include those requests when
connected to a real provider.

## Limits

This verifies a narrow transport and usage-observation contract for this exact
OpenCode build with an in-process loopback fake. It does not verify SubRoute,
any provider's usage schema, provider billing, retries, concurrent request
stress, WebSocket traffic, real token savings, task success, or the 95% goal.
OpenCode's current plugin documentation states that HTTP hooks cover native
HTTP traffic while WebSocket provider traffic bypasses them:
[OpenCode v2 plugin HTTP hooks](https://opencode.ai/v2/docs/build/plugins#native-http).

## Admission and output accounting

The job ran after storage status and resource checks. At the final pre-run
sample the host had 29.88% free RAM and 15,211/16,311 MiB free VRAM. The C:
volume had over 129 GB free. The active reservation was 50,000,000 bytes.
Five bounded exploratory outputs were retained, totaling 192,782,453 bytes;
the final run output directory accounts for 38,581,017 bytes. Thus the
reservation undercounted cumulative output growth. The storage checker still
reported the aggregate Wrench inventory below 50 GB, but future runtime probes
must reserve the full cumulative peak before starting. No further probe runs
are admitted under this reservation.

The first four probe iterations were retained as debugging evidence. Iteration
01–02 did not load the external plugin path; 03 exposed the missing plugin SDK
in the isolated profile; 04 proved transport blocking and synthetic usage
capture but assumed only one completion request. Iteration 05 added an
in-workspace no-dependency plugin and exact response/request ID correlation,
and passed all assertions.

## Reproduction

Use the command in the example [README](../../../examples/opencode_v2_http_hook_runtime_probe/README.md)
with a new output directory, after reserving its bounded peak and checking
fresh RAM, VRAM, and volume headroom. The output directory is one-shot.
