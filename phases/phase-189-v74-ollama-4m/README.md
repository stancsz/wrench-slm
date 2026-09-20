# Phase 189: v74 Ollama-shaped 4M smoke

Date: 2026-09-20

A fresh v74 portable package was started from its model directory and tested
through the Ollama-shaped `/api/chat` surface with `options.num_ctx=4000000`.
The request contained exactly 4,000,000 estimated raw input tokens.

- HTTP status: `200`;
- payload characters: `8,000,024`;
- `prompt_eval_count`: `4,000,000`;
- wall latency: `51.659 ms`;
- embedded mechanical backend;
- zero model calls;
- zero model prompt tokens;
- 4,000,000 input tokens not sent to a model;
- local route time: `9.182 ms`;
- TTC and verifier: passed.

This is direct model-directory intake plus embedded MapReduce on the current
v74 package. It is not dense native 4M attention evidence.

