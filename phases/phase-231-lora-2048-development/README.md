# Phase 231: rank-8 LoRA 2,048-step development rerun

Status: `DEVELOPMENT_DIAGNOSTIC_ONLY`

The existing rank-8 output-head calibration was repeated for 2,048 steps on
the same 132-row calibration split used by Phase 222. The sealed final split
was not read. The run used the CUDA-enabled FreeToken Python environment,
Torch 2.11.0+cu130, and the same Qwen3.6 BF16 source candidate.

The resulting checkpoint was evaluated with the same 44-row development
split and the mechanical shortcut disabled:

- outcome matches: 17/44;
- exact target matches: 8/44;
- verified accepts: 22/44;
- median generation latency: 6,105.343 ms;
- p95 generation latency: 11,713.913 ms;
- device: `cuda:0`.

This regresses the Phase 222 rank-8, 1,024-step result of 30/44 outcome
matches and 16/44 exact targets. It is not promoted. The deterministic
mechanical route remains the production-value owner for the routine portfolio,
while learned generation remains a fallback diagnostic.

The first attempted command used the system Python 3.14 environment and
failed before loading weights because its Transformers 4.57.1 installation
does not recognize `qwen3_5_moe`. The successful rerun used
`C:\Users\stanc\AppData\Local\FreeToken\venv\Scripts\python.exe`.

Evidence: `evaluation.json`.
