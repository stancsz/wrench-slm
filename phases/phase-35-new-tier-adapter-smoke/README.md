# Phase 35: new-tier adapter smoke

Phase 35 sends one request through the new 8E schema-guided NVFP4 artifact,
FreeToken, the localhost adapter, and the independent verifier. The request is
the trained `README.md` read shape from the calibration portfolio. This tests
runtime wiring and safety boundaries only; it is not a quality benchmark.

The adjacent legacy-prompt probe abstained on a missing path. The stricter
schema-guided adapter probe is recorded separately and also abstained because
the returned content was not strict JSON at the adapter boundary. This keeps
prompt-format behavior and path generalization visible instead of treating an
HTTP 200 or a loaded model as a task-success claim.
