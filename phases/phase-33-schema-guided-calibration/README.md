# Phase 33: schema-guided calibration

Phase 33 tests a targeted calibration change. The calibration and evaluation
rows use an explicit action-to-field schema in the system instruction, while
the independent verifier remains unchanged and strict. This addresses the
previous failure pattern of duplicated JSON keys, wrong field names, and
malformed action objects.

The new lineage is outside Git:

- Training: `D:\models\wrench-calibration-v6\train.jsonl`
- Training SHA-256: `0a075ca4810a01c9ba1a7d0739a33e7df2b675b741aa4d41cb8358f6d3234ef9`
- Holdout SHA-256: `18efa3688dd784902f1466a524fbe027f4ffa2fe807e85053e8c16cd5f9474d7`
- Unseen SHA-256: `7ca0ea61fd433bf2dc97ab8f87345de99cd1044e55b96a8c97fa41c2d8f29a05`
- Both tiers: 500 steps, rank 8, alpha 16, learning rate `5e-4`, seed 17

Results:

| Tier | Packed size | Holdout verifier | Holdout exact | Unseen verifier | Unseen exact |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8E FTW | 3,423,498,137 bytes, 3.188 GiB | 6/14 | 5/14 | 12/28 | 8/28 |
| 16E FTW | 3,991,755,140 bytes, 3.718 GiB | 8/14 | 4/14 | 12/28 | 8/28 |

The new 8E BF16 checkpoint scored 9/14 verifier outcomes and 8/14 exact
proposals on the holdout before packing. Packing reduced that to 6/14 and
5/14. The 16E packed tier is slightly stronger on holdout verifier outcomes,
while both tiers tie on the explicit-schema unseen fixture.

This is a development comparison, not a production-quality claim. The
portfolio is still pending human approval, real workflow traces, uncertainty
analysis, and no-mutation release gates.

