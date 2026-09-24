# Required hot-region overflow receipt

The E0 facade now asks the context ledger to report an oversized preserved
unit as an explicit omission. The prompt gate treats preserved evidence as
required, including when the same evidence is already listed by a required
source path. It therefore rejects the prompt before serialization and the
facade builds its normal incomplete outcome and accounting receipts.

The ledger's default API behavior is unchanged: callers that do not select the
new `on_preserved_overflow="omit"` policy still receive
`ContextSelectionError("preserved_unit_exceeds_active_budget")`. E0 uses the
opt-in mode only because it has a downstream required-evidence gate that can
convert the omission into a structured, non-routable rejection.

When multiple preserved units are pending after the budget fills, the opt-in
mode records each pending mandatory member as a preserved-unit budget
omission. The facade also bounds the deduplicated union of required and
preserved evidence IDs to the prompt gate's 256-ID limit, rejecting an
oversized union as invalid input before assembly.

The focused facade regression uses one Wrench-authored source, marks it both
required and hot, and sets the active context budget below its token count. It
asserts the exact omission reason, prompt rejection, absence of a prompt, and
valid incomplete receipts. The fixture uses a local JSON serializer and
character counter; this result does not establish downstream tokenizer or
client parity.
