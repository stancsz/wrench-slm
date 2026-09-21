# Phase 298: remote control-plane advisor decision

After the direct network check and a fresh self-contained remote dispatch both
failed to produce an observable 5060Ti execution receipt, Sol advisor review
was requested with a compact evidence packet.

The advisor's verdict was to issue one user-visible remote control-plane repair
request, not another opaque worker turn or an assumed file-polling queue. The
repair request must restore one observable authenticated channel and then run
the exact replay at commit `77fdf44`, returning timestamped command output,
machine/GPU identity, and receipt hash. If that single repair request does not
produce observable evidence, remote work should stop and the 5060Ti result
remain an external blocker while local release gates advance.

This changes the next action from repeated remote dispatch to one explicit
operator-facing repair request. The advisor is not benchmark evidence.
