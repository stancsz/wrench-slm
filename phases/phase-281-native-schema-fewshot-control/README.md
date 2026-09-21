# Phase 281: native schema few-shot control

Date: 2026-09-21

## Question

Does a canonical proposal example repair the malformed native decoder output,
or was the previous failure only caused by prompt shape or missing schema
guidance?

## Controlled run

The diagnostic probe `tools/probe_native_schema_fewshot.py` sent one canonical
`read_file` example followed by an ambiguous current request directly to the
current package's native OpenAI-compatible endpoint. This bypassed the
mechanical route. The payload target was 65,536 tokens and the native endpoint
returned HTTP 200 after one generation request.

Receipt:

- `C:\Users\stanc\AppData\Local\Temp\wrench-v103-native-schema-fewshot-64k-20260921.json`
- status: `NATIVE_SCHEMA_FEWSHOT_GAP`
- elapsed: 27,481.938 ms
- raw payload: 540,265 characters
- output: `{"n}}`
- parsed output: none
- model calls: one native upstream request

## Finding

Few-shot schema guidance did not produce a valid JSON object. Together with
the prior NVFP4 4M and 64K controls and the BF16 Transformers reference
control, this rules out missing examples as the primary explanation. The
learned native decoder remains diagnostic-only and fail-closed.

The production-value lane remains the embedded deterministic toolbelt with
strict verifier and fallback. A future learned-model candidate must use either
schema-focused SFT that demonstrates exact held-out proposals or a serving
backend with real constrained decoding. A valid format-only control is not a
quality, safety, MiniMax-parity, or release receipt.

## Verification

- Python compilation passed for the new diagnostic probe.
- The endpoint was native upstream only, not the package mechanical shortcut.
- GPU memory returned to the normal host-safe idle state after shutdown.
- No production default, README user change, or sealed final split was changed.

