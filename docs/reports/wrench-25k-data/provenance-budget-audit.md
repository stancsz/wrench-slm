# Wrench 25k provenance and budget audit

Date: 2026-09-23
Job: W25K-PROVENANCE-AUDIT-20260923-B
Nonce: WS25K-17C2
Repository: `C:\Users\stanc\github\wrench-slm`
Expected HEAD: `87909b958ac252b0b3b2cc720a300babb26b733d`

## Scope and method

Read the active root working agreement, North Star, 25k data goal, Phase 447 corpus README, and Phase 447 approval, pilot, quarantine, source-assessment, cross-audit, and independent-audit metadata. Ran the repository storage-budget checker in `status` mode. Checked mounted filesystem roots and SHA-256 of the local approval/pilot/audit metadata. No external research, source payloads, credentials, private prompt bodies, network calls, model requests, downloads, training, or data generation were accessed or performed. The working tree had pre-existing user changes at inspection time; this report is the only file written by this audit.

## Authorization evidence

- `minimax-data-approval.json` records human approval on 2026-09-23 for MiniMax via OpenRouter, model `minimax/minimax-m3`, with a USD 100 total corpus inference cap and synthetic prompts/fixtures only. It sets no fallback, one pilot request, at most 128 output tokens, zero automatic retries, no hidden reasoning retention, and requires usage/cost evidence. This authorizes bounded corpus inference within those constraints, not training or publication.
- The approval metadata says a corpus-specific child receipt must be bound to task hashes and the route before paid requests. A local cost ceiling, request maximum, single-request concurrency, bounded retries, and circuit breaker are required. The child receipt and request-level reserve evidence were not present among inspected local receipts. No inference job should be considered admitted yet.
- `minimax-data-pilot-receipt.json` reports one HTTP 401, no model response, no usage receipt, and `UNKNOWN_NO_PROVIDER_USAGE_RECEIPT`; it explicitly reports no rows admitted. There is no basis to count the charge as zero. Reconcile this request with provider billing before a new paid dispatch. The credential value was not read.
- The goal and North Star approve `C:\wrench-slm-data` as the large-artifact root and state a USD 100 corpus ceiling. Neither is permission to train the model or publish data. External publication requires concrete rights/artifact review and a human decision.
- AGENTS.md requires a fresh `status` and peak-byte reservation before each artifact-producing job, with all active Wrench artifacts and reservations below 100,000,000,000 bytes. This audit was metadata-only, so no reservation was needed for the audit itself.

## Storage evidence

At audit time, `python tools/check_wrench_storage_budget.py status` returned `WITHIN_LIMIT`: actual 508,213,412 bytes, active reservations 0, projected 508,213,412 bytes, and 99,491,786,588 bytes of reported headroom. It reported zero bytes at `C:\wrench-slm-data`, 6,007 bytes in the configured Hugging Face cache, and included the listed Wrench repositories and temporary source in its total. This is a point-in-time checker result, not an OS quota or guarantee that a future peak fits.

`C:\wrench-slm-data` is mounted and contains named `datasets` and `logs` roots (including the `wrench-25k` paths). D: is not mounted on this host, consistent with the active goal's C: relocation. Phase 447's older quarantine and draft receipts point to D: paths, so those payloads and their hashes could not be independently rechecked from this host. The local metadata says those old artifacts were hash-checked/read-only; treat that as historical reported evidence, not a current independent verification.

Before the next paid pilot or any artifact-writing job, rerun `python tools/check_wrench_storage_budget.py status`, calculate a bounded peak including request/output files, logs, cache growth, temporary files, and any copies that coexist, then reserve exactly that peak with the checker. Keep the reservation active through job completion and account for files before release. Use `--include-root` for any Wrench artifact root outside the repository and approved data root. The current status alone does not reserve capacity.

## Provenance, rights, and consent findings

