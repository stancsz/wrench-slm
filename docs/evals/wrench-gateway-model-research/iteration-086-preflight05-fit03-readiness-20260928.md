# Iteration 086: preflight 05 reuse and Fit-03 execution binding

Date: 2026-09-28 (America/Edmonton)  
Job ID: `WRENCH-PREFLIGHT-REUSE-ITER086-20260928`  
Status: static identity and receipt check; no new model execution  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Current gateway-goal SHA-256: `225D7250BA53C1F2FC63E999A619B53CC3D4E779BE3D3B4D5726829FA89D6D2F`

## Preflight 05 identity

The retained preflight-05 manifest is `PREFLIGHT_COMPLETED`, with
`preflight_only=true`, `fit_mode=false`, eight synthetic training examples,
one optimizer step, and no adapter output. Its receipt states that the runner
did not open held-out data. Current files match the receipt's pinned values:

| Identity | Current SHA-256 | Preflight pin | Match |
|---|---|---|---|
| GPU trainer | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` | same | yes |
| GPU fit protocol | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5` | same | yes |
| Preflight manifest | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` | Iteration 083 pin | yes |
| Preflight resource log | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` | Iteration 083 pin | yes |

This makes preflight 05 eligible for reuse under the protocol's identity rule.
It does not satisfy the independent review of the current 12-item Fit-03
package: the current goal SHA differs from the goal hash reviewed in
Iteration 083. Do not start fit until an independent reviewer rechecks the
current exact package and its scope.

## What the hardware receipt says

The one-step preflight began with 17.50% free RAM and reached a recorded
minimum of 10.985%; minimum free VRAM was 54.47%. It used the RTX 5060 Ti,
24 attention-only projection modules, and 540,672 trainable parameters. This
is real compatibility evidence for one optimizer update, but the RAM minimum
was only 0.985 percentage points above the hard floor. It is not evidence
that a 96-step fit can run smoothly. Fit-03's >=25% free-RAM start condition
remains in force.

The exact Fit-03 job is
`WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-03-ATTN`. It writes the
candidate to
`C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-02\fit-03-attention-only`
and logs to
`C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-fit-03-attention-only`.
The runner requires a fresh reservation of at least 1,500,000,000 bytes and
at least that reservation plus 5 GiB free at the destination, >=25% free RAM
at process start, and >=10% free RAM and VRAM throughout. The fit uses only
the pinned synthetic train/dev split for exactly 96 optimizer steps, saves an
inactive candidate, and does not open held-out data.

At this check, RAM was 3,390.3 / 32,701.8 MiB free (10.37%), so fit admission
failed the 25% start gate. No exact Fit-03 job was launched. No tests,
inference, training, benchmark, provider call, credential read, SubRoute
change, or held-out payload access occurred.

## Next action

When RAM has a safe margin above 10%, independently recheck the current
12-item package. If it passes, wait for a fresh >=25% RAM start sample, run
storage/destination admission, then use only the exact Fit-03 job ID and
paths above. Recheck RAM, VRAM, and storage at every prescribed boundary and
release the reservation only after the process stops and outputs are
accounted. The 95/5 routing, 95% frontier-token reduction, 95% all-in savings,
and sustained engineering claims remain unproven.
