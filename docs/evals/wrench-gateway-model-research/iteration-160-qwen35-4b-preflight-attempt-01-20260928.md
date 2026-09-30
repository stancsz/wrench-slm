# Iteration 160: Qwen3.5-4B preflight attempt 01

- Job ID: `WRENCH-GATEWAY-LORA-SCREEN-03-QWEN35-4B-PREFLIGHT-20260928-01`
- Disposition: **FAILED before tokenizer/model loading, optimizer work, or adapter creation.** Do not interpret this as model compatibility or a training result.
- Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`
- Active gateway goal hash: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`
- Trainer SHA-256: `56582C343C1C0E4DB4D1DB597A853677D72686D195F24D033E4D989712CC6AB4`
- Protocol SHA-256: `8669827AE7D4EAD882C0BDEB21DD7C0E775E999BC77D5621886C26B2FDB79E70`

## Result

The runner exited with code 1 at `tools/train_gateway_lora_screen_03_4b_gpu.py:1153` while calculating the tokenizer chat-template hash. `tokenizer` had not yet been assigned, producing `UnboundLocalError: cannot access local variable 'tokenizer' where it is not associated with a value`. The tokenizer initialization appears later in the source, after that hash calculation. This is a source-order defect missed by the static review.

The runner finalized its manifest as `FAILED`; it reports `heldout_opened_by_runner: false`, `output_dir: null`, and `runtime_scratch_peak_bytes: 0`. The failure occurred before tokenizer and base-model initialization, optimizer step, inference, or adapter output. No provider request was made.

## Preserved outputs

| Output | Bytes | SHA-256 |
|---|---:|---|
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-03-qwen35-4b-preflight-01\run-manifest.json` | 3,514 | `F26301E1EEEFA336A5451917EEBD8E0159A740FE7902BDCE5C2B22B0D423B3B9` |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-03-qwen35-4b-preflight-01\resources.jsonl` | 22,281 | `C2DFB795D5F465AD70E9DDF90FB144E9E1A99F6517F8D34D13E596D509F67837` |
| Unique job claim marker | 1 | retained under the job-specific cache claim directory |

The manifest binds resource log SHA-256 `c2dfb795d5f465ad70e9ddf90fb144e9e1a99f6517f8d34d13e596d509f67837` and runner SHA-256 `56582c343c1c0e4db4d1db597a853677d72686d195f24d033e4d989712CC6AB4` (hex case is immaterial). Logged minimum free fractions were 17.61% RAM and 92.44% VRAM; no resource-floor breach was observed. Resource values are scoped to this short failed attempt.

## Next gate

Preserve these outputs unchanged. Correct the tokenizer initialization order in a new trainer revision and assign a distinct preflight job ID, claim directory, and log directory. Refresh the independent source review against the new trainer and protocol hashes. A new preflight requires a fresh storage reservation and resource sample. Any 96-step fit remains separately gated by a successful preflight, a fresh reservation, and at least 25% free system RAM at fit start.
