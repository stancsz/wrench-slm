# Phase 171: bounded multi-file reference patch retrieval

Date: 2026-09-20

## Purpose

Improve the MapReduce-first path for long developer-tool payloads that contain
an old, exact unified diff followed by a newer review-only intent. The route may
recover up to three explicitly named relative files. It never invents missing
hunks, rejects traversal or absolute paths, bounds each diff and the combined
diff to 128 KiB, and still crosses the normal verifier and embedded TTC gate.

## Evidence

- Targeted tests: `37 passed` for mechanical routing, embedded worker, and
  prefill coverage.
- Full regression: `155 passed, 14 warnings in 33.92s`.
- A temporary allowed-root fixture contained `README.md` and
  `config/policy.json`, each with an old one-line value.
- The request contained a synthetic 4,000,253-character stale prefix, an exact
  two-file unified diff, and a current review-only intent naming both files.
- Three end-to-end worker runs measured `24.447 ms`, `22.102 ms`, and
  `22.715 ms`.
- All runs were `accepted`, used the `embedded-mechanical` backend, used the
  mechanical fast path, made zero model calls, returned both exact files, and
  reported `applied: false`. The fixture files remained unchanged.
- TTC receipt passed schema, authority, evidence, consistency, AST, diff,
  blind-critic, and final-gate checks in the direct verification run.

## Boundary

This is evidence for fast MapReduce plus deterministic retrieval and bounded
multi-pass verification. The payload is a large character payload, not proof of
dense native 4M attention. It does not establish MiniMax matched-workflow
parity, the 90 percent weighted coverage gate, or the 95 percent net savings
gate. Public package publication is a separate decision after source and
portable-runtime hashes are refreshed.
