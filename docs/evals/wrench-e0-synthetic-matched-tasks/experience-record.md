# Synthetic regression experience record evaluation

Job: `W2-NS-W5-SYNTHETIC-RECORD-20260924`

Nonce: `W5REC-01AD`

Base HEAD: `405f72e36fa53648e02ac5146dd952cb30eb0464`

## Result

The focused synthetic experience record suite and the existing matched-task
suite passed: **14 passed** using the cached Python 3.11 environment. The
record validator accepts only the fixed pinned fixture and case references,
checks canonical bounded reference-only records, and rejects training
eligibility, mismatched oracle identity, corrupted digests, noncanonical JSON,
invalid candidates, unknown cases, altered fixture identity, and invalid
review bytes.

The result is a local synthetic-regression comparison. A hash binds the
caller-supplied candidate bytes represented by canonical JSON but does not
prove route execution or task truth. No generic E0 outcome receipt is accepted
as an oracle. No record is training-eligible.

## Independent review

`synthetic_record_review1` returned **PASS** with no findings. The reviewer
checked the pinned manifest and fixed usage boundary, bounded canonical output,
candidate hashing and comparison states, hard-coded training exclusion,
fixture references, and content/path omission. The review was read-only and
did not run tests.

## Limits

The comparison covers only the pinned authored fixture's frozen expected
answers. It does not admit real, customer, public benchmark, sealed, or final
data; establish rights, consent, or reviewer identity; create an E2 learning
label; authorize training or replay; or show product utility. No model,
provider, client, network, or download was used.
