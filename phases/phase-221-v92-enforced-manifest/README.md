# Phase 221: v92 package manifest enforcement

Date: 2026-09-20

The portable materializer now records the hard raw-input admission contract in
both `wrench-runtime.json` and `wrench-package.json`:

- `raw_input_limit_enforced: true`;
- `over_limit_behavior: HTTP_400_fail_closed`.

The v92 package passed structural validation and its own package-local server
reported `context_length=4,000,000`, `parameter_size=3.88B`, and accepted a
3,998,332-token direct `/api/chat` request in 74.265 ms with zero model calls.
The response carried the `mechanical_fast_pruner_cherrypicker` and
hash-bound receipt.

This makes the portable artifact's metadata and runtime admission behavior
agree. It remains hybrid evidence, not stock Ollama native generation or
dense native 4M attention quality.
