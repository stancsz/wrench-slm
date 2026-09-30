# Iteration 080: SubRoute port 4000 and Qwen snapshot verification

Date: 2026-09-28 (America/Edmonton)

Assignment: `WRENCH-QWEN08-LOCAL-SNAPSHOT-VERIFY-ITER080-20260928`

## Local SubRoute check

Using the owner-directed service at `http://127.0.0.1:4000`, GET requests to
`/health/liveliness`, `/models`, and `/v1/models` returned HTTP 200. Both model
list routes returned 19 aliases. A GET to `/health` timed out at five seconds;
the configured liveness route succeeded, so the timeout does not establish a
gateway outage. No completion, provider, or credentialed request was sent.

This confirms the local control plane is reachable. It does not establish that
the running process loaded the reviewed callback changes, selected a provider,
or returned provider usage and billing receipts.

## Pinned local snapshot

The bounded read-only verification passed for `Qwen/Qwen3.5-0.8B`, revision
`2fc06364715b967f1860aea9cf38778875588b17`: 13 files totaling 1,769,980,465
bytes. Paths, sizes, local inventory SHA-256 values, available Git blob IDs,
and the raw upstream SHA-256 pins for the LFS weight and tokenizer matched.
The LFS pointer Git blob IDs were not recomputed; the raw file hashes were
verified. Reparse points and hard links were rejected, and read-only pinned
file handles were retained through verification.

Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\local-snapshot-verify-iter080-20260928.json`.

| Input | SHA-256 |
| --- | --- |
| Candidate manifest | `6CEFDBBD0203D8E78EB1DEE655E82C65EFCFA425B57A80CB335242645F47F0A9` |
| Local model inventory | `C0DA144391B212875A9A142272636E63C3D0B9DF8291F2827CC8534A5C2F3CA1` |
| Read-only tree helper | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |

The verifier streamed the pinned files and performed a second unchanged-content
check on the retained handles. Free RAM at admission was 10.65%; the monitored
first hash pass recorded a 10.627% minimum. After the second check, free RAM
was 10.90%. The second pass was not sampled continuously. Free VRAM was
15,199 / 16,311 MiB. Storage status, with the SubRoute checkout included, was
`WITHIN_LIMIT` at admission with 10,994,451,272 actual bytes and 6,203,000
bytes in active reservations. C: had 144,679,428,096 bytes free.

## Decision and limits

This is local control-plane and artifact-identity evidence only. No model was
loaded; no inference, LoRA fit, benchmark, held-out access, or provider request
ran. Current RAM remains below Fit-03's 25% launch gate by about 4,611.6 MiB.
The existing staged fit still requires a fresh resource/storage admission and
an exact-identity review before launch.

No model quality, 95/5 routing effectiveness, 95% frontier-token or cost
reduction, coding ability, or all-day engineering capability is established.
Frontier generation remains closed pending the numeric campaign-wide spend
cap and verified loaded SubRoute controls. See the [research goal](../../goal/wrench-gateway-model-research/GOAL.md)
and the [research synthesis](../../reports/wrench-gateway-model-research/research-synthesis-20260927.md)
for the candidate comparison and staged proof plan.
