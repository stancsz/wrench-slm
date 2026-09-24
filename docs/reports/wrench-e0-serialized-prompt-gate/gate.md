# E0 serialized prompt budget gate handoff

Job: `W2-E0-SERIALIZED-PROMPT-GATE-20260924`
Nonce: `SPG-349b21`
Baseline: `32ca951abe9c2818eb6e988a22ffd4b95160cf0a`

## API and behavior

`src/wrench_harness/prompt_compiler.py` provides `compile_prompt(...)`. The
caller supplies a full ContextLedger assembly receipt, all base chat messages
(including fixed instructions and deferred schemas), an insertion position,
actual-target serializer and tokenizer-count callbacks, explicit callback IDs,
a hard token budget, and required evidence IDs.

The gate validates a full assembly receipt and propagates selected IDs and
omission reasons. If a required ID is absent from selected evidence, it returns
the omission reason and does not serialize. Otherwise it inserts the assembled
text, serializes the complete final messages once, validates serialized type
and byte bounds, invokes the tokenizer counter on that serialized output, and
returns a routable prompt only when the exact reported count is within budget.
The receipt binds session hash, selected/omitted evidence, prompt SHA-256,
count, budget, serializer/tokenizer IDs, serialized bytes, and status.

All test callbacks are fixture-only. This is a contract gate, not a provider
call or proof that callback identities match a production runtime. A default
word estimate is not claimed to be an exact tokenizer count.

## Verification

Focused Windows command used Python 3.11 with `TEMP`, `TMP`, and `TMPDIR` set
to `C:\wrench-slm-data\tmp\W2-E0-SERIALIZED-PROMPT-GATE-20260924`, bytecode
and pytest plugin autoload disabled, and the existing pytest dependency
directory on `PYTHONPATH`:

```powershell
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -p no:cacheprovider tests/test_prompt_compiler.py
```

Result after review-requested bounded traversal and mutation-boundary repairs
was `13 passed`. Scoped `git diff --check` passed. Final storage status before
commit was `WITHIN_LIMIT`: actual 590,461,986 bytes, no active reservation,
projected 590,461,986 bytes, no checker errors. C: had 186,300,551,168 bytes
free. No packages were installed; no commit was created.

The input preflight accepts only built-in JSON containers and checks node,
depth, cumulative UTF-8 string-byte, and canonical serialized-byte bounds
before walking selected/omitted receipt rows. Final serialized text is byte
counted and hashed in bounded chunks; no unbounded encoded copy is made.
Regression coverage confirms custom assembly row containers are rejected
without iteration, caller mutation after preflight does not alter the
validated prompt, and container copying itself is capped to the node allowance
plus one sentinel.

## Independent review

Job `W2-E0-SERIALIZED-PROMPT-GATE-REVIEW-20260924`, nonce `SPGR-743ca9`,
accepted the final implementation. Review findings on preflight allocation,
assembly mutation, and concurrent container growth were fixed with exact
built-in input types, bounded chunking, an owned canonical snapshot, and
iterator bounds. The reviewer found no remaining issues and did not run tests.
E0 remains incomplete.
