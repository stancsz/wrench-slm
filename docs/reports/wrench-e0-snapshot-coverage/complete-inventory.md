# Bounded snapshot inventory aggregator

Job: `W2-NS-E0-INVENTORY-AGG-20260924`
Nonce: `INVAGG-942C`

## Contract

`build_snapshot_inventory_receipt` takes a validated `SourceSnapshot` and its
matching `SourceRootBinding`. The snapshot's canonical, sorted `sources` tuple
is the supplied manifest. The implementation checks the root binding, divides
the tuple into fixed pages of 16 entries, and calls the existing exact-read
coverage primitive for each page. It rejects malformed snapshots, noncanonical
or duplicate manifest rows, and a mismatched or changed root. A source changed
after snapshot creation is retained as a `stale` status and makes the receipt
incomplete.

Each page digest binds the snapshot and root identities, page index and path
bounds, coverage receipt digest, and exact status totals. An ordered SHA-256
chain binds page order. The final receipt reports status and read totals and is
bounded to 64 KiB. The focused test recomputes the ordered chain recurrence
from all page hashes and confirms reversing page order changes the chain.
Reordering the input paths to `create_snapshot` produces the same canonical
snapshot and inventory receipt.

The receipt accounts only for the entries in the caller-supplied snapshot. It
does not enumerate an underlying directory or establish that the manifest
includes every file in a repository or other source tree. The root identity is
replacement detection, not authentication or a filesystem transaction. This
is offline synthetic verification, not runtime, utility, or E0 acceptance.

## Verification

On Windows with cached pytest 8.4.2 and Python 3.11.16, this PowerShell
invocation passed **12 tests in 1.98 seconds**. The run used existing cached
test dependencies; no package was installed.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:PYTHONPATH='C:\Users\stanc\github\wrench-slm\src;C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages'
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -p no:cacheprovider --basetemp='C:\wrench-slm-data\tmp\W2-NS-E0-INVENTORY-AGG-20260924' tests/test_snapshot_coverage.py
```

`git diff --check` passed with only the repository's LF-to-CRLF working-copy
warnings. The approved scratch tree contains 1,399 bytes. Storage remained
within the 50 GB limit. System memory was 13,821,612 KiB free of 33,486,624
KiB and VRAM was 15,222 MiB free of 16,311 MiB before the final run.

Source SHA-256: `01D9FAD47BF6768FC9E7AF35A51FE7A05E607685AB90ED1F6C55F14957BCCD70`.
Test SHA-256: `0A9DBD18CEABED1ADEC336C93A33E2AAD85640B356853088ED6BDF7C0410363A`.
The report and evaluation hashes are included in the handoff receipt.
