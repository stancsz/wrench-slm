# Phase 376: learned head direct generation

Status: `DEVELOPMENT_GAPS`

This phase measures the learned lane separately from the deterministic
mechanical worker. It uses the existing rank-16 frozen-backbone output-head
calibration artifact and runs the model's own generation on the 44-row
development split. The sealed final split is not used for training or tuning.

Command:

```powershell
D:\models\wrench-transformers517-py311\Scripts\python.exe tools/evaluate_hf_wrench.py `
  --model D:\models\wrench-v2-head-only-r16-20260921 `
  --cases evals\wrench-expanded-v2\development.jsonl `
  --allowed-root . `
  --output D:\models\wrench-v2-head-only-r16-20260921\development-eval-44-current.json `
  --max-cases 44 `
  --max-new-tokens 128
```

Observed result:

- 44 cases completed on `cuda:0`.
- 21/44 expected outcomes matched.
- 4/44 exact target objects matched.
- 10 verified accepts.
- Median latency was `3,425.487 ms`; p95 was `10,246.146 ms`.
- Evaluation receipt SHA-256: `5ADB099C4C00C469A1F20886C77B566479452536799A8BCFC9E758BA3F6AF043`.
- Calibration receipt SHA-256: `E4B598799FC9ED7CB734A00F66131625AC90FAD4FB3B855E027915E80D926598`.

Conclusion: this learned candidate is not production-capable and is not
promoted into the router. The deterministic model-local mechanical path and
its independent verifier remain the current utility path. Learned routing
stays disabled until a new candidate is evaluated on family-disjoint data with
zero prohibited accepts and acceptable latency.
