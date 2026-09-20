# Phase 103: bounded default read fast path

The mechanical router now gives a simple read request without an explicit byte
limit the verifier's maximum bounded limit of 256 KiB. Requests that say
`entire`, `whole`, `complete`, `full`, or `all` remain ambiguous and continue
to the model or fallback path, so the default cannot silently claim a complete
large-file read.

Evidence:

- `Read README.md.` produces `read_file` with `max_bytes=262144`.
- `Read the entire README.md.` remains model/fallback-required.
- targeted route, worker, and weighted-score tests: `18 passed`.
- the historical 220-case fixture remains `200/220` mechanical routes and
  `78.9999%` eligible weighted frontier-token mass because its 20 patch-draft
  eligible prompts omit the actual diff.

This is a bounded practical-work optimization, not a quality or release claim.
