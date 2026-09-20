# Phase 160: MapReduce plus dynamic native working context

Date: 2026-09-20

## Decision

The production path is now explicit: accept the raw multi-million-token
request at the model-local endpoint, map old material into content-addressed
cards, reduce exact matches into bounded evidence windows, preserve the latest
intent and hot context, then send only the selected working context to native
inference. Full dense native attention over every 4M token remains an optional
comparison mode, not the default value path.

## Evidence

- Full repository regression after the streaming hash change:
  `148 passed, 14 warnings in 17.40s`.
- Complete 220-case deterministic retrieval diagnostic:
  target reference recall `1.0`, evidence-window recall `1.0`, current-intent
  preservation `1.0`, hash-bound reference rate `1.0`, zero model calls.
- 4M deterministic retrieval diagnostic: `3,999,951` estimated raw tokens,
  `52` staged model tokens, target reference recall `1.0`, evidence-window
  recall `1.0`; cold map `87.696 ms`, hot reduce `8.949 ms` on the development
  host.
- Fresh v62 portable package: structural validation passed and the package
  runtime 4M prefill probe passed in `123.131 ms` with zero model calls.
- The v62 package is public at Hub revision
  `b31828264d7d9771674d313c2439f39556e3fdd1`; a fresh Hub download confirmed
  the MapReduce README, serial native launcher, and process-tree cleanup.
- 4M package-server native-handoff stub: `3,999,943` raw estimated tokens to
  `1,845` staged tokens, `pipeline=map_reduce_dynamic_native`, one bounded
  upstream model call, and `114.563 ms` server-side staging after the
  streaming hash optimization. The full protocol stub round trip was about
  `2.6 s` because the request body was about 35 MB.
- Full 220-case workflow replay against the current local mechanical endpoint
  remains `QUALITY_GATE_OPEN`: weighted mechanical coverage `0.559589`, net
  frontier savings `0.618292`, Wrench-only weighted final success `0.822855`,
  zero Wrench-only prohibited accepts, and zero unexpected mutations.
- Independent scorer replay of the existing matched MiniMax captures remains
  `QUALITY_GATE_OPEN` at `0.509120` coverage and `0.596654` savings for the
  canonical v5 trace, and `0.854668` coverage with `1.0` savings for the
  complete-patch derivative. The latter is close to the 90% coverage gate,
  but does not pass it.

## Boundary

The retrieval and staging evidence proves the MapReduce path, not final model
quality, MiniMax parity, the 90%/95% North Star gates, or dense native 4M
attention. The 220 workflow receipt is diagnostic historical evidence and
still needs better eligible-task coverage and a fresh approved trace set.
