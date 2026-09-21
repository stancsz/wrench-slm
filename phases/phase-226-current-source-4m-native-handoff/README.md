# Phase 226: current-source 4M model-local native handoff

The source runtime accepted a request labeled as the 4,000,000-token probe at
its own Ollama-shaped `/api/chat` surface. The complete raw payload entered the
Wrench package first. The package's integrated first-layer gate then compacted
the request before forwarding it to a local native protocol stub.

Receipt highlights:

- requested admission target: 4,000,000 tokens
- server raw estimate: 3,996,267 tokens
- raw payload estimate from the probe: 3,995,842 tokens
- staged model context: 1,955 tokens
- configured working budget: 64,000 tokens
- server staging: 104.608 ms
- complete local round trip: 201.307 ms
- native backend prompt tokens: 1,955
- model calls: 1
- raw and prepared payload hashes: present and bound
- status: `PASS_NATIVE_HANDOFF_STAGED_4M`

The probe now uses a 4,096-token admission safety margin because the runtime
uses bounded sample-density estimation for multi-million-token requests. This
keeps a nominal 4M probe below the hard 4,000,000-token admission boundary.

The backend is a local protocol stub. This proves package-local raw intake,
first-layer reduction, bounded native handoff, and accounting. It does not
prove dense native attention over all 4M tokens or model-generation quality.
