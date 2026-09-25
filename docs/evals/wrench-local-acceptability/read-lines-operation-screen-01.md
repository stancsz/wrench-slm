# Read-lines operation screen 01: stopped before measurement

Status: invalid harness launch; zero cases executed.
Date: 2026-09-25 (America/Edmonton)
Preregistered job: `LOCAL-READLINES-ACCEPT-20260925-01`
Repository revision: `43a160a2411c3511a5c41a24fe7a03717169d50e`

The frozen command stopped during Python module import:

```text
ModuleNotFoundError: No module named 'wrench_harness'
```

The direct `python tools/...` launcher did not place the repository's `src/`
directory on `sys.path`. No fixture root, case execution, core executor call,
or measurement receipt was produced. This attempt has no route, executor,
quality, utility, or token-savings result and must not be counted. Its 5 MB
storage reservation was released after confirming no receipt existed.

The repair inserts the local `src/` directory explicitly before package imports.
It is frozen under the separate [protocol 02](read-lines-operation-protocol-02.md)
and job identity; protocol 01 will not be retried.
