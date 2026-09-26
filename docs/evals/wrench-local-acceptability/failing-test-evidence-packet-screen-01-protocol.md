# Failing-test evidence packet screen 01

Status: frozen synthetic deterministic-mechanics screen; one bounded run is
authorized by the owner's request to measure acceptable local work. It does
not authorize SLM inference, training, client execution, provider traffic, or
real-data capture.

## Question

Can the local deterministic E0 route and a bounded host-side parser produce a
complete evidence packet from noisy test output, joining every reported test
failure to its exact log line and unique source definition, while abstaining
on missing, stale, or ambiguous evidence?

This measures composed deterministic mechanics on fresh Wrench-authored
synthetic data. It does not test SLM semantic quality, real coding work,
customer utility, or downstream token savings.

## Frozen inputs and identities

- Fixture: `tests/fixtures/failing_test_evidence_packet_screen_01.json`
  SHA-256 `914618905adcf48bc6d609f20b2588e61ae2b677d66b4e0f26eda05e62a3c898`
- Runner: `tools/run_failing_test_evidence_packet_screen_01.py`
  SHA-256 `e17194e2d498acc265ec80ee0dc908836cc8b4ff9f82c3611d5348a0236f7630`
- Fixture contains three fresh positive cases, each with two failures and
  noisy non-failure lines, plus three boundaries: missing log, changed/stale
  log, and ambiguous candidate logs. Fixture and source files are synthetic,
  small, and outside all training/replay paths.
- The screen uses `wrench_harness.e0_rule_route` and
  `wrench_harness.snapshot` from the source revision recorded in the receipt.
  The runner's parser reads only successful snapshot-bound route observations;
  the frozen expected packet is scoring-only.

## Exact decision rule

Each positive packet must have exact one-to-one coverage of every `FAILED`
record in its noisy log. Every result must match the exact test ID, source
path, unique source-definition line and bytes, log path, one-based log line,
and full log-line bytes. No extra, missing, duplicate, or unsupported finding
is allowed. Pass requires all three positive packets exact (6/6 failures).

Each boundary must abstain with its frozen exact reason: missing source,
snapshot-changed source, or ambiguous/unsupported request. Pass requires all
three boundary outcomes correct. Every fixture file hash and positive request
hash must match its frozen bytes. No unexpected fixture mutation, unsafe
dispatch, or runtime error is allowed. The one declared stale-source mutation
is intentional and must match its frozen target bytes exactly.

Overall screen pass requires 3/3 exact positive packets, 3/3 exact boundary
abstentions, zero unexpected mutations, zero unsafe dispatches, zero runtime
errors, and completion within 30 seconds. Any failed condition rejects this
screen. Even a pass supports only open-development deterministic mechanics; it
does not accept a semantic SLM class or establish a real-world operating rate.

## Run bounds

- Unique job ID: `WRENCH-LOCAL-FAILURE-PACKET-20260927-01`
- Nonce: `FTP01-6C2A`
- One run, maximum 30 seconds; receipt maximum 2 MiB.
- Existing storage reservation: `WRENCH-LOCAL-FAILURE-PACKET-20260927-01`,
  10,000,000 bytes. Require storage status `WITHIN_LIMIT` and confirm this
  reservation before launch. Recheck after execution and release only after
  stopping the runner and accounting for outputs.
- Run with `python -B` to avoid bytecode caches. Temporary snapshots are
  created only below the approved artifact root and removed at process exit.
- No model, network, client, provider, training, download, or real source data.
- Keep at least 10% system RAM and VRAM free; check destination volume space.

The sole receipt path is
`C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\failing-test-evidence-packet-screen-01.json`.
Do not overwrite it or rerun this screen. Report per-case outcomes, latency,
resource/storage observations, and the exact fixture/runner identities.
Frontier-token savings remains N/A; there is no downstream arm.
