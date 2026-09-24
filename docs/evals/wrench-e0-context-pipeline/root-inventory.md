# Policy-scoped root inventory evaluation

**Final result: PASS for bounded synthetic inventory and snapshot-admission mechanics.** This component result does not accept E0 or claim repository-wide coverage.

The initial `tests/test_snapshot_root_inventory.py` run passed **11 tests**
with **2 symlink skips** on Windows Python 3.11.16. Independent review found
four policy-validation defects: a recomputed self-hash could admit a
record outside declared scopes; exclusions could cover a scope; Windows path
case handling was inconsistent for scope overlap and exclusions; and a
truncation guard was duplicated. Those findings mean the initial green tests
were insufficient for policy admission.

Correction `W2-NS-W0-ROOT-INVENTORY-FIX1-20260925` (nonce
`ROOTINV-FIX1-0F8C`) re-ran the focused suite: **17 passed, 2 skipped** on
Windows Python 3.11.16. The skips are the two symbolic-link fixture cases;
Windows-only case-variation scope and exclusion regressions passed. Added
coverage proves `create_snapshot_from_inventory` rejects an out-of-scope row
even after both public self-hashes are recomputed, and rejects exclusions
equal to or above a scope. The duplicate truncation guard was removed.

Subsequent independent review found that a caller could omit an in-scope file,
recompute the unkeyed manifest and receipt hashes, and still pass structural
validation. It also requested an accounting invariant for records and
exclusions relative to observed entries. FIX2
(`W2-NS-W0-ROOT-INVENTORY-FIX2-20260925`, nonce `ROOTINV-FIX2-84B1`) adds a
fresh full inventory under the same `SourceRootBinding` and policy at snapshot
admission. Admission requires the fresh receipt to be complete and exactly
equal to the supplied receipt before snapshot creation. The regression removes
one of two in-scope records, recomputes both hashes, confirms the forged
receipt remains structurally valid, then confirms fresh inventory rejects it.
Receipt validation also enforces `record_count + excluded_entries <=
entries_seen`.

FIX2 focused verification passed **19 tests, 2 skipped** on Windows Python
3.11.16; the skips remain the two symlink-creation cases unavailable on this
host. `git diff --check` passed. After the report-only FIX3 summary correction,
independent read-only review returned PASS. The reviewer did not rerun tests;
the 19/2 result is the focused FIX2 run.

The inventory binds its root location/object, normalized policy, and canonical
manifest. Snapshot admission requires a complete receipt, checks exact
scope-membership and exclusion constraints even after plain hashes are
recomputed, and compares a freshly enumerated complete receipt before it
rechecks path, size, and content digest. Every observed error or resource cap
makes the receipt incomplete; callers cannot pass an incomplete receipt to
snapshot creation. Exclusions are explicit, hashed policy and observed opaque
boundary entries are counted. Completeness means only that traversal did not
observe an error or cap inside declared scopes at observation time. Fresh
enumeration catches omissions that exist when admission runs, but the walk and
subsequent snapshot reads are not one atomic filesystem transaction. External race cases,
symlink traversal on a host that permits fixture creation, filesystem-wide
completeness, runtime use, task utility, authenticated measurements, and
overall E0 remain unproven.

No real repository payload, client, gateway, provider, model, network, or
external data is involved. The active Wrench storage reservation was 20 MB;
current aggregate storage remained well below the 50 GB ceiling. The exact
before/after storage readings, resource headroom, command, repository status,
and file SHA-256 values are retained in the implementation report and parent
job receipt.
