# Policy-scoped root inventory

Job `W2-NS-W0-ROOT-INVENTORY-20260925`, implementation nonce
`ROOTINV-5C27-IMPL-9A4E`, branch `development`, base
`dcc476b9c6e8720d828789dcb0d29cb6f6662016`.

`src/wrench_harness/snapshot_root_inventory.py` adds a caller-authored policy
of disjoint relative directory scopes, optional path-prefix exclusions, and
explicit entry/depth limits. It normalizes and sorts policy paths and manifest
rows, counts encountered entries and exclusion boundaries, caps metadata,
manifest size, file size, aggregate bytes, and receipt output, and emits
content-free error codes for unsafe, missing, changed, or unreadable entries.
Static links and reparse points are rejected. Each file is read through the
existing stable, root-bound snapshot reader. The receipt binds the normalized
resolved root path, root-location digest, retained root-object identity,
policy, and canonical sorted file manifest. Before snapshot creation,
`create_snapshot_from_inventory` re-enumerates the same bound root under the
same policy and requires the fresh receipt to be complete and exactly equal
to the supplied receipt. It then re-reads the manifest paths through the
existing `create_snapshot` path and compares paths, sizes, and hashes. The
inventory walk and snapshot reads are separate filesystem operations, so a
concurrent writer can still race the interval; this is not an atomic snapshot.
Structural validation additionally requires every record to be a strict
descendant of exactly one declared scope and outside every exclusion. This
prevents recomputed plain receipt hashes from admitting an in-root path outside
the declared policy. Overlapping scopes and exclusions that equal or contain
a scope are rejected. Windows scope-overlap and exclusion matching is
case-insensitive.

Limits are 512 observed entries, depth 32, 256 files, 256 KiB per source,
4 MiB aggregate source bytes, 64 policy items, 16 KiB canonical policy
metadata, 256 bounded error rows, and 512 KiB receipt output. Observed
exclusion boundaries are opaque and counted once; their descendants are not
walked. Exclusions are part of the receipt policy digest and do not by
themselves make a receipt incomplete. Errors and cap exhaustion are reported
and make it incomplete.

`complete` is scoped to the declared policy at observation time. Directory
enumeration is path-based, revalidates observed directory/root identity, and
is not atomic against external writers. The receipt does not cover paths
outside its scopes or make a whole-repository completeness claim.

## Verification

Focused Windows Python 3.11.16 invocation, using the existing cached pytest
package, bytecode disabled, plugin autoload disabled, cache provider disabled,
and basetemp under this job's reserved scratch:

```powershell
$env:PYTHONPATH = 'C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages;src'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe -B -m pytest -q -p no:cacheprovider --basetemp C:\wrench-slm-data\tmp\W2-NS-W0-ROOT-INVENTORY-20260925\pytest-fix2 tests\test_snapshot_root_inventory.py
```

Initial implementation result: **11 passed, 2 skipped**. Both skips were
synthetic symbolic-link creation tests because this Windows account/filesystem
did not permit creating links. Independent review found four
policy-validation defects. Correction `W2-NS-W0-ROOT-INVENTORY-FIX1-20260925`
(`ROOTINV-FIX1-0F8C`) adds structural scope and exclusion validation, rejects
exclusions equal to or above declared scopes, applies Windows case-insensitive
path comparison for overlaps/exclusions, removes the duplicated truncation
guard, and adds regression cases. FIX1 verification passed **17 tests with 2
symlink-creation skips**. Subsequent independent review found that an
in-policy but omitted record could still be self-rehashed, prompting FIX2.

FIX2 (`W2-NS-W0-ROOT-INVENTORY-FIX2-20260925`, nonce
`ROOTINV-FIX2-84B1`) re-enumerates the same root binding and policy during
snapshot admission and requires a fresh complete receipt to equal the supplied
receipt. It also validates that record and exclusion counts do not exceed
observed entries. A regression removes one of two in-scope rows, recomputes
both public hashes, confirms structural validation alone accepts the
internally consistent receipt, then verifies fresh enumeration rejects it.
The FIX2 focused run passed **19 tests with 2 symlink-creation skips**.
After a report-only FIX3 summary clarification, independent read-only review
returned PASS; the reviewer did not rerun tests. Enumeration and subsequent
snapshot reads are separate operations; concurrent filesystem changes can
still race this interval, so the check is not an atomic snapshot. No packages
or data were installed/downloaded.

## Changed paths

- `src/wrench_harness/snapshot_root_inventory.py`
- `tests/test_snapshot_root_inventory.py`
- `docs/goal/wrench-e0-context-pipeline/GOAL.md`
- `docs/reports/wrench-e0-context-pipeline/root-inventory.md`
- `docs/evals/wrench-e0-context-pipeline/root-inventory.md`
