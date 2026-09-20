# Phase 105: bounded toolbelt evidence in staged prefill

The staged prefill now invokes the bundled deterministic toolbelt for bounded
code samples. It records AST symbols and dependency evidence in lookup cards,
while skipping full AST parsing for monster references.

## Evidence

- Full suite: `120 passed, 8 warnings`
- Generic 3.33M-token reference:
  - model prefill: 37 estimated tokens
  - ingest: `74.617 ms`
  - selection: `0.135 ms`
- Targeted 3.33M-token lookup for `run_worker`:
  - model prefill: 59 estimated tokens
  - ingest: `72.473 ms`
  - selection: `82.067 ms`
  - target path and symbol are retained in the rendered lookup card
- Public package direct 4M mechanical route:
  - requested payload: 4,000,000 tokens
  - elapsed: `10.479 ms`
  - model calls: `0`
- Canonical 220-case deterministic route replay:
  - mechanical routes: `200/220`
  - outcome matches: `200/220`
  - prohibited accepts: `0`
  - eligible weighted frontier-token mass: `78.9999%`

The remaining 20 historical eligible rows are patch-draft prompts that name a
file but provide no requested change or diff. The router leaves them for the
model-backed path instead of fabricating a patch.

The measurements establish a fast deterministic staging path. They do not
establish native dense 4M attention quality or MiniMax parity.

The synchronized public package revision is
`6b404564d087d93ceb17904c06b9572bbe1af831`; both the root prefill module and
`wrench_runtime/prefill.py` contain the bounded toolbelt path.
