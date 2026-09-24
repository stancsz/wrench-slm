# E0 supplied-manifest baseline accounting

- Date: 2026-09-24 (America/Edmonton)
- Job: `W2-NS-E0-BASELINE-ACCOUNTING-20260924`
- Nonce: `E0BA-6F31`
- Base HEAD: `c64eb65a4d6104caf2cb36594ba9cb46b7eaf411`
- Status: implemented, independently reviewed, and committed with this report

## Receipt boundary

The content-free `wrench.e0.baseline-accounting.v2` receipt joins a root-bound
OpenCode project snapshot, its supplied-manifest inventory receipt, the
route-owned synthetic composition and terminal fixture result, the complete
seven-field post-insertion hook projection, and the lowered fixture request.
The builder rebinds the configured root and rebuilds the inventory before it
accepts the supplied inventory receipt. It rejects source changes, root
replacement, forged or stale inventory receipts, projection mismatches,
unaccounted inventory statuses, and inconsistent terminal/composition joins.

The receipt keeps different accounting scopes separate:

- `accounted_snapshot_manifest_entries` and
  `unaccounted_snapshot_manifest_entries` partition only entries in the
  already selected snapshot manifest. For a READY receipt all supplied
  manifest entries are accounted and none are left unaccounted.
- `context_candidate_count` and
  `context_selected_candidate_order_sha256` bind the existing structural
  candidate summary. Exact context-selected and context-omitted candidate
  counts remain null because the composition receipt does not expose them.
- Exact-read attempts, successes, returned bytes, and status counts come from
  the freshly rebuilt inventory receipt.
- Synthetic envelope SHA-256, UTF-8 byte count, character count, and synthetic
  tokenizer count are recorded separately from lowered fixture request-body
  SHA-256 and bytes.
- `enrolled_omission_count` is null because this interface receives no
  complete enrolled-path inventory.

## Verification

The focused test module contains one end-to-end synthetic fixture test. It
passed when directly invoked through the existing Python 3.11 environment.
The fixture exercises route preparation, a complete supplied-manifest
inventory, terminal stream completion, and receipt verification. It also
checks non-ASCII byte/character accounting; altered and rehashed contradictory
inventory receipts; post-inventory source mutation; root replacement;
projection mismatch; and rehashed receipts with zero, negative, or boolean
candidate counts. `git diff --check` passed. The `pytest` package is not
installed and was not installed.

Independent read-only review returned PASS after the inventory/context
accounting labels and standalone verifier count constraints were corrected.
Source SHA-256: `A1AF1C4A8E62702BB994619E15575AD2EAA32DB8F9E5A50954B9173AF65283B2`.
Test SHA-256: `639854D93F45FD074F30B008F0A36589F20D08D8A2B64529766E4A357BEEA265`.

## Limits

Inventory completeness applies only to the paths present in the supplied
snapshot manifest. It does not prove the manifest covers the entire enrolled
repository or filesystem. Root rebind, inventory rebuild, and later snapshot
reads are not one atomic filesystem transaction. These receipts are
caller-held, content-free joins, not authenticated runtime observations. The
fixture does not establish actual OpenCode hook execution or dispatch veto,
provider/model routing, provider/tool/retry/cost accounting, final serializer
equivalence, or tokenizer parity. The exact-token gate remains unavailable;
E0 exit criteria remain open.
