# Phase 102: pinned native 2M direct probe

Status: direct-input capacity pass, throughput fail.

The v28 NVFP4 portable package was served through the bundled FreeToken
launcher with the pinned 4M KV geometry:

- `--num-tokens 4000000`
- `--kv-reserve-tokens 8192`
- automatic expert cache
- native direct input enabled
- 4M configured maximum sequence length

The probe sent the generated payload directly to the model endpoint, with no
gateway reducer and no context ledger. It used `max_tokens=1` so the receipt
primarily measures prefill and native input handling.

| requested | actual prompt | HTTP | truncated | elapsed |
| ---: | ---: | ---: | --- | ---: |
| 2,000,000 | 1,999,929 | 200 | false | 1,287,078.199 ms |

This closes the pinned 2M no-truncation capacity milestone. It is not a fast
serving result. The measured prefill is about 21.45 minutes, so native full
context must remain an experimental path while the deterministic mechanical
route handles routine work before expensive model execution.

Receipt: `native-2m.json`.
