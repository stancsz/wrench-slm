# OpenCode request-lowering source audit

Date: 2026-09-24  
Scope: tagged OpenCode `v2.0.15` source trace and explicit E0 prompt-count research pins

## Decision

Use OpenCode `v2.0.15` as the first-client target, restricted for
characterization to the OpenAI Responses protocol and model
`gpt-4.1-2025-04-14`. The source-pinned **provider-body serializer** candidate
is `@opencode/ai@2.0.15`: `LLMClient.compile` calls the selected route's
`RouteBody.from`, which for this protocol is `OpenAIResponses.fromRequest`,
then validates the body schema before preparing the selected transport. The
separate route transport and endpoint must also be pinned in any later
runtime-matched gate. The pinned local text tokenizer candidate is
`tiktoken==0.9.0` with an explicit `o200k_base` encoding, not runtime model
auto-detection. The encoding data file is hash-pinned by that release to
`446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d`.

These pins make future offline characterization reproducible. The body
serializer pin does not yet include the selected route transport, endpoint,
or runtime model resolution. The text tokenizer pin does not provide an exact
Responses input-token count. OpenAI documents that local
tokenizers cover plain text while tools, images, files, and request structure
add tokens that the remote input-token count endpoint accounts for. That
endpoint accepts the Responses input format and returns the model input count.
Using it would transmit the final request data to OpenAI and needs separate
provider-data and spending approval. No request was sent.

## Tagged field flow

OpenCode's `SessionHooks.context` carries `sessionID`, `system`, `messages`,
`model`, `agent`, `options`, and `tools`. The hook sits before OpenCode forms
its canonical `LLMRequest`:

1. The core starts from resolved session/model data, the current transcript,
   system parts, and tool definitions, then calls the context hook.
2. It maps returned tool entries back to executable definitions by object
   identity or original name. Entries that match neither are dropped. Tool
   JSON schemas are still request data, not authorization.
3. It separates recognized generation options from provider-specific options.
4. It applies model-capability media handling and image-size reduction to
   messages, then constructs `LLMRequest` from the resolved model object and
   the hook-shaped system, messages, tools, and options.
5. Model request hooks can change the base URL and headers. The selected route
   then chooses protocol lowering and HTTP or WebSocket transport.
6. The pinned OpenAI Responses lowerer maps conversation, generation options,
   tools, and tool choice into the provider request body.

The context projection therefore records upstream hook values but cannot
reconstruct the final body alone. It lacks the resolved executable route,
model capability metadata, tool reconciliation result, any post-context model
request hook change, and transport choice. The existing Wrench prompt compiler
uses caller-supplied serializer and tokenizer callbacks, so neither callback
identity is enforced by the OpenCode adapter.

## What remains open

- The chosen body-serializer path is a candidate pin, not an installed or
  executed dependency. Route resolution, endpoint, transport, and all
  downstream transforms still need provider-free fixture characterization
  against the tagged source.
- The `o200k_base` encoding counts text. It cannot exactly count the full
  Responses request, especially tool schemas, media, files, and service-side
  structure. Exact count needs the Responses input-token endpoint and the same
  effective request body.
- The context hook does not itself identify the final route or endpoint.
  A matched gate would need a verified binding to the resolved model/route and
  must fail closed on route rewrites or unsupported request shapes.
- No evidence here proves the runtime applies the same source tag, that a
  callback error prevents dispatch, or that a Wrench admission result is
  enforced by OpenCode.

## Follow-up: hook result and local token estimate

An independent source trace of the pinned `v2.0.15` tag confirmed that the
Promise-plugin `session.context` callback type returns `void | Promise<void>`,
not an admission result. Separately, the core Effect hook trigger runs its
registered callbacks in order and returns the mutated event; its event also has
no typed admission or veto result. A thrown callback may fail request
preparation, but the tagged source does not define that failure as a supported,
verified dispatch veto. The context hook therefore cannot by itself enforce a
Wrench prompt-admission decision.

The same trace found that OpenCode's local compaction estimator is a heuristic:
`Token.estimate` rounds JavaScript string `.length` (UTF-16 code units) divided
by four, while images and PDFs use fixed estimates and prior provider usage may
anchor later estimates. This is a context-window sizing estimate, not exact
tokenization of the final provider request. The Wrench-side `tiktoken==0.9.0` /
`o200k_base` pin remains a reproducible text-count candidate only; it does not
count the full Responses request structure, tools, or media exactly.

This follow-up is still source-only. It does not validate the installed client,
exception propagation, final transport payload, tokenizer parity, or dispatch
blocking. The `session.context` shape and post-hook request lowering remain
documented in the tagged source references below.

No OpenCode client, JavaScript package, tokenizer package, tokenizer data, or
model was installed or downloaded. No provider call, test, inference,
benchmark, data capture, or training run was made. Source characterization is
not E0 completion.

## Primary references

- OpenCode [`SessionHooks.context` type](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/plugin/src/promise/session.ts)
- OpenCode [`SessionModelRequest` preparation and tool/option lowering](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/core/src/session/model-request.ts)
- OpenCode [session runner request call](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/core/src/session/runner/llm.ts)
- OpenCode [`LLM.request` normalization](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/ai/src/llm.ts)
- OpenCode [OpenAI Responses protocol lowerer](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/ai/src/protocols/openai-responses.ts)
- OpenCode [`RouteBody.from`, route compilation, schema validation, and transport preparation](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/ai/src/route/client.ts)
- OpenCode [`@opencode/ai` v2.0.15 package manifest](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/ai/package.json)
- OpenCode [Promise `session.context` hook type](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/plugin/src/promise/session.ts)
- OpenCode [core Effect hook trigger](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/core/src/plugin/hooks.ts)
- OpenCode [character-based token estimate](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/core/src/util/token.ts)
- OpenCode [compaction estimate and media constants](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/core/src/session/compaction.ts)
- OpenAI tiktoken [v0.9.0 `o200k_base` definition and expected encoding hash](https://raw.githubusercontent.com/openai/tiktoken/0.9.0/tiktoken_ext/openai_public.py)
- OpenAI tiktoken [v0.9.0 model-to-encoding mapping](https://github.com/openai/tiktoken/blob/0.9.0/tiktoken/model.py)
- OpenAI [input-token counting guide](https://developers.openai.com/api/docs/guides/token-counting)