- Phase 447 reports zero accepted rows. The 350-row and 52-row authored batches are review candidates only: no human review completion or runtime/oracle validation; contract/semantic defects remain; none pass the production corpus gate. The supplemental cross-validation receipt reports static integrity checks, not training acceptance.
- Public-source assessment admits zero rows. It describes possible task-fit/rights limitations across candidate sources; the general tool-call bundle is quarantined with license status pending. No external rows should be admitted based on those summaries.
- The 397-row real-workflow capture is not training-authorized by the evidence inspected. Permission to inspect in the prior conversation does not establish third-party rights or row-bound training consent. Metadata reports prompt/context content, a narrow credential-pattern redactor, no independent full-file PII review or source-hash-bound redaction receipt, and email-shaped review flags for 199 rows. Phase 448 joins are incomplete and do not establish action-family frequencies, independent verifier results, final task correctness, provider cost, or complete retry/correction accounting. Do not expose or use its raw content for this audit or training.
- MiniMax output rights, retention, and redistribution terms for the actual OpenRouter route remain unresolved. The North Star requires route/provider pinning and rights review; displayed public pricing is not a hard cap. Before retaining or publishing model output, establish applicable route terms and a concrete release rights review. Keep only approved visible structured proposals and required provenance; no hidden reasoning.
- Row-level consent/license status, human-review receipt, oracle correctness, duplicate/split isolation, and source hash evidence are mandatory corpus fields/gates. They are not satisfied merely by an aggregate count or human approval of the provider cap.

## Sealed-evaluation exposure

Phase 447 reports broad worker search output included evaluation rows marked `final`, with exact paths unavailable. The `read_lines` draft shard also encountered historical calibration material. The cross-audit says possible sealed-final exposure is unresolved and the current final set cannot be treated as untouched evaluation evidence. The independent audit records overall `sealed_final_content_read: unresolved`; its validator isolation checks do not resolve what earlier broad searches displayed. Never send the current sealed-final prompts to MiniMax during construction. Before claiming a clean final evaluation, either establish source-level exposure resolution or construct a new isolated final split after freezing source generators, task families, scoring, and candidate; keep it inaccessible during train/dev construction and verify split/duplicate leakage.

## Earliest safe next action

1. Resolve the failed pilot's charge status with the provider billing evidence and restore/refresh the approved route without exposing credential values. Confirm route terms, retention, and output-use rights for MiniMax through OpenRouter.
2. Prepare and review a hash-bound corpus child receipt containing the exact synthetic fixture/task hashes, pinned route/model, one-request maximum, maximum input/output usage and worst-case charge, remaining USD cap after reconciliation, zero-retry policy, local cost circuit-breaker settings, permitted output fields, and intended output/log/cache paths. Do not dispatch until the receipt and hard local guard are in place.
3. For the pilot, first run storage `status`, reserve its bounded peak, and check RAM/VRAM headroom per AGENTS.md. Use only synthetic fixtures, never current sealed-final prompts. On any missing usage receipt after dispatch, debit the full pre-reserved amount and stop rather than retrying. Record request usage, cost, response hash, oracle result, and storage accounting; measure cost per accepted row before scaling.
4. In parallel before scaling toward 25,000, define/review fixture generators and executable oracles, row-level provenance/review receipts, group-isolated split generation, and an independently protected replacement sealed-final set. Resolve the missing approved redacted real-workflow evidence before making traffic-frequency claims or allocating the 9,600 observed-workflow training rows. Synthetic rows may support authored coverage, but must not be represented as measured production frequency.

The evidence does not currently support starting full corpus generation, training, or publication. The next provider request is specifically blocked by unresolved charge reconciliation, absent task-bound child receipt/guard evidence, route-rights review, and authentication.

## Files and hashes inspected

Local SHA-256 values at audit time:

- `phases/phase-447-wrench-training-data-corpus/minimax-data-approval.json`: `6180852F0FFEF21537320AB960C01F5815BA36727C137ADA4CEF580F5F42BDD6`
- `phases/phase-447-wrench-training-data-corpus/minimax-data-pilot-receipt.json`: `5B04BA313A357AC413330DD312DA3C284FE0B61675E42FA2A75D1B5BF3B6E841`
- `phases/phase-447-wrench-training-data-corpus/independent-audit-receipt.json`: `620C54AFE83157032C434A1037A81C1268EE69ABFDFEDAB17BFDB4A2E8563877`
- `phases/phase-447-wrench-training-data-corpus/draft-batch-cross-audit.json`: `6D5DAB900EAC91BC0594AD9E2A8BB2A38F0F3CA15D320C4B363AFC0C55DB9546`
- `phases/phase-447-wrench-training-data-corpus/public-source-assessment.json`: `CF0C76CE18F1C558FDAD29572F61E7B2B779A7686D83413F5AA02C1C65608BA5`

These hashes identify the local metadata files only; they do not authenticate unavailable external source payloads or prove the factual claims inside those receipts.
