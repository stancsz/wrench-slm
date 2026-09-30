# Iteration 019: SubRoute spend guard and receipt integrity

Date: 2026-09-27 (America/Edmonton)

Status: **12 FOCUSED TESTS PASSED; NO GENERATION, MODEL INFERENCE, OR EFFECTIVENESS MEASUREMENT**

## Purpose

The diagnostic harness previously treated missing provider usage and price
fields as zero and retained a direct helper capable of posting to the teacher
endpoint. The owner directed this work to use the existing SubRoute at
`http://127.0.0.1:4000`. That answers the route choice, but no numeric
aggregate spend cap was supplied. Keep generation closed while making the
accounting fail closed and removing accidental call paths.

## SubRoute observation

Read-only GET to `/health/liveliness` returned HTTP 200. Read-only GET to
`/api/active-model` returned `active_model=openrouter`, `mode=force`, policy
version 4. The default diagnostic teacher endpoint is
`http://127.0.0.1:4000/v1/chat/completions`. The earlier read-only record in
[iteration 015](iteration-015-subroute-mock-boundary-20260927.md) says the
active alias maps to OpenRouter/MiniMax M3 and its SubRoute cost fields are
null. These responses do not identify a provider selected for a generation
or provide a billed receipt. No completion POST was made.

## Changes

- `run_diagnostic_worker_arms.py` now requires a captured teacher trace before
  the runner reads its case file. It also rejects a Wrench-arm endpoint on
  port 4000 before reading cases or opening the local health fixture.
- `run_teacher_call.py` now returns a machine-readable disabled response and
  exits without parsing the request or opening an HTTP connection. This closes
  the old direct child-process route to SubRoute.
- `run_local_wrench_call.py` rejects port 4000 before invoking local model
  execution. The diagnostic runner cannot accidentally send its local arm
  through SubRoute's forced OpenRouter policy.
- Missing, malformed, boolean, fractional, negative, or non-finite token/cost
  values remain unknown. A teacher capture requires nonzero complete prompt,
  completion, and total tokens with a consistent sum, plus a nonempty returned
  model name. Mixed returned model names are rejected.
- The requested alias, returned model string, provider identity, and provider
  billing receipt remain distinct. A returned model string alone does not
  prove which upstream provider handled a request. Missing cost remains null;
  provider billing, local compute, and all-in cost remain unmeasured.

These are controls for the diagnostic package only. They do not implement an
aggregate spend ledger, validate durable provider receipts, activate a route,
or authorize a paid comparison.

## Focused verification

Command, from the repository root:

```powershell
uvx --isolated --cache-dir C:\wrench-slm-data\cache\wrench-teacher-budget-test-20260927-01 --python C:\Users\stanc\AppData\Local\Programs\Python\Python313\python.exe --from pytest==9.1.1 --no-progress pytest -p no:cacheprovider --basetemp C:\wrench-slm-data\cache\wrench-teacher-budget-test-tmp-20260927-01 -q tests/test_diagnostic_worker_arms.py
```

Result: **12 passed in 1.24 seconds**. The tests cover unknown usage and cost,
invalid capture records, missing-trace refusal before case reads, refusal of
SubRoute `:4000` on both teacher and Wrench arms, and refusal by both child
helpers before network/model execution. `git diff --check` reported no
whitespace errors. No model or provider request was made.

The isolated uvx environment fetched missing dependency files despite a
300,000-byte initial reservation. This was an underestimation of cache growth.
The subsequent storage scan counted the new files and remained far below the
50 GB ceiling; a 2,000,000-byte supplemental reservation was opened before
the remaining documentation edits. This does not retroactively correct the
initial reservation estimate. Use the existing populated pytest cache for
future focused runs and include full isolated-environment growth in estimates.

## Exact identities

Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`.

| File | SHA-256 |
| --- | --- |
| `tools/run_diagnostic_worker_arms.py` | `C6E030988E5AFF1BA45A031C651E7FA15FFE2EE0DD20D18C9B98165A628D6669` |
| `tools/run_teacher_call.py` | `EC21E18286A87BB80AE06F743ED7E82C625E2EB4F16CB0A071420CE3DEB8EF93` |
| `tools/run_local_wrench_call.py` | `7B448F977A27B5A89AC4F12DCC5B4E14E9F5F5D4C473647A77F57148D8384240` |
| `tests/test_diagnostic_worker_arms.py` | `8D755F8F2C9D8D5CD4865C5C74E41790153958A61FDBFE3BD63715AF558406E8` |

The 3,751 / 32,702 MiB free RAM sample (11.47%) and 15,199 / 16,311 MiB free
VRAM sample were taken immediately before the focused test. A later read-only
sample showed 3,219 MiB RAM free (9.84%) and 15,192 MiB VRAM free; the latest
read-only sample before closeout showed 3,717 MiB RAM free (11.37%) and
15,199 MiB VRAM free. The test loaded no model and used no GPU. The host
remains below the fit-03 start requirement of 25% free RAM; no model inference
or training is admitted.

The post-document, pre-release storage status including
`C:\Users\stanc\github\subroute` was `WITHIN_LIMIT`: 10,991,206,981 actual
bytes plus 8,403,000 active reserved bytes, projected 10,999,609,981 under
the 50,000,000,000-byte ceiling. The final check and release of this
iteration's reservations are recorded in the turn closeout.

## Interpretation and next gate

This iteration makes the measurement harness less likely to undercount
frontier tokens or pretend unknown costs are free. It does not show that the
small LoRA is useful. The research recommendation remains: deterministic
Wrench should own exact mechanical/context work; try a Wrench-specific LoRA
first as a bounded context and routing controller, with the already staged
0.8B candidate and a 2B challenger if held-out evidence shows a capacity
limit. Evaluate a coding worker separately. The public model benchmark screen
is not evidence of Wrench repository success or day-long engineering.

The 95% local verified completion, at-most-5% escalation, 95% frontier-token
savings, 95% all-in cost reduction, quality retention, and sustained
engineering requirements remain unproven. The next paid comparison still
requires a numeric aggregate USD cap, a provider-bound request path, a
pre-request reservation ledger, and durable receipt validation. Keep SubRoute
`:4000` read-only until those gates are met.
