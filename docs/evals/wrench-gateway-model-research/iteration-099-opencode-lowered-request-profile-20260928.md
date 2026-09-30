# Iteration 099: OpenCode V2 lowered-request tool-profile preflight

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-OPENCODE-MOCK-RUNTIME-012-20260928`  
Status: **installed-runtime request shaping passed; 35.8539% target-token input reduction on one synthetic read-only request; task utility and frontier savings remain unproven**  
Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway goal SHA-256: `D6EE8ABF38EF643C58D0FE513361831BE9341E32E4794128BBF0BF7E178E2E95`

## Paired result

The harness ran installed OpenCode `2.0.12` twice in the same isolated
project and home against a loopback-only OpenAI-compatible receiver. Both
lowered requests carried the same user and non-system messages. The system
messages differed after the tool profile changed; both exact message payloads
and raw request bodies are identified by hashes below. No prompt or tool schema
is stored in the receipt.

| Arm | Tool schemas | Exact request bytes | MiniMax M3 target-token input |
|---|---:|---:|---:|
| Baseline | 12 | 26,241 | 6,599 |
| Read-only profile (`glob`, `grep`, `read`) | 3 | 15,854 | 4,233 |
| Reduction | 75.0% fewer tools | 39.5831% fewer bytes | **35.8539% fewer tokens** |

The token count used the pinned `MiniMaxAI/MiniMax-M3` chat template and
tokenizer revision `f0e1c1e04d40177e4673a22097036854f536e9c0`, inventory SHA
`86d0d4866b4278ce7957644e81e43ce90da356fdd434abfa8c928b4f1adfcc9c`, and
runtime versions `transformers 5.17.0`, `tokenizers 0.23.2`, and
`huggingface-hub 1.33.0`. The counter reads the `input_ids` sequence from the
tokenizer's `Mapping` result and validates its shape. The receipt records a
single request per arm, target-token counts, byte counts, exact lowered-body
hashes, exact message-payload hashes, and the full baseline inventory hash.

This is a **single synthetic request-shaping measurement**, not a coding task.
The prompt explicitly disallowed tool use; the mock always returned `MOCK_OK`
without executing a tool. Thus the run establishes that the installed OpenCode
V2 hook can alter the tool inventory before the outgoing request and quantifies
one mechanical overhead reduction. It does not establish verified task
completion, retained capability, real provider token billing, frontier-call
frequency, LoRA selection quality, cost, latency under useful work, or a full
workday of engineering. It is not evidence for the 95% product target.

## Runtime debugging and source change

The failed probes were preserved in their attempt receipts where the harness
had a unique receipt path. They exposed
three integration issues before a successful run:

1. OpenCode V2 did not discover a flat `.mjs` file. Moving the entry to
   `.opencode/plugins/wrench-tool-profiles/index.ts` made discovery visible.
2. The sanitized offline test environment did not contain the
   `@opencode/plugin` module from the isolated offline project. The no-provider harness now exports the
   documented V2 `{ id, setup }` definition object directly. The installed
   runtime loaded it and invoked its context hook.
3. OpenCode message entries are class instances, although their own data fields
   are JSON-shaped. The selector snapshotter now copies bounded enumerable own
   data fields from object instances while still rejecting accessors, symbols,
   hidden own properties, invalid values, and prototype chains outside the
   ordinary data-object chain. This kept
   the selector snapshot immutable and allowed the registered profile to run.

The initial equality gate compared every message, including the system prompt.
With the same project, user message, and settings, only the system message
changed across arms. The harness now requires every non-system message to stay
byte-equal, reports the system equality result and hashes separately, and
counts the exact resulting messages plus tool schemas for each arm. This
captures the measured treatment without concealing the system-prompt delta.

The first successful-runtime receipt accidentally counted the two keys in a
`BatchEncoding` wrapper rather than tokens. A follow-up failed closed because
`BatchEncoding` implements `Mapping`, not `dict`. Iteration 012 fixed the
counter to read and validate `input_ids`; its 6,599/4,233 values are the first
usable token counts. The superseded attempt receipts remain unchanged.

## Exact identity and accounting

Successful receipt: `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\opencode-request-preflight-012.json`  
Receipt size: 2,900 bytes  
Receipt SHA-256: `4e70c68f0dd532d83291127aab6ad26cae97fb518a9b53768c7b7e28f65f2c8f`

| Identity | SHA-256 |
|---|---|
| OpenCode v2.0.12 binary | `58d550b26e9241759a6906c65f1e0605eaf512d63cbaf6d8eb472375b9311c95` |
| `no_provider_request_preflight.mjs` | `e6dc5c16c474385fae243e22cc22d140399250536c7df34a8633141c96c9b859` |
| `tool_profiles.mjs` | `19769a4229878c9ac0c42ce93b3f44cde8864a7121d6fca94363f3e92ef8b014` |
| `tool_profiles.test.mjs` | `62f19a92b48546cbcde63d2435a77d560aa60320c43d17eed4d10221bee4903c` |
| Baseline exact HTTP body | `d707eb54949a1f63dbd4a413ba39fac34811ecb541afd946087f2dc8730570a5` |
| Filtered exact HTTP body | `7cc1d8602af4b4f9dcd98981df94c4f608e27c6eb70ce0c3f786ac8e1f259bde` |
| Baseline messages | `50723d5eaa84441ff65a94f1be8199ce2dd4cab546dc0cd9d9d1eaa4ba6f9d83` |
| Filtered messages | `1901156b0ff370c34017ecaac4e412654dcf801db2a446bbd6777f893abcb53f` |

The local mock received exactly two requests and the receipt records zero
provider calls. SubRoute `127.0.0.1:4000` was not called or changed; the forced
OpenRouter route and missing aggregate spend cap remain reasons not to send a
real provider completion. Egress was limited by an isolated OpenCode
configuration/home, scrubbed child environment, offline package resolution,
and a receiver that accepts only loopback peers; no OS-wide firewall change
was made. The pre-run sample was 27.70% free system RAM and 15,225 MiB free GPU
memory. No continuous minimum was captured, so sustained resource-floor
compliance for this short job remains unverified. Its unique 100,000,000-byte storage reservation covered
the temporary runtime and receipt. The checker inventoried the repository,
approved data root, Docker WSL model volume, automation and known external
roots and remained below the 50 GB aggregate ceiling.

## Verification and next step

`node --test examples/opencode_v2_subroute_tool_profiles/tool_profiles.test.mjs`
passed **24/24** against the source hashes above. `node --check` and
`git diff --check` passed; Git printed existing line-ending conversion
warnings. The OpenCode integration was exercised using the installed
v2.0.12 binary, not only a unit-test mock.

Next, measure a predeclared ladder of tool profiles over frozen coding
episodes, then score exact completion, required tool coverage, failures,
abstentions, retries, and human rescue. Optimize token reduction subject to
that quality gate. Continue paired provider accounting only after a caller-side
hard cap and durable usage receipts exist. The broader Qwen3.5-2B LoRA study,
95/5 routing, 95% retained task success, 95% frontier-token/all-in cost savings,
and sustained all-day engineering remain open.
