# Prompt-only local work screen 01 result

**Status: FAIL_DIAGNOSTIC.** The pinned local Qwen 0.8B completed all 18
exposed synthetic prompts, but accepted zero of the 12 answerable examples
under the exact answer/schema/evidence oracle. It correctly abstained on three
of six boundary examples. All three task classes fail the all-cases-pass
threshold. This is a prompt-only diagnostic, not evidence of real-work
acceptance or held-out generalization.

| Class | Positive accepts | Correct abstentions | Whole-case passes | Decision |
| --- | ---: | ---: | ---: | --- |
| Exception mapping | 0/4 | 2/2 | 2/6 | Fail |
| Configuration extraction | 0/4 | 1/2 | 1/6 | Fail |
| Function localization | 0/4 | 0/2 | 0/6 | Fail |

Failure patterns were wrong exception normalization and invalid `reason`
fields, extra or incomplete configuration evidence fields, and missing
property-access citations plus wrong guesses on localization boundaries.
Outputs did not clear any semantic work class for local completion.

The complete analysis and artifact identity are in the [screen report](../../reports/wrench-local-acceptability/prompt-only-local-work-screen-01.md).
The [frozen protocol](prompt-only-local-work-screen-01-protocol.md) limits
this claim to these 18 closed-form text cases. It had no tools, no repository
access, no mutations, no provider calls, and no frontier usage pairs. Frontier
token savings are `N/A`. Do not tune or train on this exposed fixture.
