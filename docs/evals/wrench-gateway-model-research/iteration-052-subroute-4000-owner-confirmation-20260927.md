# Iteration 052: owner confirms SubRoute at port 4000 (2026-09-27)

## Route confirmation

The owner directed use of the existing `http://127.0.0.1:4000` SubRoute.
Read-only GETs returned HTTP 200 for:

- `/health/liveliness`
- `/api/active-model`
- `/models`

The live active-model response reports alias `openrouter`, mode `force`, and
policy version 4. The model inventory response reports 19 entries. The
repository's OpenCode setup example targets
`http://127.0.0.1:4000/v1` and makes `wrench-subroute/openrouter` selectable;
it does not set that model as default or alter the active user configuration.

The configured alias is force-routed and may reach a remote provider. A local
health check proves only that the gateway answers GETs. The owner has not
provided a numeric aggregate USD cap, and no existing v2 approval was
validated during this iteration. Therefore there was no provider POST,
generation, spend, credential read, or OpenCode configuration change.

## Source-review findings carried forward

Recent independent, read-only reviews provide useful gates, not runtime
evidence:

- The OpenCode synthetic observer has not proved at the actual OpenCode
  transport boundary that its rejection prevents an HTTP request.
- The legacy teacher-capture path still needs a reviewed SubRoute caller seam;
  SubRoute request metadata propagation and returned billing attribution have
  not been verified end to end.
- The Qwen3.5-0.8B inventory is accepted for preparation, but no live inference
  authority or current resource admission was present.
- The fit-03 scorer binding review passed source review only; it does not show
  that a trained adapter learns the policy or improves held-out outcomes.
- Request-capture hardening still leaves completeness caller-supplied and
  does not prove all live attempts were recorded.

The selected route remains `:4000`; the next paid comparison remains closed
until the exact SubRoute caller is bound to a current numeric aggregate cap,
durable reservation/settlement evidence, and provider/model attribution.

## Host and storage gates

At the current sample, free RAM was 3,260.2 / 32,701.8 MiB (9.97%), below the
10% reserve. The GPU is an NVIDIA GeForce RTX 5060 Ti; VRAM free space was not
sampled in this iteration. No tests, OpenCode runtime, inference, training,
benchmark, packaging, or delegated workload ran.

The storage checker includes the external SubRoute checkout and reports
aggregate use below the 50 GB decimal limit. The 30,000-byte documentation
reservation is `WRENCH-SUBROUTE-4000-RECONFIRMATION-20260927-01`; release it
after these files are accounted for.

## Disposition

The endpoint and route alias are confirmed for the experiment. This does not
establish a functioning Wrench LoRA, 95/5 routing, 95% frontier-token savings,
95% all-in cost reduction, or all-day coding ability. The goal remains active.

References: [OpenCode SubRoute setup](../../../examples/opencode_v2_subroute_capture/SUBROUTE_SETUP.md), [tool-profile prototype](../../../examples/opencode_v2_subroute_tool_profiles/README.md).
