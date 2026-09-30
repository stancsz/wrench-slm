# Iteration 072: SubRoute ASGI ingress and mocked wire-body integration

- **Assignment:** `WRENCH-SUBROUTE-ASGI-INGRESS-ITER072-20260928`
- **Independent review:** `WRENCH-SUBROUTE-ASGI-REVIEW-ITER072-20260928`
- **Disposition:** **FAIL for the provider-control wire contract; ingress metadata forwarding observed.**
- **Paid requests:** 0. **Provider requests:** 0.

## Revisions and source identity

| Repository | HEAD |
|---|---|
| Wrench | `af01304824f079a64b6c3902397a2034b843511a` |
| SubRoute | `51d262370b3de790ee97ec6b9d43c33e4b44a2ee` |

The SubRoute files exercised or in scope were:

| File | SHA-256 |
|---|---|
| `config/litellm.yaml` | `05B40C8A4B95E7D9703DD88102F4D981F760CBF17DA30D2DEF781EF958EF0735` |
| `src/unified_llm_gateway/plugins/openrouter_request_controls.py` | `334901565986DACF7E689E37AC6DA914D02BFB374732A85A09BF55FDC9F4B46E` |
| `tests/test_openrouter_request_controls.py` | `56474AEF1CCEB773AFDD1CB2A4D065C4C67D22B94E102E71A6B66A8B0461D1E9` |
| `tests/test_openrouter_proxy_ingress.py` | `A791B29D40F1A5D51AF28A9C7420B55AAF317A7056157AE487FBE87501F7D40F` |

The ingress test is a new untracked file in the already-dirty SubRoute checkout. No existing file was reset or cleaned. The independent static review matched both HEADs and all four hashes before and after, and confirmed the test's boundary and failure. Its report is [here](iteration-072-subroute-asgi-ingress-independent-review-20260928.md). The reviewer did not rerun the test because the assignment was static-only; it also notes that plugin import installs a process-global transform patch which this test does not restore. Each test run was a separate short-lived `docker exec` process, so the patch did not persist in the running gateway.

## What was exercised

The owner-directed local SubRoute at `http://127.0.0.1:4000` had previously returned HTTP 200 for `GET /health/liveliness` and `GET /models`; the models response listed 19 aliases. No completion was sent to that running port.

The no-provider integration ran the test source inside the existing `unified-llm-gateway` container, whose LiteLLM version is 1.103.0. It imported the actual LiteLLM FastAPI ASGI app, sent a metadata-only request to `/v1/chat/completions` through `TestClient`, and configured an in-memory Router for `openrouter/minimax/minimax-m3`. The test replaced `httpx.AsyncClient.send` with a synthetic responder that accepts only `127.0.0.1:9`, captures the serialized request, and returns a fixture response. No real provider or network transport was available to the test. The deployed container was not restarted and its `litellm.yaml` loader was not invoked.

## Result

The one-test run **failed** (`Ran 1 test`, `FAILED (failures=1)`). Checks before the failing assertion established that:

- the ASGI request returned the synthetic HTTP 200 response;
- `metadata.wrench_openrouter_provider_controls` reached the adapter validator unchanged;
- exactly one send reached the mocked transport at `http://127.0.0.1:9/v1/chat/completions`; and
- `X-OpenRouter-Metadata: enabled` was present on that captured request.

The required wire-body check failed. The captured JSON had no root-level `provider` field. Instead it contained:

```json
{
  "extra_body": {
    "usage": {"include": true},
    "provider": {
      "only": ["minimax"],
      "allow_fallbacks": false,
      "max_price": {"prompt": 0.3, "completion": 1.2}
    }
  }
}
```

This does not satisfy the required OpenRouter request-body shape. The result proves the incoming HTTP metadata path reaches the plugin, but it disproves the claim that the current ASGI-to-SDK path emits provider controls at the expected wire location. The earlier direct SDK unit test calls `.chat.completions.create`; LiteLLM 1.103.0's request helper uses `.chat.completions.with_raw_response.create`. That difference is a plausible explanation for why the direct test does not catch the ASGI failure, but it has not been isolated as the cause.

## Interpretation and next gate

Treat SubRoute provider-control routing as **not integration-ready**. Correct the adapter for the actual LiteLLM ASGI/SDK call path, keep the ASGI test asserting the required root-level JSON fields and metadata header, then rerun it against the exact deployed LiteLLM image. A passing mocked integration still would not establish provider selection, billing, real 4000-process callback loading, or Wrench end-to-end spend accounting.

The test uses a manually configured `proxy_server.app` and in-memory Router; it does not load `litellm.yaml`, run ASGI lifespan through a context-managed `TestClient`, or verify the callback in the live 4000 process. The independent review confirms these limits and did not independently rerun the test. The model/token/cost hypothesis remains unanswered by this integration check. No LoRA was trained, no coding task was dispatched, and no task-success, routing-rate, frontier-token reduction, cost reduction, or all-day engineering metric was measured. Do not convert this result into 95/5/95 evidence. No numeric campaign-wide paid-call cap was supplied, so no paid completion was made.

## Resource and storage record

Before the final test, free RAM was 3,963.1 / 32,701.8 MiB (12.12%); during it, 3,925.8 MiB (12.00%) remained free. VRAM was 15,214 / 16,311 MiB free (93.3%). Both remained above the 10% floor. RAM remains below the separate 25% fit-03 start gate; no fit-03 job was launched.

At test admission, the Wrench storage checker reported `WITHIN_LIMIT`: 10,993,960,847 actual bytes against the 50,000,000,000-byte ceiling, with 6,303,000 bytes of active reservations. The C: volume had 135.22 GB free. After both reports and the test output were accounted for and the jobs stopped, the 100,000-byte ingress and independent-review reservations were released. Final status with `--include-root C:\Users\stanc\github\subroute` remained `WITHIN_LIMIT`: 10,993,972,986 actual bytes and 6,103,000 bytes in other active reservations. A later text-only closeout edit was admitted under separate reservation `WRENCH-ITER072-DOC-FINALIZE-20260928` for 25,000 bytes, including the SubRoute root; that reservation is released after final accounting. This was a source-piped test and created no model, dataset, checkpoint, or benchmark output.

The source command was `Get-Content -Raw tests/test_openrouter_proxy_ingress.py | docker exec -i unified-llm-gateway python -B -`. The only egress-like call was intercepted in-process by the mock and restricted to loopback port 9. No credentials were read. The only calls to port 4000 were the previously recorded GET health/models checks.
