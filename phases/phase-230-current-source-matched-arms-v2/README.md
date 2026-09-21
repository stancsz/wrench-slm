# Phase 230: current-source matched workflow arms

The current checked-out source server was replayed against the v2 canonical
220-case fixture using the matching v2 MiniMax teacher capture. The runner's
new isolated IPv4 health fixture was enabled, and client-side mechanical
shortcut was disabled so the request crossed the current model-local HTTP
surface.

Input and teacher pairing:

- cases SHA-256: `77ce67c7b6bb492ffc63ba26c75c322d38d73425f51e672a640705b97c78ac77`
- teacher capture: `phase-185-v2-teacher-capture/teacher-220-v2-max1024.json`
- trace set SHA-256: `3efb654569f86fdb58cf7338bcbb56e77702f26c49f0f82e27ed4ac1d367d60b`

Matched-arm results:

- weighted mechanical frontier-token coverage: `94.5411%`
- net frontier-token savings: `95.5310%`
- MiniMax teacher-only weighted final success: `78.9959%`
- Wrench plus identical MiniMax fallback weighted final success: `99.6503%`
- Wrench frontier tokens: `2,879`
- teacher frontier tokens: `64,422`
- Wrench fallback count: `5`
- prohibited accepts: `0`
- unexpected mutations: `0`
- Wrench median / p95 latency: `184.409 ms` / `2,004.182 ms`

All diagnostic gates passed. The p95 is higher than the earlier package replay
because this run includes the current source HTTP child-process boundary. This
is still historical 220-case evidence, not family-disjoint approval,
independent 5060 Ti verification, or public production authorization.
