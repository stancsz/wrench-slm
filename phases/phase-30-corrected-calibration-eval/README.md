# Phase 30: corrected calibration lineage and packed evaluation

Phase 30 retrains both tiers from a corrected calibration corpus whose accepted
`read_file` limits exceed the current repository file sizes. The corpus is
written byte-for-byte with a stable SHA-256:

- Training: `D:\models\wrench-calibration-v5\train.jsonl`
- Training SHA-256: `9020d5cfb9ad7ede43e5880db1d1200d46f6e20ddc1c52610f4fdd51d325d49c`
- Corrected 14-case holdout SHA-256:
  `628b9633352e3d4457a3e3c511d6c299bda9b833634eeba46d56eba7285940dd`
- Corrected 28-case unseen evaluation SHA-256:
  `56bb3d875d8b94fff1b5b43c289a2c009830dc9a1a081b52d74e16430254c1a2`

Both retrained checkpoints used 500 steps, rank-8 output adapters, learning
rate `5e-4`, and the same calibration bytes before full-chat-template NVFP4
quantization.

Packed results:

- 8E: 3,426,514,765 directory bytes, 3,406,319,616 packed weight bytes.
  The 14-case holdout scored 5/14 verifier outcomes and 3/14 exact proposals;
  the 28-case unseen evaluation scored 9/28 verifier outcomes and 9/28 exact
  proposals.
- 16E: 3,996,022,971 directory bytes, 3,975,827,456 packed weight bytes.
  The 14-case holdout scored 7/14 verifier outcomes and 5/14 exact proposals;
  the 28-case unseen evaluation scored 10/28 verifier outcomes and 7/28 exact
  proposals.

These are still development-only synthetic receipts. The corrected data
lineage improves the compact tier's proposal fidelity, but neither tier has
passed the real-workflow usefulness, human-approval, or production gates.
