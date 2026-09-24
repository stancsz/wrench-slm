# Prompt serializer input mutation guard evaluation

## Result

The fail-closed guard passed focused verification. The serializer receives a
read-only list/dict-shaped copy. A regression attempts to change the prepared
context message, catches the raised exception, and then returns serialized
input; the mutation attempt remains recorded and the gate returns
`SERIALIZER_MUTATED_INPUT` with no prompt or context identity.

## Verification

Four focused suites passed **98 tests in 7.32 seconds** on Windows Python
3.11.16 using cached pytest 8.4.2. The first invocation lacked the reserved
scratch parent and produced 43 pytest setup errors plus 55 passes. After
creating that directory under `C:\wrench-slm-data\tmp`, the complete rerun
passed all 98 tests. No dependencies were installed. `git diff --check` passed
after source and test changes.

- Source SHA-256: `1EEE1A0B41AB4669E0F15BECC6DDD9BCB7E9401AC5165BC52093CD7CAAE8669F`
- Test SHA-256: `A1D86CBE4DBA74EA02BDFEF62B0E56EAFCC40522A346AD8AA88730C1FE21FFFD`

Independent review found that unbound `dict`/`list` base methods can bypass
the mutation overrides on the serializer-only copy. They cannot mutate the
compiler-owned message that was hashed. Arbitrary serializer output remains
unverified, including output deliberately made inconsistent with its input.
The goal entry and task report now limit the guarantee accordingly.

## Limits

The JSON-shaped subclasses prevent ordinary Python writes to the serializer
copy and record attempted writes, including caught attempts. Python base-class
mutator calls can alter that copy, and the callback can return unrelated
output. The gate does not prove serialization correctness, downstream runtime
identity, OpenCode message-schema conformance, dispatch enforcement, or final
request/tokenizer parity. E0 and customer-utility acceptance remain open.
