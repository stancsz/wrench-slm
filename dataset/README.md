# External tool-call data excluded from the Wrench corpus

The three public tool-call bundles previously stored here are excluded from
Wrench training. Their task mix does not match Wrench's six-action proposal
contract, and source licensing is still pending. They have been moved out of
the active dataset directory to:

`D:/wrench-slm-data/quarantine/dataset-general-tool-call-2026-09-23/`

The file-by-file sample counts, byte sizes, SHA-256 hashes, and disposition
are recorded in
[`quarantine-manifest.json`](../phases/phase-447-wrench-training-data-corpus/quarantine-manifest.json).
The machine-readable source manifest below is marked as excluded. Do not load
the archived data into the 20,000-row training corpus.

| Source bundle | Rows | Disposition |
| --- | ---: | --- |
| pyromind short tool-call subset | 2,000 | Excluded. Sampled topics and tools include finance calls outside Wrench's allowlist. |
| pyromind long tool-call subset | 1,000 | Excluded. Broad web research and multi-step workflows are outside the bounded worker contract. |
| Glaive function-calling subset | 2,000 | Excluded. Generic function schemas do not teach Wrench's typed proposal and abstention protocol. |

This data may be reconsidered only after both task-fit and license review pass.
The training target and quality gates are documented in
[`Phase 447`](../phases/phase-447-wrench-training-data-corpus/README.md).
