# Iteration 050: harden tool-profile snapshots (2026-09-27)

## Hourly continuation state

The local automation record confirms wrench-hourly-token-reduction-monitor is
ACTIVE with an hourly interval and targets this research thread. The older
wrench-gateway-research heartbeat is PAUSED, so this work does not add a
duplicate schedule.

## Source change

Continued the Iteration 049 per-request tool-profile prototype:

- Tool inventory hashing now tracks aggregate UTF-8 input bytes while
  canonicalizing. It rejects an oversized inventory before building an
  unbounded serialized representation.
- The local selector receives a frozen JSON snapshot. Undefined optional
  object fields are omitted; accessors are rejected without invoking them;
  oversized and overly complex inputs fail through with the full tool set.
- Added three synthetic cases for aggregate size limits, optional undefined
  fields, and accessor rejection. The current suite now contains 13 cases.

Current source identities:

| File | SHA-256 |
| --- | --- |
| examples/opencode_v2_subroute_tool_profiles/tool_profiles.mjs | 74B64E1769344586175A817F26E87280F34EB680918DEC7DCE36F2E7925A1DE2 |
| examples/opencode_v2_subroute_tool_profiles/tool_profiles.test.mjs | 86B7302110BEB6B92372D9CA29ADC7A164708144D326DDEF59D3F09AEE2E2401 |
| examples/opencode_v2_subroute_tool_profiles/README.md | DA037AAE6878412E0D04FBE0AD477632771EF3541FA39D6C64E4F4D56C9DC925 |

Repository HEAD before and after was
af01304824f079a64b6c3902397a2034b843511a.

## Verification and admission

No tests or syntax checks were run after this source change. The previous
Iteration 049 10/10 result applies only to the prior source hashes. This
13-case suite is pending verification. RAM samples varied from 9.70% to
10.12% free during this continuation; the final sample was
3,309.4 / 32,701.8 MiB (10.12%), too close to the reserve for another runtime
job. No inference, training, benchmark, packaging, or delegation ran. No
provider request or credential read occurred.

The storage checker, including the external SubRoute checkout, reported
WITHIN_LIMIT: 10,992,785,011 actual bytes plus 8,183,000 bytes in active
reservations. The current 80,000-byte source-job reservation is
WRENCH-TOOL-PROFILE-SNAPSHOT-HARDENING-20260927-01 and must be released after
this report and goal update are accounted.

## Next step

When system memory is safely above the runtime floor, run the current 13-case
suite, then verify the hook against an isolated no-provider OpenCode v2.0.12
request. Training and model inference still require the separate 25% RAM
start gate and complete job admission. Keep the :4000 route reserved for the
paired frontier arm; do not send a generation request before a numeric
aggregate USD cap and validated billing receipts exist.
