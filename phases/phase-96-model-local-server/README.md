# Phase 96: model-local 4M endpoint

This phase moves the practical long-context serving entrypoint into the
downloaded package itself. The package now contains `wrench_server.py` and
`wrench_runtime/server.py`, a small OpenAI-compatible endpoint with
`/v1/chat/completions`, `/v1/models`, and `/health`.

The endpoint receives the complete raw request before invoking the bundled
worker. Mechanical requests stay on the embedded route with zero model calls;
ambiguous requests can use the normal worker model path when started without
`--mechanical-only`. This keeps the model-local serving contract separate from
the repository harness.

## Package evidence

- v23 and v24 structural package validation: `PASS_STRUCTURAL_PACKAGE`.
- 64K raw estimated input: HTTP 200, correct `read_file`, zero model calls,
  `35.488 ms` request latency.
- 2M raw estimated input: HTTP 200, correct `read_file`, zero model calls,
  `76.024 ms` request latency.
- 4M raw estimated input: HTTP 200, reported `4,000,010` input tokens,
  correct `read_file`, zero model calls, `138.212 ms` request latency on the
  v23 probe and `152.254 ms` on the v24 refresh probe.

The 4M result is package-local deterministic routing evidence. It is not a
claim that dense native attention was computed over every 4M token, nor a claim
of MiniMax parity or production readiness. Native dense attention and learned
retrieval quality remain separate gates.

The public Hub package was refreshed as v24 at revision
`2ed0d0dcde998258d501190bba52ff9d8072bfb0`. The Safetensors weights remain
unchanged. Remote hashes for the bundled server and worker match the v24 local
package.
