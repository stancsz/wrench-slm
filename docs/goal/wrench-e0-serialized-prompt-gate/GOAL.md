# E0 serialized prompt budget gate

Status: bounded implementation slice accepted; E0 remains incomplete
Job: `W2-E0-SERIALIZED-PROMPT-GATE-20260924`
Nonce: `SPG-349b21`
Baseline: `32ca951abe9c2818eb6e988a22ffd4b95160cf0a`

## Outcome

Provide a deterministic contract gate that counts the complete serialized chat
prompt supplied by the caller's serializer and tokenizer counter before a
caller may route it. The gate does not attest that those callbacks match a
downstream runtime.

## Acceptance

- Require the caller's complete base messages, assembly receipt, insertion
  position, hard positive token budget, serializer/tokenizer callbacks, and
  explicit identities for both callbacks.
- Insert selected assembled context into the complete base message list,
  including fixed instructions and deferred schemas supplied by the caller.
- Validate assembly shape, selected/omitted evidence, required evidence IDs,
  message counts, input bytes, and final serialized byte size.
- Count the serialized output only. Return the prompt only when within budget
  and no required evidence was omitted. Required-evidence omission, invalid
  data, callback error, and over-budget count fail closed. Optional evidence
  omissions may still return `READY` when their IDs and reasons are recorded
  in the receipt and all other gates pass.
- Return a receipt binding session, selected/omitted evidence, serialized hash,
  exact count, hard budget, tokenizer/serializer identities, and status.
- Keep the API pure: no provider/model calls, sending, routing, or execution.

## Limits

The gate can verify that named callbacks were invoked and bind their declared
identities; it cannot prove they match a later production runtime. Fixture
callbacks do not establish tokenizer accuracy. Logical context budgets and
default word estimates are not substitutes for this final serialized count.

## Review

Independent review accepted the bounded snapshot, complete-message
serialization, evidence-omission accounting, and token-budget gates. It does
not establish production tokenizer accuracy or complete the integrated E0
baseline.
