# Iteration 073: SubRoute provider controls at the request root

- **Job:** `WRENCH-OPENAI-RAW-EXTRABODY-PROBE-20260928`
- **Result:** **PASS** for metadata-only ASGI ingress and root-level provider controls through the mocked LiteLLM 1.103.0 request path.
- **Provider egress:** none.

## Identity

| Repository | HEAD |
|---|---|
| Wrench | `af01304824f079a64b6c3902397a2034b843511a` |
| SubRoute | `51d262370b3de790ee97ec6b9d43c33e4b44a2ee` |

SubRoute source identities after the fix:

| File | SHA-256 |
|---|---|
| `config/litellm.yaml` | `05B40C8A4B95E7D9703DD88102F4D981F760CBF17DA30D2DEF781EF958EF0735` |
| `src/unified_llm_gateway/plugins/openrouter_request_controls.py` | `C9915FC3B561C18DCF204B1581BAF3AE34EC0FBB5B0A4F7E5C3186510A4CF40C` |
| `tests/test_openrouter_request_controls.py` | `C8D1C52D812AFE98D2D8D3226E514A385C941315D8EFE66090EA06343F4D47E9` |
| `tests/test_openrouter_proxy_ingress.py` | `A791B29D40F1A5D51AF28A9C7420B55AAF317A7056157AE487FBE87501F7D40F` |

## Root cause and change

Iteration 072's ASGI test reached the Wrench metadata validator and sent the metadata header, but captured `provider` and `usage` inside a literal `extra_body` JSON member. Source inspection of the running LiteLLM 1.103.0 image showed the OpenRouter route uses `litellm/llms/custom_httpx/llm_http_handler.py`; `_make_common_async_call` serializes the transformed dictionary with `json.dumps(data)`. It does not pass the dictionary through OpenAI SDK `extra_body` handling.

A separate in-process OpenAI 2.33.0 `MockTransport` probe showed normal `.create` and `.with_raw_response.create` both merge SDK `extra_body` members at the JSON root. That falsified the initial suspicion that the raw-response wrapper caused the nesting. The LiteLLM `custom_httpx` serialization path is the cause supported by this evidence.

The SubRoute adapter now merges any mapped `extra_body` entries into the transformed dictionary's root, rejects conflicting duplicate values, and writes metadata-derived `provider` controls at the root. The metadata header remains set to `enabled`. The unit test now checks this actual LiteLLM payload shape without simulating a separate OpenAI SDK path. Existing invalid-control, conflicting-control, default-route, and header-rejection cases remain covered.

## Verification

Against the existing `unified-llm-gateway` image with LiteLLM 1.103.0:

- `tests/test_openrouter_request_controls.py`: **5/5 passed**.
- `tests/test_openrouter_proxy_ingress.py`: **1/1 passed**.

The ASGI test sends a metadata-only request through `proxy_server.app` using `TestClient` and a manually configured in-memory Router. Its replacement `httpx.AsyncClient.send` accepts only `127.0.0.1:9`, captures the serialized request, and returns a synthetic response. The passing assertions verify metadata arrival at the adapter validator, the `X-OpenRouter-Metadata: enabled` header, root-level `provider` controls, root-level `usage.include`, and exactly one mocked request to the loopback dummy URL. The Wrench checkout's test source was piped to the existing container with `python -B`; no test source or bytecode was copied into the running service.

## Limits and next gates

This establishes the mocked request contract for the manually assembled ASGI app on LiteLLM 1.103.0. The test imports the plugin directly, sets LiteLLM callbacks to an empty list, and does not load `config/litellm.yaml` or exercise ASGI lifespan. It does **not** establish that the running port 4000 process loaded the dirty checkout, that a real OpenRouter provider selects MiniMax, or that usage and billed-cost receipts are correct. The 4000 service was not restarted and received no completion. The host SubRoute lock still pins LiteLLM 1.101.0; compatibility with that exact locked runtime remains unverified.

No LoRA training, local coding task, frontier comparison, or paid request ran. This result says nothing about 95% local completion, 5% frontier routing, retained task success, frontier-token reduction, all-in cost, or all-day engineering. Paid calls remain closed without numeric campaign authorization and durable caller-side accounting.

## Resource and storage

Before the direct unit run, free RAM was 3,797.2 / 32,701.8 MiB (11.61%); during it, 3,833.5 MiB remained free. Before the ASGI run, free RAM was 3,771.3 MiB (11.53%); during it, 3,762.8 MiB remained free. VRAM samples ranged from 15,189 to 15,228 / 16,311 MiB free. The latest post-test sample was 3,410.5 MiB free RAM (10.43%), still above the 10% floor but below the 25% fit-03 launch gate. No further runtime job was started.

The Wrench storage checker reported `WITHIN_LIMIT` before the job, with the SubRoute repository explicitly included and a 100,000-byte reservation. C: free space was checked after the runs. After this report and the updated goal record were accounted and the test processes stopped, that reservation was released; final status including SubRoute remained `WITHIN_LIMIT`. No model, dataset, checkpoint, or persistent test output was produced.
