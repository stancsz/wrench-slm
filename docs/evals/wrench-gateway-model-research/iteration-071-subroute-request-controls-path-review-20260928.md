# SubRoute Request Controls Path Review

**Assignment:** `WRENCH-SUBROUTE-REQUEST-CONTROLS-REVIEW-ITER071-20260928`  
**Nonce:** `25f948bf-4a48-48db-b9f6-085bf48a759f`  
**Verdict:** **CONDITIONAL**

## Revision and pin checks

| Repository | HEAD before review | HEAD after review |
|---|---|---|
| Wrench | `af01304824f079a64b6c3902397a2034b843511a` | `af01304824f079a64b6c3902397a2034b843511a` |
| SubRoute | `51d262370b3de790ee97ec6b9d43c33e4b44a2ee` | `51d262370b3de790ee97ec6b9d43c33e4b44a2ee` |

| Assigned file | Expected SHA-256 | Observed SHA-256 | Match |
|---|---|---|---|
| Wrench `tools/capture_subroute_teacher_traces.py` | `8852DED137D07A5CF7E47F93E38CA310272EF0CE0E0B0EEA131A347925DC9AE6` | `8852DED137D07A5CF7E47F93E38CA310272EF0CE0E0B0EEA131A347925DC9AE6` | Yes |
| Wrench `tools/subroute_budget_guard.py` | `DAB8B7212E91C2687E13F53AB619E296BAE3FB91E10B716AD57EC4C4933FB00B` | `DAB8B7212E91C2687E13F53AB619E296BAE3FB91E10B716AD57EC4C4933FB00B` | Yes |
| SubRoute `config/litellm.yaml` | `05B40C8A4B95E7D9703DD88102F4D981F760CBF17DA30D2DEF781EF958EF0735` | `05B40C8A4B95E7D9703DD88102F4D981F760CBF17DA30D2DEF781EF958EF0735` | Yes |
| SubRoute `src/unified_llm_gateway/plugins/openrouter_request_controls.py` | `334901565986DACF7E689E37AC6DA914D02BFB374732A85A09BF55FDC9F4B46E` | `334901565986DACF7E689E37AC6DA914D02BFB374732A85A09BF55FDC9F4B46E` | Yes |
| SubRoute `tests/test_openrouter_request_controls.py` | `56474AEF1CCEB773AFDD1CB2A4D065C4C67D22B94E102E71A6B66A8B0461D1E9` | `56474AEF1CCEB773AFDD1CB2A4D065C4C67D22B94E102E71A6B66A8B0461D1E9` | Yes |

## Findings

**The assigned adapter, config, and test do not establish that metadata from a real incoming `POST /v1/chat/completions` reaches `litellm_params["metadata"]`.** The Wrench caller constructs a request containing both top-level `provider` controls and `metadata.wrench_openrouter_provider_controls` (`capture_subroute_teacher_traces.py:95-117`) and posts it to the configured local completion endpoint (`:144`). That proves what the caller sends, not how the gateway maps the inbound JSON.

The SubRoute config registers `openrouter_request_controls_plugin` in LiteLLM's callback list (`litellm.yaml:283-287`). The adapter reads only an already-formed `litellm_params["metadata"]` dictionary (`openrouter_request_controls.py:38-44`); its signature-checked wrapper calls LiteLLM's OpenRouter request transformation and validates that metadata (`:88-118`). When present and valid, it adds the controls to the OpenRouter body under `extra_body.provider`, rejects conflicts, and sets `X-OpenRouter-Metadata: enabled` (`:133-153`). This is post-mapping behavior. Config registration is evidence of intended loading, not evidence of inbound field propagation or that the running service loaded this dirty checkout.

The test provides a narrower proof. Its helper calls `OpenrouterConfig.async_transform_request` directly and supplies `litellm_params={"metadata": metadata or {}}` itself (`test_openrouter_request_controls.py:28-52`). The invalid-control and conflicting-body cases exercise metadata-only adapter input at that layer (`:116-134`). The successful case captures the final OpenAI SDK request with `httpx.MockTransport` (`:61-108`), proving the transformed outbound body/header for those already-supplied arguments without provider traffic. That successful case also supplies `provider_argument=PROVIDER_CONTROLS` (`:61-65`), so it is not an isolated end-to-end proof of the metadata source. None of these cases sends a request into LiteLLM's HTTP completion endpoint.

## What remains unverified and smallest next proof

Unverified: the deployed LiteLLM inbound request parser and routing/callback path, including whether this request's `metadata` object is retained as `litellm_params["metadata"]` for the configured OpenRouter alias. The source/test evidence also does not prove the plugin is loaded by the currently running service or that the deployed LiteLLM version follows the tested transformation path.

The smallest useful next proof is a no-provider integration test against the configured LiteLLM ASGI app (or an isolated service instance) that posts the exact Wrench-shaped JSON to `/v1/chat/completions`, replaces OpenRouter transport with a mock, and asserts that the adapter receives this metadata key and emits the expected provider body plus metadata header. Avoid a live completion request until that ingress path is proven.

## Limits, commands, and changes

- **Resource check:** parent-provided current RAM sample was 4,745.8 / 32,701.8 MiB free (14.51%); the permitted VRAM sample returned 15,203 / 16,311 MiB free. Both were above the 10% floors.
- **Scope:** static inspection of only the five assigned source/config/test files; no tests, server, runtime probe, HTTP request, provider call, credential/environment read, or unrelated-file inspection.
- **Commands:** `git -C ... rev-parse HEAD` for both repositories; `git -C ... status --short` for SubRoute context; `Get-FileHash -LiteralPath` for all five assigned files before and after; `Get-Content -LiteralPath` for those files; `rg -n` restricted to those five paths; and the permitted read-only RAM/VRAM sample commands. No source files were changed. SubRoute was already dirty in its assigned config/adapter/test files and other listed paths; no changes were made there. The only write was this requested report.
