# Wrench gateway LoRA screen 03: Qwen3.5-4B BF16

Status: **implementation package only. No preflight or fit has run, and this
protocol does not itself authorize execution. An independent exact-hash source
review must pass before the one-step preflight. The full fit additionally needs
a successful matching preflight, a fresh storage reservation, and at least 25%
free RAM at process start. No adapter, model-quality, engineering-effectiveness,
or 95/5/95 result exists.**

## Fixed candidate and data

- Base model: `Qwen/Qwen3.5-4B`, revision
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, local snapshot only at
  `C:\wrench-slm-data\weights\qwen35-4b-hf-cache\models--Qwen--Qwen3.5-4B\snapshots\851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.
  The supplied local inventory identifies Apache-2.0 and 14 files totaling
  9,342,907,469 bytes. Inventory SHA-256 is
  `30B09CF32F06FAE5418A0B925820202BFDDF9E1C2A1F009D12E6396D10AED15A`.
- `config.json` SHA-256 is
  `DDC63E1C717AFA86C865BB5E01313D89D72BB53B97AD4A8A03BA8510C0621670`.
  The trainer validates the pinned hybrid config before target selection:
  hidden size 2560, 32 text layers, 16 query heads, 4 KV heads, head dimension
  256, and BF16 dtype. Full-attention layers must be indices
  `[3, 7, 11, 15, 19, 23, 27, 31]`; the other 24 layers must be linear
  attention. The vision configuration is present, but vision modules are
  excluded from targets and must remain frozen.
- Adapter profile: rank 8, alpha 16, dropout 0.05, no bias. Target only the
  `q_proj`, `k_proj`, `v_proj`, and `o_proj` `nn.Linear` modules under
  `model.language_model.layers.<index>.self_attn` for those eight configured
  full-attention layers. The derived target list must contain exactly 32 unique
  names and all must exist with the expected class. Any mismatch fails closed.
  The trainer records the instantiated trainable-parameter count; it does not
  hardcode an assumed count. Config dimensions imply 1,310,720 trainable
  parameters for standard q/o and k/v projection shapes at rank 8. Treat that
  arithmetic as a review sanity check only; instantiated module shapes and the
  preflight receipt are authoritative for the exact run.
- Data: only the existing synthetic screen-01 `train.jsonl` (256 rows) and
  `dev.jsonl` (64 rows), balanced across four synthetic families. Manifest,
  train, and dev SHA-256 values are respectively
  `11683129106FF2448930818D6631B8E76201798893E7587ECB0872CBF6BCEBED`,
  `22F45C8B51EF680F9D05E8C42243EBB34E9F596B22D76577C64E371D272A39D2`, and
  `EE0F6DE198CB1D6C6B4EA19A138CCDA9F0D9F1562232430A0A9CE15307760AA7`.
  Each manifest/train/dev file is read once through the confined single-link
  handle path; the trainer parses the same bytes it hashes. The heldout payload
  is never opened. The manifest's heldout metadata may be recorded only as
  metadata. Synthetic labels check plumbing and bounded policy behavior; they
  do not show real workflow quality or generalization.

## Fixed training procedure

- Runtime must be the existing pinned Python 3.13.15, Torch 2.14.0+cu132,
  Transformers 5.17.0, PEFT 0.21.0, and Accelerate 1.15.0. Use the existing
  interpreter `C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe`
  and add-ons at
  `C:\wrench-slm-data\envs\wrench-gateway-lora-screen-01-addons`; do not
  install or download packages. Runtime code verifies versions and module
  origins before loading the model or data.
- Offline only. Set Hugging Face, Torch, CUDA, Triton, XDG, and temporary
  directories beneath the unique job scratch root. The loader uses the pinned
  local snapshot with `local_files_only=True` and `trust_remote_code=False`.
- Load with BF16 on the single pinned RTX 5060 Ti at `cuda:0`. Require BF16
  support, exact GPU UUID/name, and all model parameters on the pinned GPU.
  Enable gradient checkpointing and disable cache. BF16 has not been measured
  on this 4B training workload. A successful static review is not a fit result.
- Optimizer: AdamW, learning rate `2e-4`, weight decay 0, batch size 1,
  gradient accumulation 8, maximum sequence length 512, 3 epochs, exactly 96
  fit optimizer steps, seed `20260927`, gradient norm cap 1.0. Reject rows over
  the sequence cap. The preflight takes the first 8 train rows and performs
  exactly one optimizer step without saving an adapter. Dev loss is diagnostic
  only and is not an activation or selection metric.
- Check finite loss, gradient norm, and trainable parameters at each optimizer
  step. Adapter remains inactive and grants no tool, shell, credential, provider,
  or permission authority. There is no automatic activation or fallback.

## Output identities and admission controls

- Preflight retry job ID:
  `WRENCH-GATEWAY-LORA-SCREEN-03-QWEN35-4B-PREFLIGHT-20260928-03`; logs at
  `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-03-qwen35-4b-preflight-03`;
  scratch under
  `C:\wrench-slm-data\cache\gateway-lora-screen-03-qwen35-4b\<job-id>`.
- Attempt 01 (`...PREFLIGHT-20260928-01`) failed before tokenizer/model load
  because the runner read the tokenizer chat template before initializing the
  tokenizer. Its manifest, resource log, and failure report are preserved.
  Attempt 02 (`...PREFLIGHT-20260928-02`) loaded BF16 weights and matched the
  32 configured attention targets, then exposed token-boundary mismatch: the
  fast tokenizer merges whitespace across the serialized generation-prompt
  boundary. Its manifest, resource log, and failure report are preserved.
  Attempt 03 is distinct and uses full-sequence offset-based assistant-only
  labels, validates in-range nondecreasing token start and end offsets,
  masks any token that begins before the prompt boundary, and rejects
  non-whitespace tokens that cross it. It must not overwrite or reinterpret
  either prior attempt.
- Fit job ID:
  `WRENCH-GATEWAY-LORA-SCREEN-03-QWEN35-4B-FIT-20260928-01`; candidate at
  `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-03-qwen35-4b\fit-01\adapter`;
  logs at
  `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-03-qwen35-4b-fit-01`.
  Each job has a distinct claim and scratch path. The runner refuses any
  existing output or reused claim path.
- Preflight reservation minimum is 250,000,000 bytes; fit minimum is
  2,000,000,000 bytes. Before each job, run the Wrench storage checker, reserve
  the exact job ID, include all assigned roots, and confirm at least 5 GiB of
  destination free space beyond the active reservation. Recheck reservation
  identity and destination headroom at each optimizer boundary. These
  application checks do not replace the storage checker or an OS quota.
- Require at least 10% RAM and VRAM free at all times. The preflight start
  sample must meet both 10% floors. Fit also requires at least 25% free RAM
  before it creates artifacts. A monitor starts before heavyweight imports,
  records RAM, GPU identity/free memory, and scratch bytes every second, and
  interrupts on any 10% floor, scratch cap, or log cap breach. Stop and
  preserve a failed receipt if a breach occurs.
- Scratch caps: 256 MiB preflight, 512 MiB fit. Resource and receipt logs are
  capped at 20 MiB. The candidate adapter is capped at 100 MiB and saved to
  staging, inventoried, then promoted with no-replace rename only after final
  resource checks. No intermediate checkpoints are written. Keep output and
  scratch entirely below `C:\wrench-slm-data`.
- Before model loading, the runner hashes and parses the inventory/config/data
  bytes through approved confined handles. It uses the pinned Windows tree
  helper hash from screen 02 to reject links/reparse points, retain no-write
  model handles during path-based loading, and verify the loaded tree stayed
  unchanged. A cache snapshot that fails the helper's no-follow rules is a
  hard stop; do not weaken the rule or resolve to a different model path.
- Preflight receipt binds schema, job ID, exact trainer/profile, sorted module
  names and count, instantiated trainable count, BF16 precision, model revision,
  inventory/config hashes, protocol/data hashes, tokenizer chat-template hash,
  runtime identity, GPU identity, reservation, and hash-bound resource log.
  Full fit must verify all of those fields and resource minima; it also verifies
  its instantiated module list and trainable count equal the preflight. Release
  the preflight reservation only after that process stops and files are
  accounted for; take a fresh fit reservation before launching fit.

## Required next gates and interpretation

1. Obtain an independent exact-hash source review of the completed trainer and
   this protocol. Confirm the pinned tree helper API, PEFT target-name behavior,
   BF16 architecture/loading, and that no vision parameter can become trainable.
2. Run the distinct one-step preflight only after a fresh storage reservation,
   exact runtime/GPU admission, and at least 10% free RAM/VRAM. Preserve its
   receipt even on failure. Do not launch fit unless the preflight completes
   with finite update and all checks pass.
3. Before fit, require the independent review and exact preflight receipt, a
   fresh fit reservation, at least 25% free RAM, at least 10% free VRAM, and
   5 GiB destination headroom. Fit is exactly 96 updates. On failure, preserve
   evidence, account storage, and do not reuse paths or IDs.
4. After a completed fit, obtain a separate evaluator review before any heldout
   access. Evaluate real, reviewed repository tasks under task-level success,
   cost, and sustained-work accounting. Keep sealed final data sealed until
   the approved one-shot scorer gate.

This screen is a small synthetic controller LoRA feasibility experiment. It
does not establish 95% of a strong model's completed-task value, at most 5%
frontier episodes, at least 95% frontier-token and all-in-cost savings, success
retention, or sustained all-day engineering. Those remain acceptance targets,
not results.
