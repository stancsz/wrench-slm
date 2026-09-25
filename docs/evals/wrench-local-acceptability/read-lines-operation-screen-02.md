# Read-lines operation screen 02: superseded before measurement

Status: independent preregistration review found a scoring defect before any
case execution; zero measurement cases ran.
Date: 2026-09-25 (America/Edmonton)
Preregistered job: `LOCAL-READLINES-ACCEPT-20260925-02`
Repository revision at review: `b3cb74cbcbe29288f31892c48e7bed675f07d365`

The reviewer found that the runner converted every non-completed route status
to `abstain` and compared the action only for completed routes. The protocol
requires exact status/action/reason scoring for every case. A `partial` route
could therefore have been reported as a correct abstention, and a wrong action
could have escaped detection. This was a material scoring defect, so the run
was stopped before execution and its 5 MB reservation released.

The runner now compares the exact enum status and expected action for each
case, including an explicit `None` action for the ambiguous prompt. The
corrected rule and fresh run identity are frozen in
[protocol 03](read-lines-operation-protocol-03.md). Neither protocol 01 nor 02
produced measurement cases, and neither is combined with later results.
