# Iteration 043: use the existing SubRoute at port 4000 (2026-09-27)

## Owner direction

The owner directed use of the existing SubRoute setup at
`http://127.0.0.1:4000`. The repository already has a selectable OpenCode
v2.0.12 provider profile, `wrench-subroute/openrouter`, pointed at
`http://127.0.0.1:4000/v1`; it is intentionally not the default model. The
profile is the designated comparison route for this experiment.

## Read-only route check

Fresh GETs to `/health/liveliness`, `/api/active-model`, and `/models` returned
HTTP 200. The active-model response was `openrouter`, mode `force`, policy
version 4. The model inventory had 19 entries. This confirms the route is
reachable and the forced alias is selected. It does not establish which
upstream deployment handles a generation, tool-call compatibility, or its
billed cost.

No POST or provider generation was sent. The numeric campaign-wide USD cap is
still unspecified, so the existing caller's approval and billing-receipt gate
was not opened. The SubRoute setup stays selected in experiment configuration;
no active OpenCode configuration or gateway routing policy was changed.

## Execution gate and outcome

Free system RAM was 3,256.0/32,701.8 MiB (9.96%), below the required 10%
runtime floor. GPU free memory was 15,242/16,311 MiB (93.44%). No tests,
OpenCode runtime preflight, inference, training, benchmark, or delegation ran.
The model and product-effectiveness claims remain unproven.

The storage checker, including the external SubRoute checkout, reported
`WITHIN_LIMIT`: 10,992,472,274 actual bytes plus 8,103,000 bytes in prior
reservations before this report's 200,000-byte reservation. C: had 132.17 GiB
free. The reservation must be released after this report and goal update are
accounted.

## Next step

Use this route for the future paired frontier arm through the campaign-wide
caller. A paid request still requires the numeric aggregate cap, current
hash-bound approval, and validated durable usage and bill receipt. Under the
current RAM reading, continue only with offline source or protocol work.
