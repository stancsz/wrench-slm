# Phase 442: MiniMax and OpenRouter credential capability check

Date: 2026-09-22

## Question and boundary

Check whether the existing MiniMax and OpenRouter credentials are configured
and whether the active gateway exposes the intended MiniMax routes. This was a
read-only capability check. It did not issue a model completion, change the
gateway, alter the Wrench Q4 contract, or run a canary.

## Findings

- `MINIMAX_API_KEY` and `OPENROUTER_API_KEY` were present in the current and
  user environment scopes and in the running `unified-llm-gateway` container.
  Secret values were not displayed or saved.
- Port 4000's live `/model/info` response reported `openrouter` mapped to
  `openrouter/minimax/minimax-m3` and `minimax` mapped to
  `minimax/MiniMax-M3`. The running container mounts the gateway's
  `config/litellm.yaml` at `/app/config`.
- Using the running container's configured credentials, the read-only
  OpenRouter `GET /api/v1/credits` returned expected account metadata, and the
  MiniMax `GET /v1/token_plan/remains` returned plan metadata. Both providers
  accepted their respective credentials for these metadata reads.
- No model completion or paid canary was sent. Available credit, provider
  hard-cap enforcement, and actual MiniMax inference/model entitlement were
  not tested.

## Q4 scope and next decision

The active Wrench parent contract still authorizes one paired canary on the
GPT-6 route at `http://localhost:4000/v1`, with a `$500` maximum and one
repetition. This check does not authorize replacing that model/provider with
MiniMax. Choosing either MiniMax route for the canary requires an explicit Q4
scope decision and a child contract bound to the selected alias, expected
provider model, accounting source, and spend controls. The pending GPT-6 alias
choice remains separate.

## Rollback and identities

No repository, gateway, or runtime configuration changed, so no rollback was
needed. No credentials were written to the repository or receipt.

- Active gateway container ID prefix: `95c3f526b63a`.
- Gateway model configuration SHA-256:
  `F2235AFD7F6F615EA58EFB52E7A92ED539523563171111001C2385A557C8EE4D`.
- Wrench Q4 parent SHA-256, unchanged by this phase:
  `CF255E5C73AE9DF58C5FD29D879BD7AAA9A2972245EFB61A3C4C597F65D9B4B5`.
