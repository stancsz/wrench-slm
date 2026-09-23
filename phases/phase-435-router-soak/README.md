# Phase 435: bounded Gate E router soak

Date: 2026-09-22

## Decision and scope

The human approved one retry of the local 200-request soak with up to eight
concurrent clients and a five-minute limit, against the Phase 434 loopback-only
test handler with deterministic fake callbacks. The approved retry parameters
were a 20-second test-only proposal queue/invocation timeout and a 30-second
local HTTP timeout. The runner binds an ephemeral `127.0.0.1` port, configures
no upstream, sends no provider traffic, loads no model, and samples system RAM
and GPU VRAM against the 10% reserve. It stores aggregate results only. No
workload or prompt file is written.

## Result

**Attempt 01: FAIL.** The run stopped on the first response that did not
satisfy the acceptance check. It started 29 requests, accepted 28, and
recorded one failed response in 7.977 seconds. The callback launched 28
children; router attempts were 28 with zero callback failures and the circuit
remained closed. No child was active before or after server shutdown. It is
not Gate E pass evidence.

The response-level fallback reason was not captured. The unchanged child and
router counts were consistent with a queue timeout, but did not prove one.

**Attempt 02: FAIL, with a configuration mismatch.** The one approved retry
started 29 requests, accepted 27, and captured two `router_queue_timeout`
responses in 8.116 seconds. It launched 27 callback children, recorded 27
router attempts, and kept the circuit closed with zero callback failures. No
child was active before or after shutdown. Minimum reserves were 54.13% free
RAM and 89.43% free RTX 5070 Ti memory. It used ephemeral loopback port 55622.

The retry did not use its approved 20-second proposal timeout and 30-second
HTTP timeout. The runner had no argument parser, so invoking it with
`--help` started the run using its old five-second proposal timeout and
12-second HTTP timeout. Attempt 02 therefore confirms the queue-timeout cause
under the old settings, but is not evidence for the approved adjusted retry.
The single approved execution opportunity has been consumed. No additional
HTTP soak is authorized by that approval.

**Attempt 03: PASS, test-only bounded soak.** After fresh Q4 approval and
preflight resource checks, the corrected 20-second proposal and 30-second HTTP
settings completed all 200 requests in 54.527 seconds with eight concurrent
clients. All 200 callbacks launched and succeeded; there were zero failed or
cancelled requests, router failures, fallback observations, or surviving
children. The circuit remained closed. The ephemeral loopback port was 52172.
Minimum observed free reserves were 53.81% RAM and 89.54% GPU memory.

Attempt 03 was isolated to `127.0.0.1`, used an injected deterministic
test-only callback, loaded no model, configured no upstream, accessed no
credentials, persisted no request payloads or prompts, and made zero provider
requests and zero model calls. It verifies this bounded serving-path fixture
only. It does not close Gate E for model-worker lifecycle and recovery, nor
establish production routing or release readiness.

## Evidence

- Redacted receipt: [router-soak-receipt.json](router-soak-receipt.json)
  SHA-256: `3a47fc9cd8614d7cb5e26ff9ef7e9fe93f419f2bb8442c44c4f304cbd2070c01`
- Redacted attempt 02 receipt:
  [router-soak-receipt-attempt-02.json](router-soak-receipt-attempt-02.json)
  SHA-256: `83fa7753e7ebf9703675ea5f8caeb6b1ecb69977a8070a6143676c7b7342e7d5`
- Redacted attempt 03 receipt:
  [router-soak-receipt-attempt-03.json](router-soak-receipt-attempt-03.json)
  SHA-256: `fcccf36643005a9e69aba60e4acb2ea9c14584e1cc1c45d5db13a8679ee3c400`
- Fixed-scope runner: [run_gate_e_router_soak.py](../../tools/run_gate_e_router_soak.py)
- Diagnostic regression checks: [test_gate_e_soak_runner.py](../../tests/test_gate_e_soak_runner.py)
- Runner Ruff check passed and the Q4 collaboration contract validator
  returned `VALID` before execution.
- Before attempt 02, the runner was hardened to store only allowlisted
  response metadata and select a new receipt path per attempt. The attempt
  captured `router_queue_timeout` without saving prompt or arbitrary response
  details.
- After attempt 02, the runner was set to the approved 20-second proposal and
  30-second HTTP timeouts. It requires an explicit `--run` flag, so `--help`
  and an invocation without that flag cannot launch the soak. Attempt 03 used
  those settings after fresh Q4 approval.
- Before the attempt 02 CLI fix, `py -3 -m pytest -q` passed 310 tests with 18
  existing Windows asyncio deprecation warnings. This did not repeat the Gate
  E HTTP soak.
- After the runner fix, `py -3 -m pytest -q` passed 313 tests with the same 18
  warnings. Ruff passed, the Q4 contract validator returned `VALID`, and the
  real `--help` command printed usage without launching a soak. At that
  checkpoint, no HTTP soak had yet been run with the corrected settings;
  attempt 03 later completed that approved run.

## Next decision and stop boundary

Q4 checkpoint: the earlier one-run approval was consumed by attempt 02, which
used the old timeouts. On 2026-09-22 the human gave fresh approval for exactly
one corrected local fake-callback soak. That approval was consumed by attempt
03. It does not authorize a provider call, model request, production route, or
any additional soak.

- Recommendation: keep the bounded fixture result as test-only Gate E evidence
  and leave Gate E open for the model-worker and sustained operational gaps.
- Alternative: reject the fixture result as insufficient for even the bounded
  router lifecycle, which would require an independently approved new test.
- Evidence and impact: attempt 03 completed 200/200 requests with clean router
  and child receipts and safe reserves. Attempts 01 and 02 remain failed
  evidence. The result does not exercise a model or provider.
- Rollback: no production route or runtime setting changed. Preserve all
  three receipts and revert only the local test wiring if it causes a failure.
- Decision deadline: the one-run approval is consumed. Any further soak needs
  a fresh Q4 decision and must retain the loopback-only, fake-callback,
  200-request, eight-concurrent, five-minute boundary and the same stop rules.
