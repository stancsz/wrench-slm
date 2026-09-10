# Historical native sidecar example

This example serves the older native-model sidecar, not the V21 PEFT adapter. It is retained for reference and has not been validated as a production container.

From this directory, set LEAN_ROUTER_LOGS_DIR to a gateway log directory you intend to expose, then use docker compose -f compose.yml. Build context points to the repository root. The configuration mounts scratch data under artifacts/legacy-work/data and local models under models/. Supply those inputs before starting. The gateway mount is read-only.

Use the adapter workflow in docs/reference/TRAINING_FROM_CLONE.md for V21.
