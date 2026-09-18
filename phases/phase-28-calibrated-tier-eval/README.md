# Phase 28: calibrated tier evaluation

This phase evaluates experimentally calibrated 8-expert and 16-expert Wrench
checkpoints against an unseen synthetic holdout. The training rows are
generated outside Git under `D:\models\wrench-calibration-v2`; only hashes and
verifier receipts are retained here. This is development evidence, not final
portfolio approval or production quality evidence.

The latest 16-expert calibration was quantized with the full chat-template
calibration path, stripped to text-only, and packed to FreeToken FTW. The
corrected holdout fixture is under `D:\models\wrench-calibration-v3b` with
SHA-256 `628b9633352e3d4457a3e3c511d6c299bda9b833634eeba46d56eba7285940dd`.
The correction raises the two file-size limits above the current repository
file sizes so the verifier does not manufacture false abstentions.

Current 16E evidence:

- BF16 calibrated checkpoint: 9/14 exact verifier outcomes on the corrected
  holdout (`score-16-calibrated-v1b-corrected.json`).
- NVFP4 FTW checkpoint: 7/14 exact verifier outcomes on the same holdout
  (`score-16-calibrated-v1b-ftw-corrected.json`).
- Packed FTW model-weight bytes: 3,975,827,456 bytes, about 3.70 GiB. The
  complete text-only directory is 3,996,022,974 bytes, about 3.72 GiB.

The compact 8E calibrated FTW artifact remains 3,406,319,616 packed weight
bytes, about 3.17 GiB, with a complete directory size of 3,426,514,763 bytes,
about 3.19 GiB. On the corrected holdout it scores 9/14 in BF16 and 7/14
after NVFP4 packing, matching the 16E tier on these provisional measures. No
score here is a production-quality claim.
