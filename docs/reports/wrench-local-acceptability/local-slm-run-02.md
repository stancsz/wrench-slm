# Local SLM acceptability run 02

Date: 2026-09-25 (America/Edmonton)

## Result

**No measured task class is acceptable for this local SLM route.** The pinned
model completed all ten synthetic responses, but made zero required evidence
tool calls. All ten cases failed schema validation, exact tool flow, and the
case-pass rule. Each of the five classes scored 0/2. This is a negative screen
on one open-development synthetic fixture, not a real-work estimate.

| Task class | Cases | Grounded accepts | Strict correct abstentions | False abstentions | Wrong known claims | Escalations | Class pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Localization | 2 | 0 | 0 | 0 | 2 | Not representable | 0/2 |
| Failing-log triage | 2 | 0 | 0 | 2 | 0 | Not representable | 0/2 |
| Context selection | 2 | 0 | 0 | 2 | 0 | Not representable | 0/2 |
| Evidence availability: missing/stale | 2 | 0 | 0 | 0 | 0 | Not representable | 0/2 |
| Evidence specificity: specific/ambiguous | 2 | 0 | 0 | 1 | 0 | Not representable | 0/2 |
| **Total** | **10** | **0** | **0** | **5** | **2** | **Not representable** | **0/10** |

The two localization outputs asserted `known` with unsupported source claims.
The other eight outputs abstained with `unknown`. Five were false abstentions
for answerable cases. Three matched only the broad abstention intent on
missing, stale, or ambiguous cases; they do not count as strict correct
abstentions because the model skipped the required read/search action and
returned the invalid combined reason `missing|stale|ambiguous`. Therefore all
ten task outcomes remain unresolved as evidence-grounded decisions. There
were zero disallowed tool attempts or mutations. The response contract has no
escalation action, so escalation counts are not measurable here.

## Identity and receipt

- Durable output:
  `C:\wrench-slm-data\artifacts\wrench-local-acceptability\qwen35-0.8b-synthetic-20260925-02.json`
- Receipt SHA-256: `d2cce0fd3dee7a420cffa23e9f8f4bc8bb24368dab842353de8c85fce43598f8`
- Fixture manifest SHA-256: `871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5`
- Model: Qwen/Qwen3.5-0.8B revision `2fc06364715b967f1860aea9cf38778875588b17`; all 13 snapshot file identities verified, totaling 1,769,980,465 bytes.
- Runtime: Windows 11, Python 3.13.15, Transformers 5.17.0, Tokenizers 0.23.2, Hugging Face Hub 1.33.0, Torch 2.14.0+cu132, CUDA 13.2; all 35 locked distributions verified.
- Serializer: `direct_transformers.apply_chat_template.v1`; runtime lock SHA-256 `0ed35342ae184741886fff2764f87c44df8babfde3912c54a9e1cd73ffbf2420`; tokenizer template SHA-256 `273d8e0e683b885071fb17e08d71e5f2a5ddfb5309756181681de4f5a1822d80`.
- Run status: completed, 10/10 responses, no retries, no provider/network calls, no training.

## Cost and resources observed

The ten serialized requests consumed 2,693 local prompt tokens and 366 local
completion tokens, 3,059 total. Mean generation time was 11.26 seconds per
response (112.56 seconds total); localization responses took 25.1 and 26.6
seconds, while the other responses took about 7.2 to 7.8 seconds. The tool
call count and tool time were both zero. Frontier-token savings are **N/A**:
there are zero matched real frontier usage receipts. The local token count is
not a token-saving percentage.

During model loading, 21 resource samples showed minima of 44.61% free RAM and
85.16% free VRAM; the maximum observed sampling interval was 2.591 seconds.
During case generation, the minima remained above the required 10% reserve.
No sampled reserve breach occurred. Sampling can miss shorter transient dips.
Transformers reported falling back to reference PyTorch implementations for
the optional causal-convolution and flash-linear-attention kernels; no runtime
packages were added during this run.

Before the run, storage status was `WITHIN_LIMIT`: actual 10,078,261,598 bytes,
active reservations 18,001,103,000 bytes, projected 28,079,364,598 bytes, with
21,920,635,401 bytes headroom. The 18 GB admission reservation covered this
single run and its pinned model/runtime. The run JSON remains under the approved
data root and is not copied into the repository.

## Decision

Do not route local SLM answers into coding work based on this result. The
measured failure mode is failure to initiate required evidence-tool use,
combined with unsupported answers in localization and blanket abstention on
other answerable classes. Keep deterministic exact-read/literal-search
behavior as the only currently measured narrow local envelope; this run does
not validate the SLM for it. Do not train, tune, or claim utility from this
open-development fixture. Any next diagnostic needs a fresh preregistration
with a specific tool-selection/abstention hypothesis. Real-work acceptability
still needs consented matched tasks and independent outcome oracles. The
frontier token-savings dashboard remains N/A, not zero percent.
