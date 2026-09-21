# Phase 314: current source regression

At source commit `b00a2333cba12d7be917b75ec7e0f84754d53af7`, the full local
pytest suite completed with `194 passed`, `0 failed`, and `18 warnings` in
`18.41 seconds`.

The warnings are Python 3.16 deprecation warnings from the Windows asyncio
event-loop policy used by the long-context overlay tests. They did not affect
the result. This is source regression evidence only and does not close the
family-disjoint, 5060 Ti, learned-decoder, or production gates.
