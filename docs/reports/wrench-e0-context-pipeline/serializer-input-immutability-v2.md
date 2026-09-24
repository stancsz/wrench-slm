# Prompt serializer input immutability

Date: 2026-09-24 (America/Edmonton)
Job: `W2-NS-E0-SERIALIZER-MUTATION-HARDENING-20260924`
Nonce: `E0SMH-ROOT-7D42`
Base: `cd70a88e399fb722c7918b5c1fe87141141cf381`

## Change

`compile_prompt` now passes the serializer a recursively detached read-only
message tree: mappings are `MappingProxyType` views over copied dictionaries,
and list-shaped values are tuples. Direct `dict.__setitem__`, `list.__setitem__`,
and ordinary `object.__setattr__` attempts cannot change these built-in
immutable views. A serializer that catches a `TypeError` may continue safely
because the message tree remains unchanged. An uncaught callback error returns
`SERIALIZER_ERROR` without a prompt.

The callback interface is typed and documented as a
`Sequence[Mapping[str, object]]`. JSON encoders that need concrete lists and
dictionaries may call the bounded `materialize_prompt_messages` helper, which
returns a detached mutable JSON tree. Callback output remains any `str` or
`bytes`, including a target-specific suffix; it is counted as returned.

The older serializer-mutation report and evaluation describe the earlier
list/dict subclass approach and are preserved as historical evidence. This
report records the replacement contract.

## Verification

Windows Python 3.11.16 with cached pytest 8.4.2 ran the eight available focused
modules:

```powershell
$env:PYTHONPATH = 'C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages'
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_prompt_compiler.py tests/test_e0_context_pipeline.py tests/test_e0_request_record.py tests/test_e0_lifecycle_accounting.py tests/test_e0_route_preparation.py tests/test_e0_route_preparation_composition.py tests/test_e0_source_injection_route.py tests/test_opencode_context.py --basetemp C:\wrench-slm-data\tmp\W2-NS-E0-SERIALIZER-MUTATION-HARDENING-20260924
```

Result: **102 passed in 11.18 seconds**. The prompt compiler tests cover direct
unbound dict/list mutator calls, caught mutation exceptions, built-in
attribute replacement, JSON materialization, and arbitrary string and byte
suffixes. JSON callback fixtures in the affected modules now materialize the
read-only input before encoding.

The initial nine-module collection including
`tests/test_qwen_system_one_contract.py` stopped because `torch` is not
available in the existing Python 3.11 environment. No packages were installed.
The Qwen suffix serialization behavior also has a passing focused regression
in `tests/test_prompt_compiler.py`; the Qwen contract module itself remains
unverified in this run.

The first run after changing to built-in immutable views found two test
expectations that caught `TypeError` but not `AttributeError` from
`object.__setattr__`. The fixtures were corrected to accept both blocked
mutation exceptions; the complete eight-module rerun passed.

Independent read-only review `E0SMH-FINAL-24C8` returned **PASS** against the
final source hash. It confirmed the materializer and arbitrary output contract,
direct built-in mutation resistance, suffix coverage, and the stated
same-process reflection limit. The reviewer ran no tests.

## Exact identities

| File | SHA-256 |
| --- | --- |
| `src/wrench_harness/prompt_compiler.py` | `3201A779F940FF8506A1396157CBFC36A7C2F97032CF93B2F54F1C38502B4B43` |
| `tests/test_prompt_compiler.py` | `ACB12A8E2EB1A7CB94790637949D74711B150A419CED1E0B362568E12A5B6388` |
| `tests/test_e0_context_pipeline.py` | `0029E6F2A683CD0A015E82B96E8F5D25380641B77AC6FCBA7DC53267DE832105` |
| `tests/test_e0_request_record.py` | `62F2C46AE095635CFC3F7A33CDABB752CB5E28D78B3B37161499FAEC2C7093C5` |
| `tests/test_e0_lifecycle_accounting.py` | `55C98F759A9B8F2A0C7E2A24475843CE60A4A7F20485F6FEC18994D4B4E5472F` |
| `tests/test_e0_route_preparation.py` | `3AF272082F057C24931DECC2477A9797B66594EC47FB1B1BE7B6FB1AA1C8847C` |
| `tests/test_e0_route_preparation_composition.py` | `56228829D3B9FCBEBBB9C451BAAE83EE1B591877BDAA71ED19F42B8E0634A430` |
| `tests/test_e0_source_injection_route.py` | `1421604D79B848A8E030CFF1DD5635AE3A91217744052B7D1F9A20650BA8458A` |
| `tests/test_opencode_context.py` | `565382F64EA3048EA7AC84A2707840F014743710FB23F7CD25CB597BF40D4853` |
| `tests/test_qwen_system_one_contract.py` | `B5F760BFAEA762A28B60568F270E5A88A222CAAA1A2B691D11623F2DE0C4A36D` |

## Resource and storage record

Before and after the focused run, the storage checker included
`C:\Users\stanc\AppData\Local\npm-cache` and returned `WITHIN_LIMIT`.
After the run, actual Wrench storage was 2,286,617,807 bytes, with 10,103,000
reserved bytes including this job. The task scratch path was under
`C:\wrench-slm-data\tmp\W2-NS-E0-SERIALIZER-MUTATION-HARDENING-20260924`.
At the last resource inspection, 14,646,693,888 of 34,290,302,976 RAM bytes
and 15,192 of 16,311 MiB VRAM were free. No model or GPU workload ran.

## Limits

The immutable views block the tested built-in mutation paths. A same-process
callback can use reflection such as `gc.get_referents` to reach a mapping
proxy's backing dictionary, so this is not a Python sandbox. A callback may
also return an unrelated representation; arbitrary formats prevent a generic
structural equivalence check. The serializer and tokenizer identities remain
caller-declared, and this change does not prove OpenCode runtime use, final
provider request parity, dispatch prevention, or E0 acceptance.
