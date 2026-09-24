# Model story editorial evidence

Reviewed 2026-09-22 for the bilingual `model-story.html` pages. This document
is repository-only and is not copied to the static publish directory.

- Official upstream model card: https://huggingface.co/Qwen/Qwen3.6-35B-A3B/blob/main/README.md
- Source lineage and acquisition: `phases/phase-22-source-inspection/README.md`
  and `checkpoint-facts.json`; revision `995ad96eacd98c81ed38be0c5b274b04031597b0`.
- Initial 0..7 selection and 3,881,244,016 parameters:
  `phases/phase-24-structural-prune-baseline/README.md` and `runtime-smoke.json`.
- Router telemetry, selection, candidate sizes, historical NVFP4 exports:
  `phases/phase-25-router-profiling/README.md`, `selection-8.json`,
  `tools/build_router_selection.py`, and `tools/prune_qwen_experts.py`.
- Attention LoRA configuration and failed safety comparison:
  `phases/phase-130-balanced-attn-lora/README.md`, `lora-receipt.json`,
  and `full-220-direct.json`. The 62/220 baseline and 138/220 outcome matches
  are historical cases, not fresh held-out evidence or current production results.
- Token boundary and target-only labels:
  `phases/phase-222-lora-training-audit/README.md` and
  `tools/calibrate_qwen_router.py` (`_example` and `calibrate`).
- JSON syntax versus semantic correctness:
  `phases/phase-353-guided-json-lora-development/README.md`.
- Historical model-story scope: `docs/misc/v1/WRENCH_MODEL_TOOLBELT.md` and the archived v1 direction. Current scope is in `GOAL.md` and `docs/northstar/V2_ARCHITECTURE.md`.

Do not combine historical quantization and adapter experiments into one
promoted artifact. File size is not runtime VRAM; expert retention is not
per-token activation count; training loss is not matched workflow utility.
This content update does not authorize training, inference, or publication.
