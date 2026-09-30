# Iteration 174: independent review of the scorer trainer pin

Assignment: `WRENCH-QWEN35-4B-DEV-EVAL-REVIEW-ITER174-20260929`  
Nonce: `7f93b727-9cec-46cb-a19e-eac4d8a81735`

## Verdict

**PASS** for the exact-hash Iteration 173 source repair. The corrected
`TRAINER_SHA` is the pinned trainer digest, and the one-byte correction
reconstructs the prior evaluator's exact SHA when reversed. The fit manifest
has its pinned digest and its `runner_sha256` equals the trainer digest. The
preflight/full-score and other boundaries reviewed in Iteration 172 remain
present. This static pass is **not permission to run preflight or scoring**.

## Identity checks before and after review

HEAD before and after: `af01304824f079a64b6c3902397a2034b843511a`.

| Item | SHA-256 before | SHA-256 after |
|---|---|---|
| Current scorer | `5B92E5EC7A325B82C265FB082350EF3664361229B850F70B79F31C75A2D255AF` | `5B92E5EC7A325B82C265FB082350EF3664361229B850F70B79F31C75A2D255AF` |
| Trainer | `1D7CCBB42AF72C41066D52A4CB6448D000C07D395657CAE475DAAA79363B49B5` | `1D7CCBB42AF72C41066D52A4CB6448D000C07D395657CAE475DAAA79363B49B5` |
| Fit manifest | `D39A9335FBDD107390F053F2460A34845CE3EFE2EA473F73060C6EAE85278F0E` | `D39A9335FBDD107390F053F2460A34845CE3EFE2EA473F73060C6EAE85278F0E` |
| Evaluation protocol | `328CDD2A156288D25F1665C10DC46DB2FD84D0D009F294D2D10185839A9D2CA6` | `328CDD2A156288D25F1665C10DC46DB2FD84D0D009F294D2D10185839A9D2CA6` |
| Iteration 173 repair report | `6BF04572B9B115A6B8479D758F9B7E89071E09499514CAA4EDDE96F35A0A21FB` | `6BF04572B9B115A6B8479D758F9B7E89071E09499514CAA4EDDE96F35A0A21FB` |
| Iteration 172 review baseline | `AB3717714239BC1B552A17C99FFDDF8AB8DB3DBAF5E545DE7AFDAE1A1BCE0E1E` | `AB3717714239BC1B552A17C99FFDDF8AB8DB3DBAF5E545DE7AFDAE1A1BCE0E1E` |

The scorer's `TRAINER_SHA` constant is
`1d7ccbb42af72c41066d52a4cb6448d000c07d395657cae475daaa79363b49b5`.
The fit manifest's `runner_sha256` is the same value. Its SHA-256 is
`D39A9335FBDD107390F053F2460A34845CE3EFE2EA473F73060C6EAE85278F0E`.
The scorer also hashes the trainer file against this constant in
`load_fit_receipt()` and repeats the trainer/protocol check in `main()`.

To independently compare the current evaluator to the stated prior digest
`14ec4c0939e8135a14d31a9a93e51de6df01da658e6f42a3369967e94c4c2d05`, I
read the scorer bytes and computed candidate digests after deleting one `b`
from the corrected trainer-SHA literal. Deleting one of the two adjacent `b`
bytes reproduces that prior digest exactly. This confirms a one-byte insertion
is the only difference from the prior source represented by that digest; no
source file was modified for this check.

## Boundary review

- The frozen fit manifest digest is checked before parsing. The scorer checks
  the trainer file digest and requires manifest `runner_sha256` to equal the
  same trainer digest. No fit manifest or trainer change is part of this
  repair.
- The corrected scorer digest and evaluation-protocol digest are bound into
  preflight receipts. Full scoring verifies those identities, the fit
  manifest, model/data/prompt hashes, runtime/GPU identity, reservation,
  sealed prediction hashes, and resource samples.
- The Iteration 172 gate remains: full scoring parses both sealed preflight
  rows, verifies matching example identity and both-arm generation success,
  rejects failures, then loads the prompt projection and model runtime.
- Prompt-only input and delayed oracle opening remain ordered as reviewed:
  generation receives prompt messages; both prediction files are sealed
  before the oracle projection is opened. No held-out payload path was read.
- The scorer remains local-only. The reviewed paths contain no provider or
  SubRoute call, credential access, adapter activation, or permission to
  mutate active Wrench state. The candidate remains inactive.
- Existing protocol limits still apply: cooperative generation time budget
  with an externally enforced hard timeout, disclosed path-check TOCTOU
  limitation, and synthetic-dev-only interpretation.

## Commands and resource sample

Read-only identity and inspection commands included:

```powershell
git rev-parse HEAD
Get-FileHash -Algorithm SHA256 <assigned scorer, trainer, protocol, reports and fit manifest>
Get-Content <bounded scorer and report sections>
rg -n "TRAINER_SHA|FIT_MANIFEST_SHA|runner_sha256|preflight_prediction_issues" <assigned files>
```

The prior-source check read the scorer bytes and computed hashes of
one-byte-deletion candidates in memory; it did not write or execute source.
At the resource sample, system RAM free was 24.29% (8,134,988 KiB of
33,486,624 KiB), and the pinned RTX 5060 Ti had 15,185 of 16,311 MiB free.
No model workload was started. These readings are not admission for a later
job.

The assigned review storage reservation is 50,000 bytes. This report is
within that bound. No preflight, scoring, or execution authorization is
included.
