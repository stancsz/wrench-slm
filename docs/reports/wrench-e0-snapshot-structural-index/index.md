# E0 snapshot-backed structural index handoff

Job: `W2-E0-SNAPSHOT-STRUCTURAL-INDEX-20260924`
Nonce: `SSI-5b614d`
Baseline: `06210190ce6ea3ba4c004f7ca3486293c2485864`

## API and behavior

`src/wrench_harness/snapshot_structure.py` exposes
`build_snapshot_symbol_index(root, snapshot, paths)` and
`query_snapshot_symbols(index, query, limit=...)`. The build API reads only
the caller's bounded path list through `retrieve_exact`, strictly decodes UTF-8,
then uses the existing read-only `build_symbol_index` parser. Python AST
declarations and its lexical fallback are preserved. Any retrieval, text,
parser, count, or output failure returns an explicit status and no partial
index.

Every file and symbol candidate carries the snapshot hash, exact source hash,
normalized path, parser/language, and line range. File/symbol order and
canonical index SHA-256 are deterministic. Candidate queries use the existing
read-only lexical `lookup_symbols` helper and return structural references
only. No scan, write, persistence, context mutation, model/provider call, or
execution is added.

Bounds are 16 files, 64 KiB per file, 512 KiB aggregate bytes, 4 MiB serialized
output, 4,096 symbols, 32 returned candidates, and 256 query characters.

## Verification

Focused Windows command used Python 3.11 with `TEMP`, `TMP`, and `TMPDIR` set
to `C:\wrench-slm-data\tmp\W2-E0-SNAPSHOT-STRUCTURAL-INDEX-20260924`, bytecode
and pytest plugin autoload disabled, and the existing pytest dependency
directory on `PYTHONPATH`:

```powershell
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -p no:cacheprovider tests/test_snapshot_structure.py
```

Result: `10 passed`. Scoped `git diff --check` passed. Storage status was
`WITHIN_LIMIT`: actual 590,488,754 bytes, active reservation 20,000,000 bytes,
projected 610,488,754 bytes, no checker errors. C: had 186,300,375,040 bytes
free. No commit was created.

## Final acceptance

Independent review job `W2-E0-SNAPSHOT-STRUCTURAL-INDEX-REVIEW3-20260924`,
nonce `SSIR3-699d33`, accepted the final four-file implementation after two
rounds of boundedness repairs. The first review required validating public
index handles and enforcing output limits before encoder allocation. The
follow-up required exact built-in query and limit types to prevent hostile
subclasses from bypassing caps. Both findings were fixed and covered by
regression tests.

Final focused verification: `21 passed`; scoped `git diff --check` passed.
Storage remained `WITHIN_LIMIT` at 590,504,998 bytes actual plus 20,000,000
reserved, or 610,504,998 projected; C: had 186,293,911,552 bytes free.
Acceptance applies to this component slice only. It does not complete E0.

## Query argument type repair

Job: `W2-E0-SNAPSHOT-STRUCTURAL-INDEX-FIX2-20260924`  
Nonce: `SSIF2-c8a302`  
Source hash at repair start: `F3190350750CAE254C7D090F6CDB0A2D6264D13E772F469D7E9EFA5FB9F87173`

`query_snapshot_symbols` now requires exact built-in `str` and `int` types
before calling `len` or performing limit comparisons. Tests use a `str`
subclass whose `__len__` raises and an `int` subclass whose comparison raises;
both are rejected through their explicit statuses without invoking those
methods.

Focused verification reran the named test file with Python 3.11 and the
existing cached pytest dependencies: `21 passed`. Scoped `git diff --check`
passed. No commit was created.

## Bounded-handle review repair

Job: `W2-E0-SNAPSHOT-STRUCTURAL-INDEX-FIX-20260924`
Nonce: `SSIF-24e7b1`
Baseline at repair start: `06210190ce6ea3ba4c004f7ca3486293c2485864`

Before query expansion, the module now validates exact immutable index/file/
symbol record types and tuple containers, file and symbol count caps, bounded
text and line values, valid lowercase SHA-256 fields, canonical safe path
components and Windows case-fold path uniqueness, and cross-field path/source/
snapshot/parser/language identities. It recomputes the canonical index
serialization and checks its size and digest. Any mismatch returns
`INVALID_INDEX` with an empty candidate tuple.

Canonical serialization now performs a bounded shape walk and exact JSON byte
size preflight, including control-character escaping, before invoking the JSON
encoder. This prevents an oversized escaped output chunk from being allocated
before the byte cap is enforced. Query serialization has its own 4 MiB cap.
Regression tests cover malformed and forged handles, escaped-output overflow,
and query-output overflow.

Focused Python 3.11 command used the active structural-index reservation, with
`TEMP`, `TMP`, and `TMPDIR` at the approved Wrench temp directory, bytecode and
pytest plugin autoload disabled, and the cached pytest dependencies:

```powershell
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -p no:cacheprovider tests/test_snapshot_structure.py
```

Result: `20 passed`. Scoped `git diff --check` passed. Final storage status:
`WITHIN_LIMIT`, actual 590,503,252 bytes, active reservation 20,000,000 bytes,
projected 610,503,252 bytes, no checker errors; C: had 186,294,267,904 bytes
free. No commit was created.
