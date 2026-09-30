# Iteration 201: Qwen3.5-2B preflight 02 projection dimensions

Date: 2026-09-29  
Disposition: **FAILED at a fail-closed LoRA target dimension check**  
Weights loaded: **yes**; optimizer steps: **0**; held-out data opened: **no**

## What happened

After the Iteration 200 metadata-layout issue was resolved, the second
one-shot preflight verified the pinned 13-file model inventory and loaded all
617 weight tensors. It then stopped while validating the first `q_proj` LoRA
target:

`projection dimensions changed from the pinned config: model.language_model.layers.11.self_attn.q_proj`

The package assumed `q_proj` was 2048 by 2048. The installed and pinned
Transformers 5.17.0 Qwen3.5 implementation constructs it as
`hidden_size -> num_attention_heads * head_dim * 2`. For the pinned config,
that is 2048 by 4096. The extra width contains the query and its gating branch.
The runner's architecture check caught the stale assumption before target
selection, training, or an optimizer update. Its earlier parameter estimate
of 638,976 was therefore also low; rank 8 over the same six q/k/v/o layers
would be 737,280 parameters if the q projection is adapted as one full matrix.
That corrected count must be reflected in the next reviewed package before
another preflight.

## Resource and run evidence

- Job ID: `WRENCH-GATEWAY-LORA-SCREEN-04-QWEN35-2B-PREFLIGHT-20260929-02`.
- Status: `FAILED`; no output adapter; runtime scratch peak was zero.
- Model: `Qwen/Qwen3.5-2B`, revision
  `15852e8c16360a2fea060d615a32b45270f8a8fc`.
- Inventory SHA-256:
  `23E0D5F79E57D41AB9F007B697D8F75F56F5F528519BFDF15F406E1F28DF3DD5`;
  13 paths and 4,571,274,023 bytes matched the local top-level model files.
- Runner SHA-256:
  `5178AD9E24E5BEB79049A6517F357208CA83F378707268A664EA95B369535253`.
- Protocol SHA-256:
  `2AB727A4B30DEE5079528882693AD157D58A374CE52ECC5E70712EFC081E160A`.
- Run manifest: 5,625 bytes, SHA-256
  `99B8B8DF3D457092F12C642E0D8F9B12312B307AAABFBC222CDD83F2CD4C0702`.
- Resource log: 21,856 bytes, SHA-256
  `1EEDCDD49580396BE5BA254BF0B068E121232CD77E5EEEDDC95D6DC32214EF4D`.
- Start RAM free: 29.43%; minimum observed RAM free: 23.49%.
- Minimum GPU VRAM free: 10,905 MiB / 16,311 MiB (66.81%).
- C: free space at admission: 129,727,598,592 bytes. Reservation: 300,000,000 bytes.
- Runtime package: Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0,
  PEFT 0.21.0, Accelerate 1.15.0; GPU UUID
  `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`.

The 2B weights loaded on the RTX 5060 Ti without an OOM or reserve breach in
this run. This is initial load-feasibility evidence only; it does not show
forward/backward fit, latency under representative work, adapter utility,
coding completion, Frontier-token savings, or all-in cost. No provider calls
were made. Attempt 02 and its output paths are consumed and must not be reused.

## Next gate

Correct the pinned projection widths and derive the LoRA parameter count from
those same widths. Create attempt-03 one-shot paths and protocol, obtain a new
independent exact-hash review, then take fresh resource and storage admission
before any further model loading. The previous `.cache` metadata remains
preserved at `C:\wrench-slm-data\cache\hf-snapshot-metadata\Qwen3.5-2B\.cache`;
its 16 files total 3,474 bytes and were SHA-256-checked before and after the
move. No snapshot file was changed.
