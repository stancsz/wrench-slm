# Wrench-SLM marketing review

Reviewed: 2026-09-12

This review treats the repository as a product funnel. It does not treat stars,
fixtures, local tests, or polished copy as proof of adoption or production
readiness.

## Decision

**Do not launch broadly yet.** The repository has a defensible technical story
and a provider-free evidence path, but no anonymous runnable model, trusted
workflow comparison, public release, or production outcome. Use the current
README to recruit a small number of technically qualified reviewers and data
partners. Reconsider a broader launch after M3 produces a matched decision.

## Brief

| Question | Answer |
| --- | --- |
| Primary audience | Agent-platform and developer-tool engineers evaluating safe local offload |
| Painful job | Remove routine work from a strong-model loop without creating silent errors or costly redo |
| Promise | A narrow local proposal is returned only after real-observation verification; uncertainty falls back intact |
| Memorable difference | Let the small model handle the boring work. Keep the strong model in charge. |
| Primary action now | Run the provider-free evidence gates and inspect the active contract |
| Primary action after M3 | Reproduce the matched A/B/C workflow and challenge the operator decision |

Direct alternatives are cloud-only execution, deterministic rules with
fallback, and an in-house small-model router. Wrench must beat rules on the same
workflow to justify its learned component. Model size or authored exact-match
scores alone are not meaningful differentiation.

## Funnel diagnosis

| Surface | Current state | Assessment |
| --- | --- | --- |
| Positioning | README leads with the small-model/strong-model boundary and current `DISABLE` decision | Clear and evidence-bounded |
| Discovery | Accurate About text and ten relevant topics are live | Prepared, but the repository is private |
| Proof | Frozen denominators, receipt paths, and provider-free checks are visible | Strong for local capability, insufficient for production value |
| Activation | Verification is copy-pasteable without provider calls | Useful for reviewers; there is no anonymous model demo |
| Contribution | Labels describe maturity, status, and scope | No issue templates, contribution guide, or public contributor flow |
| Retention | No releases or Discussions | Do not add these until there is a maintainable release cadence |

The highest conversion friction is artifact access. V21 and its complete runtime
package require an authorized Hugging Face account. The second is practical
value: M3 is blocked, so a visitor cannot yet reproduce a token, cost, or final
outcome advantage.

## Highest-leverage work

| Priority | Change | Expected impact | Confidence | Effort | Dependency |
| --- | --- | --- | --- | --- | --- |
| 1 | Complete trusted-data intake and the frozen matched M3 comparison | Converts a capability story into a product decision | High | High | Authorized joinable data and finite provider budget |
| 2 | Publish an anonymous minimal artifact or deterministic demo | Removes the largest first-use barrier | High | Medium | Distribution and licensing decision |
| 3 | Create one visual proof unit from the completed M3 receipt | Makes method and result legible outside the repository | Medium | Medium | M3 completion |
| 4 | Add `CONTRIBUTING.md`, security policy, and focused issue templates | Creates a maintainable contributor path | Medium | Low | Decision to accept outside contributors |
| 5 | Add a 1280 x 640 social preview and first release | Improves external sharing and return visits | Medium | Low | Public repository and launch-worthy proof |

## Existing assets

- README positioning line: **Let the small model handle the boring work. Keep
  the strong model in charge.**
- Trust line: **Current operator decision: `DISABLE`.**
- Proof unit: 90/600 accepted authored held-out cases, 90/90 successful accepted
  completions, zero accepted prohibited actions, and zero unexpected mutation.
- Verification CTA: `py -3 -m pytest -q tests`. Stronger receipt verifiers are
  development-worktree evidence until their source and inputs are committed.
- Public boundary: **no measured frontier-token savings**.

## Distribution plan

No post or outreach is authorized by this plan. Each item is a future,
maintainer-triggered experiment.

| When | Channel and audience | Native value and proof | CTA | Owner | Stop condition |
| --- | --- | --- | --- | --- | --- |
| Now, private review | Directly invited agent-infrastructure engineers | Explain the fail-closed verifier and provide the tracked receipt checks | Run the gates and report one reproducibility failure or boundary objection | Maintainer | Stop if reviewers cannot reach first proof from a clean clone |
| After M3 | Technical write-up for model-routing practitioners | Publish the complete A/B/C method, denominators, uncertainty, and decision, including a negative result | Reproduce or challenge the decision | Maintainer | Do not publish if accounting is incomplete or populations are mixed |
| After anonymous demo | Repository launch to one relevant developer community | Show one bounded request, observation, verifier result, and safe fallback | Try the demo, then inspect the receipt | Maintainer | Stop if support load exceeds capacity or failures cannot be reproduced |
| After first outside reproduction | Release note and maintainer profile | Credit the independent reproduction and document what changed | Watch releases or contribute a scoped case | Maintainer | Do not claim adoption from a clone, star, or one reproduction |

Do not mass-post identical copy, automate unsolicited outreach, buy or trade
engagement, or call stars users.

## Measurement plan

Baseline captured through authenticated GitHub CLI/API on 2026-09-12. The
repository was private with 0 stars, 0 forks, 0 watchers, 0 open issues, no
release, no Discussions, no homepage, 0 repository views and 0 unique visitors
in the available 14-day traffic window, and 6 clones from 2 unique cloners.
Popular paths and referrers were empty. GitHub community-profile health was 28%,
with no detected license metadata, contributing guide, code of conduct, issue
template, or pull-request template. Clone counts are not successful installs.

| Event | Definition | Source | Window | Decision rule |
| --- | --- | --- | --- | --- |
| Qualified visit | Repository visit during a named, annotated review or launch window | GitHub traffic API | 14 days | Report raw views and uniques; make no causal claim without a clean comparison |
| Verification success | A clean-clone user reports all three README commands passing with environment details | Reproducible issue or permitted direct report | Per release | One report is evidence of reproduction, not adoption |
| Activation | User produces the documented bounded local result or independently verifies the receipt | Explicit, permissioned report | Per release | Keep the CTA only if the event is reproducible and supportable |
| Contributor start | A scoped issue, discussion, or pull request tied to a maintained label | GitHub | 30 days | Add community machinery only when response capacity exists |
| M3 reproduction | An independent party reruns the fixed A/B/C protocol with complete accounting | Published receipt | Per protocol | Broader launch requires at least one reproducible complete result |

Traffic should be snapshotted before and after any authorized campaign because
GitHub retains only a short window. With current traffic, sequential releases
and qualitative reviewer feedback are more honest than A/B testing.

## Claim boundaries

Do not claim any of the following until the named gate exists:

- production readiness, reliability, or safety before M4 and M5;
- provider-token, cost, or latency savings before complete matched M3 evidence;
- public availability while adapter and runtime access remain private;
- general coding ability from the narrow tool-call suites;
- adoption from clones, stars, watchers, or repository traffic;
- independent generalization from authored or generated fixtures.

Publishing the repository, weights, a release, an external post, or user data
requires explicit maintainer authorization and the applicable licensing,
privacy, and evidence checks.
