# Iteration 090: refresh the hourly experiment instructions

Date: 2026-09-28 (America/Edmonton)

Assignment: `WRENCH-AUTOMATION-ITER089-HOURLY-PROMPT-REFRESH-20260928`

Status: **hourly heartbeat remains active; prompt refreshed to current evidence**

Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`

Gateway research goal SHA-256 preserved:
`225D7250BA53C1F2FC63E999A619B53CC3D4E779BE3D3B4D5726829FA89D6D2F`

## Change

Updated the existing Codex heartbeat `wrench-hourly-token-reduction-monitor`
(`Wrench hourly gateway experiment`) in place. It remains `ACTIVE`, hourly, and
attached to thread `01a0e15d-1974-7691-9584-372374c98560`. Its update timestamp
changed from `1790581740749` to `1790582316975`; the stored prompt is 6,098
bytes.

The refreshed instructions use Iteration 089's pinned Qwen3.5-4B inventory and
current SubRoute evidence. They record that port 4000 is forced to OpenRouter,
the `desktop` alias is disconnected from the installed Ollama tags, and the
campaign spend cap is still absent. The automation is explicitly told not to
send a completion, read credentials, change/restart SubRoute, or ask again for
the cap.

The prompt now records the latest observed host sample (9.23% free RAM,
15,231 / 16,311 MiB free VRAM), prohibits runtime and delegated work below the
10% floor, retains the 25% Fit-03 start gate, and directs each hourly run to
make one concrete advance rather than repeat status-only checks. It preserves
the exact Fit-03 assignment, nonce, data boundaries, steps, storage reserve,
and held-out gate. It also requires fresh storage accounting including the
Docker WSL volume and automation directory.

## Verification

After the update, read the automation file and verified the ID, name, `ACTIVE`
status, hourly recurrence, target thread, new update timestamp, Iteration 089
reference, 9.23% resource snapshot, prohibition on repeated cap questions, and
anti-repeat instruction. The stored prompt was shortened from 11,559 bytes to
6,098 bytes. Storage remained `WITHIN_LIMIT` after adding this report; the
Docker volume stayed included in the check.

The live SubRoute GETs still returned 200 for liveness, model catalog, and
active-route status. The active route remained `openrouter`, `force`, policy
version 4. No completion, model inference, training, test run, provider call,
credential read, SubRoute change, or service restart occurred. The RAM reading
was below the runtime floor, so no agent was delegated.

## Next action

The next hourly run must take a fresh resource sample. If RAM remains below
10%, continue with lightweight provider-free work that closes a specific
acceptance gap. When resources recover, disposition the already-prepared
Fit-03 review packet before considering the separately gated synthetic fit.
The 95% local completion, 5% frontier routing, 95% frontier-token and all-in
cost reduction, and sustained engineering claims remain unproven.
