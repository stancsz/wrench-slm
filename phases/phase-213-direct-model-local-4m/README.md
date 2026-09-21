# Phase 213: Direct model-local 4M intake

Date: 2026-09-20

The v86 package was started only from its own `run_wrench.ps1` with no
repository `PYTHONPATH` and no external gateway. A PowerShell client sent a
single Ollama-shaped `/api/chat` request containing an old reference message
and a current mechanical intent.

Receipt summary:

- estimated raw input: `3,998,332` tokens;
- raw input characters: `7,998,072`;
- request body: `7,998,214` UTF-8 bytes;
- complete local HTTP round trip: `72.288 ms`;
- Wrench worker elapsed: `1.446 ms`;
- model calls: `0`;
- result: accepted `read_file` proposal for `wrench-package.json` with a
  `4096` byte bound;
- verifier schema, authority, evidence, consistency, blind critic, and final
  gate: all passed;
- raw input was acknowledged as `options.num_ctx=4000000`.

This is direct raw-context intake at the model-local package surface and a
real fast mechanical completion. It is not dense native attention over all
4M tokens, and it does not repair the separate stock Ollama native-generation
quality failure.

