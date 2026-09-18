# Phase 44: compact-tier runtime prerequisite check

The 8E holdout rerun was attempted against the verified compact artifact, but
the local FreeToken runtime was not installed in the available environment.
The direct launch lacked the `freetoken` package. The repository environment
bootstrap then failed while building the editable package because `CUDA_HOME`
was not set. The Python interpreter available to the shell only exposes a CPU
PyTorch install.

No 8E weights were loaded, no request was served, and no quality or latency
result was recorded. Existing artifact-size and prior runtime receipts remain
valid; the compact-tier adaptive holdout is deferred until the CUDA runtime
environment is restored.
