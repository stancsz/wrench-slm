# Phase 195: v79 bundled 220-case replay with isolated health fixture

Date: 2026-09-20

## Runtime

The v79 package was loaded from:

`D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v79-health-fixture-replay`

The package-local `wrench_runtime` endpoint served all 220 requests. Client
mechanical fast-path bypass was enabled, so every Wrench request crossed the
package-local HTTP endpoint. The teacher arm reused the existing proposal-only
capture and made no provider request.

The replay started a deterministic loopback health fixture on port 28907 and
set the explicit test-only `WRENCH_TEST_HEALTH_FIXTURE_BASE_URL`. The verifier
preserved the requested `localhost:4000` URL and recorded the fixture transport
URL in accepted health observations. With the variable absent, production
transport behavior is unchanged.

## Receipt

The corrected 220-case contract returned `PASS_MECHANICAL_WORKER`:

- 220 traces, 120 eligible mechanical traces;
- weighted mechanical frontier-token coverage: `96.2576%`;
- net frontier-token savings: `96.1611%`;
- Wrench-plus-identical-fallback weighted final success: `99.6767%`;
- teacher weighted final success: `70.7422%`;
- Wrench frontier tokens: `2,487`;
- Wrench local tokens: `23,643`;
- Wrench-plus-fallback median latency: `187.900 ms`, p95 `355.140 ms`;
- Wrench-only diagnostic median latency: `187.640 ms`, p95 `336.630 ms`;
- Wrench fallback count: `5`;
- zero prohibited accepts;
- zero unexpected mutations.

The structural package receipt is `package-validation.json`. The full replay
receipts are `evaluation.json` and `trace-manifest.json` in this directory.

## Interpretation and open gates

This is the strongest current bundled 220-case diagnostic because the health
fixture removes unrelated host-service noise. It is still not the final
family-disjoint real-workflow approval, not MiniMax parity proof, and not
production enablement. The independent 5060Ti receipt for the current source
commit is still missing. Dense native attention remains optional research, not
the Wrench product selling point or release gate.
