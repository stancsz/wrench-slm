# E0 source-injection prompt-format regression

Job: `W2-NS-E0-SOURCE-INJECTION-ROUTE-20260925`
Nonce: `SRCINJ-0E62`
Baseline: `39ae986a45bf1cb51c24f32e6737676b4f7cc89f`

## Change

The prompt compiler now labels assembled retrieved context as untrusted source
data and passes the assembled text as a JSON-quoted string between explicit
markers. JSON quoting keeps source newlines and marker-like text inside the
quoted value. The final serializer and token counter still receive the complete
message list, including this wrapper.

The authored synthetic regression puts a marker-like line and instructions in
one snapshotted file that ask the recipient to read an unselected `.private.env`
file and transmit its value. It exercises the bounded rule route, then E0
preparation against the same one-file snapshot. It verifies the route reads
only the named member, preparation retrieves only the named path, the prepared
prompt visibly labels and quotes the source, the unselected secret is absent,
and executor/process tripwires remain untouched.

## Verification

Focused Windows run used the existing cached pytest 8.3.5 environment, with
temporary output under the approved Wrench data root:

```text
tests/test_e0_source_injection_route.py tests/test_prompt_compiler.py
14 passed
```

`git diff --check` passed. No model, provider, client, network, real task data,
or training was used.

## Limits

The wrapper is a prompt-format signal. It does not prove that any model obeys
the label, prevent prompt injection, authenticate the caller, authorize
dispatch, or stop a later client from sending another request. The serializer
and character counter in the fixture are local test callbacks, not runtime
parity evidence. This work does not establish E0 acceptance, production safety,
or customer utility.

Independent review: **PASS**, job
`W2-NS-E0-SOURCE-INJECTION-REVIEW-20260925`, nonce `SRCINJREV-81A4`. Review was
read-only and limited to the five scoped paths. The reviewer confirmed that
the marker-like source line remains inside the quoted payload and the read
scope assertions match the stated claim.
