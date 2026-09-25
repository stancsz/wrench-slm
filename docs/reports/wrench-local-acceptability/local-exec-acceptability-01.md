# Deterministic local operation screen 01

Date: 2026-09-25 (America/Edmonton)

## Result

**Invalid scorer run; no class result accepted.** The runner processed all 10
open-development synthetic cases. It returned the expected `completed` or
`abstain` status for every case, produced exact search observations for 2/2
literal-search cases, and made the exact expected abstention on 3/3
missing/stale/ambiguous cases. It returned successful read observations for
all five read-file cases, but the scorer marked their observation equality
false.

The cause is a measurement-harness omission: the frozen fixture's
`expected_mechanics` read-file object does not carry a `bytes` field, while
both the E0 route and core executor correctly return that field. The existing
fixture test explicitly adds the expected UTF-8 byte count before comparing
the route result. The runner omitted the same normalization. This is visible
in the receipt as five successful route statuses and five accepted executor
statuses, alongside five read observation comparison failures. It is a scorer
failure, not evidence that the read operations failed or passed the exact
oracle.

No operation class passes this run. The valid subset diagnostics are the two
literal-search mechanics cases and the three exact safe abstentions; they do
not repair the overall invalid read scorer. No unexpected mutation or unsafe
dispatch was observed. No model inference, provider/client call, training, or
frontier usage occurred. Frontier-token savings are N/A.

## Identity

- Preregistration: [deterministic execution protocol 01](../../evals/wrench-local-acceptability/deterministic-execution-protocol.md).
- Runner revision: `e907878b740860b65dc461a285e27c5ce8efafaf`.
- Fixture manifest SHA-256: `871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5`.
- Review receipt SHA-256: `b5c32928841b66aa679eccdbd7d88a4bffad4075b07f794f2a42d380961c1b2f`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-local-acceptability\local-exec-acceptability-20260925-01.json`.
- Receipt SHA-256: `f55a9b64e3777db99bc21d2efc9eb516f19bdc6e2365dd961658033714338a28` (10,416 bytes).
- The 5,000,000-byte reservation for this run covered the run and output. The
  approved data root remained below the aggregate 50 GB limit.

## Correction and disposition

The run is retained unchanged as a harness-invalid result. A corrected scorer
will derive the read byte count from the already hash-verified fixture bytes,
check the complete isolated temporary file inventory before and after each
executor call, and report the five fixture pairs separately rather than
combining availability with specificity. These are evaluator corrections;
the Wrench router and executor are not being tuned. Any follow-up is a new
preregistered run with a unique output receipt and storage reservation. Even a
clean follow-up remains exposed fixture mechanics, not task utility or a
production acceptability rate.
