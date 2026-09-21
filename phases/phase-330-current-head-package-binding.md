# Phase 330: Exact current-head package binding

Status: `PASS_STRUCTURAL_PACKAGE`, with package-local route and client smoke
passing.

The portable package was rematerialized from the actual current repository
HEAD `bbc680f617884d5e658172a61461335e2368180a` into:

```text
D:\models\_wrench-release-candidate-bbc680f
```

The package contains the same 3,881,244,016-parameter NVFP4 artifact and the
runtime files from current HEAD. Structural validation passed with no errors.

The exact package then passed:

- model-local 4M route: `4,000,000` requested tokens, `27.693 ms`, zero model
  calls;
- OpenCode: exit `0`, structured read observed;
- DeepSeek Harness: exit `0`, structured read observed;
- Claude Code: exit `0`, structured read result observed;
- zero model calls and no mutation claim in the mechanical client traces.

Evidence:

- `phase-330-current-head-package-binding-validation.json`
- `phase-330-current-head-package-4m-route.json`
- `phase-330-current-head-client-smoke/receipt.json`
- `phase-330-current-head-client-smoke/wrench-client.trace.jsonl`
- `phase-330-current-head-client-smoke/claude.trace.jsonl`

This remains an Experimental Preview package binding. It does not establish
standard Transformers full-weight loading, dense-native 4M decoder quality,
learned MiniMax parity, independent RTX 5060 Ti verification, or production
enablement.
