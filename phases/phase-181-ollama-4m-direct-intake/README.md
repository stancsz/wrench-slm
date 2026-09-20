# Phase 181: Ollama-shaped direct 4M intake

Date: 2026-09-20

## Receipt

A fresh v73-style portable package server was started from the downloaded
model directory with `--mechanical-only`. The request used the Ollama-shaped
`/api/chat` endpoint, not the OpenAI-compatible endpoint:

- model: `wrench-v73-ollama`;
- `options.num_ctx`: `4,000,000`;
- raw input token estimate: exactly `4,000,000`;
- payload characters: `8,000,024`;
- wire bytes: `8,000,151`;
- HTTP status: `200`;
- wall latency: `80.412 ms`;
- endpoint `prompt_eval_count`: `4,000,000`;
- response backend: `embedded-mechanical`;
- mechanical fast path: `true`;
- model calls: `0`;
- model prompt tokens: `0`;
- model completion tokens: `0`;
- input tokens not sent to a model: `4,000,000`;
- local server route time: `10.158 ms`;
- declared context tokens: `4,000,000`;
- TTC and verifier checks: all passed.

The returned proposal was the bounded read of `README.md` with a 4096-byte
limit. The raw request was accepted by the downloaded model directory before
the embedded reducer selected the mechanical path.

## Boundary

This proves direct 4M logical intake through the Ollama-shaped local model
surface plus embedded MapReduce. It does not prove dense native 4M attention:
the four million tokens were intentionally not sent through dense model
prefill. Native attention remains a separate comparison lane.

