# Iteration 206: local run report

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-QWEN35-4B-LORA-CONTEXT-ITER206-20260929-01`  
Nonce: `8ea69481-5d65-4c7a-8a56-8d3b3a27148d`  
Protocol: [Iteration 206 protocol](iteration-206-qwen35-4b-lora-context-pair-protocol-20260929.md), SHA-256 `3786AB66487DC63BD8F64A6E182196672D1C8CAB42CA0C91A73F10C9B8042E03`  
Runner SHA-256: `E9B646AEA4C04B3739EA949DB82147E55A5B922CA4917BA28F1CF9CFEAE1C55C`  
Required repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Active goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Result

The pinned local run completed on the RTX 5060 Ti. The output receipt is
`C:\wrench-slm-data\artifacts\wrench-gateway-model-research\iteration-206-qwen35-4b-lora-context-pair.json`, 10,450 bytes, SHA-256 `012D2EAF4659B5F1F519652CD85305728C035F260CAEA1E0F1847000666A586A`.

| Arm | Full-context local input tokens | Wrench-context local input tokens | Input reduction | Strictly verified |
| --- | ---: | ---: | ---: | ---: |
| Qwen3.5-4B base | 26,244 | 521 | 98.0148% | 0/3 |
| Qwen3.5-4B + screen-03 LoRA | 26,244 | 521 | 98.0148% | 0/3 |

The corresponding total-token reduction, including generated answer tokens,
was 97.9215% (26,269 to 546) in each arm. The context and answer token counts
are from the pinned local Qwen tokenizer. The three cases are reused authored
synthetic development lookups, not held-out or representative engineering
tasks. Every decoded answer had the requested content but an extra trailing
newline, so the preregistered strict string equality correctly scored all
rows as failures. No post-hoc normalization was applied.

This result measures only local prompt-size reduction for the tested fixture.
There were zero Frontier calls; Frontier token savings and all-in cost savings
remain `null`. It does not establish task utility, routing rate, 95/5/95
acceptance, or all-day engineering.

## Adapter-load issue

PEFT emitted a missing-adapter-keys warning during load. Read-only inspection
of the exact checkpoint found 64 LoRA tensors covering the intended eight
full-attention blocks `[3, 7, 11, 15, 19, 23, 27, 31]`, across `q_proj`,
`k_proj`, `v_proj`, and `o_proj`. The checkpoint keys use
`model.language_model.layers.*`; the warning names expected keys under
`model.layers.*`. This path mismatch leaves adapter load coverage unverified.
The base and LoRA answers were identical, which is consistent with (but does
not prove) the learned weights failing to attach. Do not use this run to infer
LoRA utility. Before a new paired run, resolve the model-class/key mapping and
add a load-time assertion that every intended trained tensor is attached to
the expected module; then create a fresh protocol, output path, and independent
package review.

## Runtime and resources

- Exact base: `Qwen/Qwen3.5-4B`, revision
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, 14 pinned files totaling
  9,342,907,469 bytes; inventory SHA-256
  `30B09CF32F06FAE5418A0B925820202BFDF9E1C2A1F009D12E6396D10AED15A`.
- Exact inactive adapter: screen-03 fit-01; weights SHA-256
  `051a942cc306d15ff22ad300d6256cc4b8e6335b9c6263b65696353b04938e5c`,
  config SHA-256
  `f77ecf3c2e87b2586563f3ca6017b74f62b180c31f67260a590ccff85453531f`.
- Python 3.13.15, Torch `2.14.0+cu132`, Transformers `5.17.0`, PEFT
  `0.21.0`, CUDA `13.2`; isolated package manifest SHA-256
  `46576C195C4A131D063D952C10175C5D54C0F4079CDFF54815BF50C9594D4687`.
- Model load: 27.5078 s. Total run: 77.2929 s; generation: 76.0976 s.
- Peak CUDA allocated/reserved: 10,923,434,496 / 11,974,737,920 bytes.
- Lowest sampled free RAM: 19.57%; lowest sampled free VRAM: 22.16%.
  The 10% runtime floors held for the run.
- Frontier calls: 0. Provider spend: `$0`. Held-out split accessed: `false`.
- Adapter remains inactive. The run did not mutate repository files.

The bounded Iteration 206 storage reservation may be released now that the
process stopped and the output receipt and report have been counted. Preserve
the output and this report as negative/inconclusive evidence; do not overwrite
either artifact.
