# Iteration 159: Qwen3.5-4B LoRA feasibility review

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-4B-LORA-PACKAGE-FEASIBILITY-REVIEW-ITER159-20260928`  
Nonce: `4d5bf817-38c6-4be5-bbde-f9c75df7349d`  
Disposition: **NO-GO for the existing trainer; conditional candidate for a new 4B package**  
Repository HEAD before and after: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Finding

The existing GPU trainer is bound to Qwen3.5-0.8B, its revision and inventory,
24 expected LoRA targets, candidate metadata, preflight receipt, and FP32 load
path. It cannot be reused for Qwen3.5-4B. A 4B FP32 base requires roughly
16 GB decimal for weights alone, before activations or runtime overhead, so it
exceeds the 16,311 MiB GPU. This rejects the current FP32 fit path, not a
separately designed BF16 or quantized path.

The 4B configuration has 32 text layers and full attention every fourth
layer, giving eight full-attention blocks. The proposed finite profile is
`q_proj`, `k_proj`, `v_proj`, and `o_proj` under
`model.language_model.layers.*.self_attn.*`, restricted to `nn.Linear`.
That implies 32 modules only if each expected module exists once per block.
The approximate rank-8 trainable count is 1.31M under standard projection
shapes. Both figures remain unverified until instantiated-module inspection.
The multimodal vision tower must be explicitly excluded and remain frozen.

The previous common-battery run is the current quality lead: the 4B base
verified 3/3 answers with related TOML-table context; 2B and 0.8B each
verified 2/3 on that aggressive arm. The task set has only three reused,
experimenter-authored cases. It shows neither LoRA utility nor representative
coding ability. The 4B run used 10.92 GB peak CUDA allocation and retained at
least 25.38% free VRAM and 14.68% free RAM during inference. This does not
predict training fit.

## Admission blockers and next candidate gates

At review finish, RAM was 20.54% free and VRAM was 15,185/16,311 MiB free.
The existing fit protocol requires at least 25% free RAM at start, so no fit
is admitted at this snapshot. A new 4B BF16 or quantized package must pin the
model revision, all 14 inventory files, config and tokenizer, runtime, adapter
targets, data and split identities, output and scratch caps, and exact peak
storage reservation. It needs a source review followed by a one-step GPU
preflight that confirms module names/classes/count, trainable parameters,
vision exclusion, text-only task compatibility, and 10% RAM/VRAM floors.
Full fitting additionally requires a fresh >=25% RAM start sample, destination
headroom, and its own reviewed fit package. Keep the candidate inactive and
the held-out split sealed.

The screen-01 manifest, train, and dev hashes were verified. The reviewer read
only the train/dev payloads to confirm 256/64 row counts and balance across
four synthetic families. No held-out payload was opened. No model was loaded;
no inference, fit, tests, provider request, credential access, network call,
or file modification occurred during the review. A guessed initial config path
failed; the pinned snapshot path was then found and its assigned identity
matched.

## Hashes rechecked after review

| Input | SHA-256 |
|---|---|
| `tools/train_gateway_lora_screen_02_gpu.py` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` |
| `docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md` | `EDAA9A20E66E18F005420B3F797EED085B002BBE9AD266A5E75EE12DACE33B5` |
| `docs/goal/wrench-gateway-model-research/GOAL.md` | `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59` |
| 4B local inventory | `30B09CF32F06FAE5418A0B925820202BFDDF9E1C2A1F009D12E6396D10AED15A` |
| Pinned 4B `config.json` | `DDC63E1C717AFA86C865BB5E01313D89D72BB53B97AD4A8A03BA8510C0621670` |
| Screen-01 manifest | `11683129106FF2448930818D6631B8E76201798893E7587ECB0872CBF6BCEBED` |
| Screen-01 train split | `22F45C8B51EF680F9D05E8C42243EBB34E9F596B22D76577C64E371D272A39D2` |
| Screen-01 dev split | `EE0F6DE198CB1D6C6B4EA19A138CCDA9F0D9F1562232430A0A9CE15307760AA7` |

The 4B upstream revision is `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`,
with Apache-2.0 license and 9,342,907,469 inventoried bytes.
