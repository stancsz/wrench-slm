# Phase 227: real worker CUDA generation smoke

The fused development-only rank-8 LoRA candidate was loaded through the same
`WrenchWorker.from_pretrained(load_model=True)` path used by the portable
worker. The mechanical shortcut was explicitly disabled so the Transformers
model had to generate the proposal.

Result for canonical development case `eval59_read_file_06_00`:

- verified status: accepted
- exact target match: yes
- outcome match: yes
- model calls: 1
- reported model device: `cuda:0`
- backend: `transformers`

The earlier standalone HF evaluator measured 4,493.678 ms for the same
development-only generation smoke. The checkpoint is a temporary local fused
LoRA artifact and is not promoted as the selected or public model. This is a
device-placement and real-generation smoke, not a family-disjoint quality
benchmark, MiniMax parity result, or production approval.

The worker now defaults to CUDA when available, while
`WRENCH_MODEL_DEVICE=cpu` or an explicit device can override placement. A
pre-existing Accelerate device map remains authoritative.
