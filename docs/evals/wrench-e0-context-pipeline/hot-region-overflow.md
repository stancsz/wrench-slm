# Required hot-region overflow evaluation

**Scope:** one offline E0 facade fixture at the repository's current source
revision. No client, provider, model, network, or real task data is involved.

The regression marks one exact snapshot source both required and hot, then
gives context assembly a budget of one token. The source cannot fit. The E0
facade returns no prompt, records the source ID with
`preserved_unit_exceeds_active_budget`, reports
`REQUIRED_EVIDENCE_OMITTED`, and emits an incomplete outcome receipt plus a
verifiable preparation-accounting receipt. Direct ledger callers retain the
previous default exception behavior.

A ledger fixture also covers a second mandatory unit after the first exactly
fills the budget, and an E0 fixture confirms the combined required/preserved
ID union is rejected when it exceeds the prompt gate's 256-ID bound.

This verifies the facade's fail-closed overflow and omission accounting only.
The injected fixture serializer and character-count callback do not match a
downstream client runtime and provide no utility evidence.

Independent review returned **PASS** (`HOTREV3-70AF`) at repository HEAD
`0123979281170440162972d7163510dbfdb3e1ff`. The review checked the default
fail-closed behavior, explicit omission receipt, combined-ID bound, and the
matching report/evaluation scope.
