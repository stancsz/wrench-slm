# Iteration 004: SubRoute read-only preflight

Date: 2026-09-27 (America/Edmonton)

Status: **CONNECTIVITY VERIFIED; GENERATION NOT AUTHORIZED OR ATTEMPTED**

## Owner direction

The owner reconfirmed that the evaluation should use the existing SubRoute at
`http://127.0.0.1:4000`. The saved same-day route snapshot from the prior
read-only check recorded `active_model=openrouter`, force mode, and policy
version 4. The previously audited model mapping is OpenRouter/MiniMax M3. This
does not pin the individual inference provider selected by OpenRouter for a
future request.

## Read-only checks

| Check | Result |
|---|---|
| `GET /health/liveliness` | HTTP 200, `I'm alive!` |
| `GET /models` | 19 configured aliases, including `openrouter` and `minimax` |
| `GET /model/info` safe-field projection | `openrouter` maps to `openrouter/minimax/minimax-m3`, mode `chat`, configured input cost `$0.30/M`, output cost `$1.20/M`; model-info ID `7ec0fcd796f4452d965d34f010bc30802a1dd926dcb39eabd474cd913172a74e`; provider is unset |
| Host sample | RTX 5060 Ti: 15,203 / 16,311 MiB VRAM free; 18.35% RAM free, below the 25% fit-start gate |
| Chat/completion generation | Not called |
| Provider spend or usage | None |

The live model-info projection now confirms the forced model target and its
configured pricing. The `provider` field is null, so the actual inference
provider is not pinned by this route and must be read from a verifiable
per-request receipt. The separate `minimax` alias maps to `minimax/MiniMax-M3`
at the same configured rates, but the active force route remains `openrouter`.
The aliases alone do not prove a billed cost.

## Evaluation safety finding

`tools/run_diagnostic_worker_arms.py` is not ready to make a spend-capped
comparison. Its defaults point to the local SubRoute endpoint and `minimax`
alias, with `max_tokens=768`, `teacher_workers=4`, and a 10-second timeout.
The runner has no aggregate USD limit or input-token ceiling. Its `_cost_usd`
helper returns `0.0` when the response lacks billed-cost fields. A generation
run must wait until the caller reserves worst-case cost before each request,
stops before the approved total is exceeded, and fails closed when the
provider/model, usage, or billed-cost receipt is missing. Preserve force mode.

## Product-evidence limits

This is a connectivity and protocol safety record. It does not measure
MiniMax quality, route accuracy, task completion, LoRA utility, frontier-token
savings, dollar savings, or sustained engineering. The existing 128-case
synthetic task distribution has 104 `LOCAL` labels (81.25%), so it cannot
establish the 95% local-completion target even if every case is classified
correctly. A powered, rights-cleared, outcome-verified task set and paired
usage receipts remain necessary.

The owner's numeric aggregate USD cap is still pending. Continue offline work
without generation calls. Do not modify the gateway's route or force policy to
increase access.
