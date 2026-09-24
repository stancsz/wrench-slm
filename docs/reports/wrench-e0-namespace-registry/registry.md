# E0 bounded namespace registry handoff

Job: `W2-E0-NAMESPACE-REGISTRY-20260924`
Nonce: `NSR-0d772c`
Baseline: `3198c6a39dcfe438f306389c881be0bd804b9ed0`

## API and bounds

`src/wrench_harness/namespace_registry.py` provides finite frozen
`NamespaceDescriptor` and `OperationDescriptor` inputs plus
`NamespaceRegistry.discover(query=None)` and `lookup(namespace_id,
operation_id)`. Discovery returns sorted namespace/operation identifiers and
summaries only. Schema bodies are deferred until lookup, which returns a deep
immutable JSON-shaped mapping and SHA-256 of canonical JSON. Unknown namespace
and operation IDs have distinct statuses.

Visibility is metadata only. There is no execute, permission, routing, shell,
provider, or model surface. The caller supplies the complete descriptor set;
the registry does not scan or discover environment state.

Bounds: 64 namespaces, 128 operations per namespace, 512 operations total,
128 characters per identifier, 512 UTF-8 bytes per summary, 32 KiB canonical
JSON per schema, 256 KiB aggregate canonical schemas, 64 levels of schema
depth, and 10,000 schema nodes. Invalid/duplicate identifiers, non-JSON
values, cycles, and over-limit inputs fail closed.

## Verification

Focused Windows command used Python 3.11 with temp paths below the job scratch
root, bytecode and pytest plugin autoload disabled, and the existing pytest
dependency directory on `PYTHONPATH`:

```powershell
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -p no:cacheprovider tests/test_namespace_registry.py
```

Result after review-requested depth, node, traversal, and string-allocation
bounds was `10 passed`. Focused `git diff --check` passed. Final storage status
before commit was `WITHIN_LIMIT`: actual 590,395,608 bytes, active reservation
20,000,000 bytes, projected 610,395,608 bytes, no checker errors. C: had
186,307,579,904 bytes free. No packages were installed; no commit was created.

## Independent review

Job `W2-E0-NAMESPACE-REGISTRY-REVIEW-20260924`, nonce `NSRR-e3c41f`, accepted
the final module and tests with no remaining findings. The review checked
deterministic discovery, deferred immutable lookup, bounded traversal and
string allocation, and absence of permission/execution APIs. The reviewer did
not run tests. E0 remains incomplete.
