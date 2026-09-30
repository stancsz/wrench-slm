# Independent review: SubRoute ASGI ingress regression

- **Assignment:** `WRENCH-SUBROUTE-ASGI-REVIEW-ITER072-20260928`
- **Nonce:** `9b469c61-c33e-427e-88bf-a9e2236208e4`
**Verdict:** The test is useful and establishes metadata arrival and a no-network mocked provider path, but it currently fails its intended provider-body assertion. It is not a passing regression for the expected OpenRouter wire shape.

## Findings

The ingress test posts to `/v1/chat/completions` with the Wrench controls only in `metadata`; it does not provide a top-level OpenRouter `provider` argument. Its observer wraps `controls_adapter._validated_provider_controls`, reads the marker from the received `litellm_params["metadata"]`, records its value, and delegates to the original validator. The test asserts that the exact supplied controls were observed. The parent reports this assertion passed in the final run, so the request does demonstrate metadata-only ASGI ingress reaching the adapter validator in this harness.

The adapter code validates that metadata and constructs `extra_body["provider"]`; it also sets `X-OpenRouter-Metadata: enabled`. In the final runtime result supplied by the parent, the captured request has the metadata header, but its JSON nests both fields under `"extra_body"` (`{"extra_body": {"provider": ..., "usage": ...}}`). The test expects `provider` and `usage` at the JSON root. Its root-level provider assertion therefore fails. The adapter reaches its transformation, but this test does not demonstrate the expected OpenRouter wire body; the observed serialized shape contradicts that expectation. The failure is useful because it exposes the integration boundary that the isolated adapter unit test does not cover.

The isolated unit test separately exercises the adapter transformation and OpenAI SDK with `httpx.MockTransport`, and asserts root-level provider/usage fields plus the metadata header. However, its input includes `provider_argument=PROVIDER_CONTROLS` as well as metadata. It is therefore not a metadata-only regression and cannot establish the full ingress path's serialization behavior.

Provider egress is prevented for this test path. The test replaces `httpx.AsyncClient.send` with a function that records the request, rejects destinations other than `127.0.0.1:9`, and returns a synthetic response without invoking the original send method. The configured API base is that local dummy address. The parent reports one intercepted request and no provider call. This makes real network transport impossible through the exercised async HTTP client path; the captured request is only an in-process mock. The claim is bounded to this configured LiteLLM/OpenRouter path and the patched transport.

The test restores the globals it changes in `finally`: the validator, `AsyncClient.send`, proxy router and general settings, and `litellm.callbacks`. It also closes the `TestClient`. One process-global mutation is not restored: importing `controls_adapter` imports a module whose module-level plugin instance installs the `OpenrouterConfig.transform_request` wrapper. That import-time patch can affect other tests in the process. The test also sets `litellm.callbacks = []`, so it does not test the callback-loading path listed in `config/litellm.yaml`; it manually imports the adapter module, whose plugin instance installs the wrapper. Finally, `TestClient` is used without its context manager, so ASGI lifespan startup/shutdown is not exercised. The test uses a manually built `Router` and patched proxy globals rather than loading the configured gateway lifecycle.

## Identity and review scope

Repository identities were unchanged before and after the review:

| Repository | Expected and observed HEAD |
|---|---|
| `C:\Users\stanc\github\wrench-slm` | `af01304824f079a64b6c3902397a2034b843511a` |
| `C:\Users\stanc\github\subroute` | `51d262370b3de790ee97ec6b9d43c33e4b44a2ee` |

The four assigned SubRoute file hashes matched before and after review:

| File | SHA-256 |
|---|---|
| `config/litellm.yaml` | `05B40C8A4B95E7D9703DD88102F4D981F760CBF17DA30D2DEF781EF958EF0735` |
| `src/unified_llm_gateway/plugins/openrouter_request_controls.py` | `334901565986DACF7E689E37AC6DA914D02BFB374732A85A09BF55FDC9F4B46E` |
| `tests/test_openrouter_request_controls.py` | `56474AEF1CCEB773AFDD1CB2A4D065C4C67D22B94E102E71A6B66A8B0461D1E9` |
| `tests/test_openrouter_proxy_ingress.py` | `A791B29D40F1A5D51AF28A9C7420B55AAF317A7056157AE487FBE87501F7D40F` |

Static review was limited to those four files. Read-only commands used were `git -C <repo> rev-parse HEAD`, `Get-FileHash -LiteralPath` for the four assigned files before and after, `Get-Content -LiteralPath` for those files, and `rg -n` searches limited to those files. Two initial targeted `rg` expressions failed to parse; simpler expressions succeeded. Resource samples used `Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory,TotalVisibleMemorySize` and `nvidia-smi --query-gpu=memory.free,memory.total --format=csv,noheader`. Before and after review, RAM and VRAM remained above the required 10% free threshold.

No tests, runtime commands, HTTP requests, provider calls, network access, credential/environment reads, or SubRoute source edits were performed by this reviewer. The LiteLLM 1.103.0 test result and captured wire shape cited above were supplied by the parent and were not independently rerun under this static-only assignment.

The task-provided reservation was 100,000 bytes and included the SubRoute root. This review produced only this report and no SubRoute artifacts. The storage checker was not run because it was outside the assigned command allowlist; reservation status was therefore not independently revalidated.
