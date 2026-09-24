# E0 omission and stale-miss accounting

- Date: 2026-09-24 (America/Edmonton)
- Job: `W2-NS-E0-OMISSIONS-STALE-MISS-20260924`
- Nonce: `E0OSM-63B1`
- Base HEAD: `d367083d517347ccf016235355fdac9728b29253`
- Status: synthetic accounting slice implemented and independently reviewed

## Change

The offline composition receipt now carries content-free selected-evidence and
omitted-evidence counts, omission-reason counts, and retrieval-miss counts by
status. The omitted-evidence and retrieval-miss denominators remain separate,
even when a source condition contributes to both. Labels are finite allowlists;
paths, evidence IDs, source text, and prompts are not copied into these fields.

The baseline accounting receipt advances to schema v3. Complete receipts carry
the preparation outcome identity, selection and omission counts, and the
synthetic exact-token status. A source-miss result may instead produce an
explicitly incomplete receipt after a fresh supplied-manifest inventory check.
In that variant, no request, lease, insertion, projection, request body, token
count, or terminal outcome is claimed. The fixture confirms active pins are
released and no request is issued on this path.

The standalone validators bound counts, distinguish complete and incomplete
variants, reject fields that should be unavailable in an incomplete result,
and reconcile stale-miss and inventory outcomes by aggregate counts. They do
not join individual stale misses to individual changed manifest entries: the
existing content-free inventory receipt exposes aggregate/page information,
not per-source status identities. Enrolled omissions also remain unavailable
because this interface accounts only a supplied snapshot manifest.

## Verification

The focused `test_e0_offline_request_composition.py` functions passed (14/14),
and `test_e0_baseline_accounting.py` passed (2/2), invoked directly through the
existing Python 3.11 environment. `git diff --check` passed. An independent
read-only reviewer passed the final four implementation/test file hashes.
No client, provider, localhost endpoint, prompt, or inference was used.

## Limits

This remains authored synthetic evidence. It does not establish complete
enrollment coverage, authenticated runtime observations, OpenCode dispatch
denial, final provider routing, exact serializer or tokenizer identity,
downstream task utility, or E0 acceptance. The synthetic exact-token gate stays
unavailable. See the [E0 experiment criteria](../../northstar/V2_EXPERIMENT.md)
and [previous supplied-manifest accounting report](supplied-manifest-baseline-accounting.md).
