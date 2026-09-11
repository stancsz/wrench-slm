# Wrench-SLM architecture

Updated: 2026-09-11

Wrench-SLM is a research repository for small models and deterministic policy
that propose structured tool calls for routine developer work. The maintained
artifact is Wrench-Pro V21, a PEFT LoRA adapter for the pinned
`Qwen/Qwen2.5-0.5B-Instruct` base model. The repository also contains an
active, narrower selective-offload experiment. That experiment is not part of
the V21 release contract and is not production-ready by presence alone.

## System boundary

```text
request + public context + declared tools
                  |
                  v
       policy / model proposal
                  |
                  v
         structural validation
                  |
          +-------+--------+
          |                |
     safe local read     fallback
          |                |
          v                v
  runtime observation   stronger model
          |
          v
   observation verifier
          |
     local result or fallback
```

The local path proposes and validates an action. It does not grant arbitrary
shell access, deployment authority, or permission to execute writes. A local
result is allowed only when the request, action, visible resource boundary,
tool observation, and verifier agree. Any uncertainty falls back with the
original request and relevant observation.

## Main layers

| Layer | Location | Responsibility |
| --- | --- | --- |
| Product direction | `NORTHSTAR.md` | Durable user outcome and decision principles |
| Active execution contract | `goals/active/*/GOAL.md` and compatibility `goal.md` | Acceptance criteria, constraints, progress, evidence, and blockers |
| Release adapter runtime | `wrench/pilot_inference.py`, `wrench/protocol.py`, `wrench/weight_inference.py` | Load V21, format prompts, predict, parse, and validate structured calls |
| Experimental local policy | `wrench/selective_policy.py`, `wrench/selective_runtime.py` | Public-context selection, safe action validation, observation verification, fallback |
| Pilot workflow | `wrench/pilot_workflow.py`, `wrench/selective_eval.py` | Execute bounded local/cloud arms and record episode accounting |
| Training | `wrench/sft.py`, `wrench/training.py`, `wrench/pure_training.py` | LoRA and experimental native-model training paths |
| Data contracts | `wrench/dataset.py`, `wrench/release_data.py`, `wrench/pilot_tasks*.py` | Prompt formatting, split construction, and task provenance |
| Evaluation | `wrench/release_eval.py`, `wrench/evaluate.py`, `wrench/selective_eval.py` | Exact predictions, outcomes, gates, and uncertainty summaries |
| Reproducibility | `scripts/fetch_assets.py`, `scripts/verify_assets.py`, `releases/v21/` | Restore and verify release packages and checksums |
| Public documentation | `README.md`, `docs/`, `releases/v21/` | User-facing scope, status, release cards, and evidence links |

## Prediction and validation

The release format is a JSON object representing a tool call or a
`ROUTER_FALLBACK` decision. `wrench/protocol.py` owns parsing, canonical JSON,
target extraction, and exact-match evaluation. `wrench/policy.py` provides a
baseline predictor and prediction loader. `wrench/pilot_inference.py` adapts a
Transformers/PEFT model to the pilot record format and validates its output.

The repository contains FSM and tokenizer-grammar implementations in
`wrench/fsm.py` and `wrench/tokenizer_fsm.py`. Their presence does not mean
that the packaged V21 runtime uses grammar-constrained decoding. The published
V21 evaluation generates a completion and validates it afterward.

## Selective offload boundary

1. A selector sees only public request context, declared tools, policy
   configuration, and information produced by a real tool call.
2. An action must name an allowed tool, provide complete arguments, stay within
   visible paths and bounds, and align with the request.
3. The executor runs only the narrow read-only operation contract.
4. The runtime verifier checks the observed result's declared shape. Offline
   gold is scoring data after routing, never a routing input.
5. Invalid, irrelevant, timed-out, failed, malformed, or boundary-changing
   episodes fall back.

`wrench/pilot_environment.py` and `wrench/pilot_workflow.py` support fixture
execution and episode accounting. They are test infrastructure, not proof of
live production traffic. The trusted-scenario intake and readiness gate in the
current worktree deliberately stop before replay when prompt/context fields,
price data, or trustworthy duration units are missing.

## Data and artifact boundaries

- Maintained release inputs live under `data/releases/`.
- Historical baselines live under `data/archive/baseline/`.
- Pilot and stress populations live under `data/pilots/` and remain separate
  from release data.
- The V21 package, evidence, cards, and checksums live under `releases/v21/`.
- Weights, checkpoints, restored packages, and local receipts belong under
  ignored `artifacts/` paths unless a release card explicitly says otherwise.
- Generated fixtures and teacher-distilled rows must not be labeled as
  production traffic.

## Operational invariants

- A LoRA adapter is not standalone model weights. The pinned base revision is
  required.
- A release score applies to the named authored suite and environment only.
- A release-ready package is not the same claim as production readiness.
- `0.0.0.0` is a bind address. Local probes use `127.0.0.1` or `localhost`.
- No provider-value claim is valid without complete local, fallback, provider
  token, cost, latency, and outcome accounting.
- Provider execution requires explicit attempt and token ceilings plus explicit
  operator authorization.

## Where to change what

- Change durable product intent in `NORTHSTAR.md`.
- Change architecture or invariants here.
- Change the active acceptance contract only in the active `GOAL.md` as the
  Steward, never to make an implementation pass more easily.
- Change release artifact claims in `releases/v21/` and the linked handoff.
- Change public site content in `docs/` only when the corresponding evidence
  and status source are understood.
- Keep historical documents in `docs/reference/archive/` or clearly label them
  as historical; do not silently refresh their old denominators.
