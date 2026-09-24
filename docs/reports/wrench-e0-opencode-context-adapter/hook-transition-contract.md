# OpenCode context-hook transition contract

Job: `W2-NS-W4-HOOK-TRANSITION-20260924`  
Nonce: `W4HOOK-72C4`  
Base HEAD: `405f72e36fa53648e02ac5146dd952cb30eb0464`

## Change

Added `validate_opencode_context_hook_transition` to the existing offline
projection module. It revalidates both supplied projections against the
projector's pinned seven-field top-level envelope and Wrench bounded shape
constraints, then recomputes their digests. This is not full validation of all
nested OpenCode message or option schemas. It accepts only when session
identity is unchanged; `agent`, model, system, tools, and options are
unchanged; and the messages array contains exactly one expected bounded JSON
object at the declared position, with all original messages retained in order.
Its READY receipt contains the two projection digests, the inserted-message
digest, session/schema/version identity, and insertion position. Failure
results carry no receipt.

The projections and expected message are caller-supplied. The validator does
not authenticate that a client emitted either snapshot, prove that a hook used
the validated transition, enforce a dispatch veto, reconstruct later request
lowering, or establish provider-body/tokenizer parity. OpenCode's context hook
has no typed Wrench admission result; runtime enforcement remains unverified.

## Verification

Focused command, using the existing Python 3.11 runtime and cached pytest
dependency without installing packages:

```powershell
python -B -m pytest -p no:cacheprovider tests/test_opencode_hook_projection.py --basetemp C:\wrench-slm-data\tmp\W2-NS-W4-HOOK-TRANSITION-20260924
```

Result: **37 passed**. Coverage includes one valid insertion, changed session
and each protected field, changed/reordered originals, wrong inserted content,
invalid positions/messages, and a forged projection digest. No client,
provider, model, network, real data, or training was used.

## Independent review

Read-only review job `W2-NS-W4-HOOK-TRANSITION-REVIEW-20260924`, nonce
`W4HOOKREV-813B`, found no implementation blocker and requested that the report
limit its schema-validation claim. The report wording was corrected and
targeted re-review job `W2-NS-W4-HOOK-TRANSITION-REVIEW2-20260924`, nonce
`W4HOOKREV2-2C9A`, returned **PASS**. Both reviews were read-only and ran no
tests. See the [evaluation](../../evals/wrench-e0-opencode-context-adapter/hook-transition-contract.md).
