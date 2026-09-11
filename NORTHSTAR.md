# Wrench-SLM North Star

> Make routine developer tool work cheaper and faster with a small local model that earns trust through correct actions, clear limits, and reliable fallback.

## The problem we want to solve

Developer agents repeatedly ask large models to choose ordinary tool calls: read a configuration file, inspect a line range, search for a literal string, or check Git state. These steps can add cloud calls, repeated context processing, and waiting to an otherwise simple task.

Wrench-SLM explores how much of that work a small local model can handle usefully. The opportunity exists only where local prediction, validation, and any subsequent verification cost less than the work they replace. A smaller model is a means to that outcome.

## Who we are building for

Our first users are developers and agent-system builders working on Windows with PowerShell and a local GPU. They need dependable tool proposals grounded in the tools, resources, and context their system actually supplies.

The initial scope is deliberately narrow: file and configuration reads, inclusive line ranges, literal search, Git status and latest commit subject, local health reads, and file-write drafts for review. English and Chinese requests are part of this scope. Broader platforms, tools, and hardware must earn their own evaluation evidence.

## The experience we want

A developer asks for a routine task. Wrench identifies an appropriate available tool and its complete arguments from the supplied context. A separate execution boundary validates the proposal and decides whether an action is permitted. The surrounding agent receives real observations and can finish the task with less work.

When the request is ambiguous, unsupported, missing required context or tools, or outside the input budget, the system falls back cleanly. It never invents a resource or forces a local answer to improve its offload rate. Mutations remain review-only drafts within the current scope.

The long-term experience should feel like a dependable local component: easy to load, bounded in resource use, observable when it fails, and simple to bypass.

## What success means

Our north-star outcome is **more correctly completed developer tasks at lower total workflow cost and latency, without weakening execution controls**.

We measure that outcome against both a cloud-only workflow and a deterministic helper using the same inputs and task conditions. The learned component must justify its added complexity. If rules provide the same benefit more reliably or cheaply, use the rules for that work.

The scorecard must keep these dimensions visible:

| Dimension | What we measure |
| --- | --- |
| Task success | Correct final outcomes supported by real tool observations |
| Useful local coverage | Correct accepted routine proposals divided by all supported routine requests |
| Accepted errors | Incorrect accepted calls and false acceptance of requests that require fallback |
| Total cost | Cloud usage and local work, including verification, corrections, failures, and retries |
| Total latency | Complete task time, including local prediction, queueing, tool execution, and cloud turns |
| Resource use | Measured memory and throughput on the named hardware and workload |

Coverage alone cannot establish value. Valid JSON alone cannot establish correctness. Model accuracy alone cannot establish workflow improvement. Report the tradeoffs rather than hiding them in a single score.

## Principles that guide decisions

1. **Correctness before coverage.** Prefer a recoverable fallback over an incorrect accepted action. Evaluate abstention and useful completion together so refusing everything cannot count as success.
2. **Context before memorization.** Select tools and arguments from supplied schemas and resources. Test unfamiliar wording, competing resources, missing information, and misleading context.
3. **Execution controls outside the model.** A prediction is a proposal. Syntax validation and model confidence do not authorize execution or prove that a command is safe.
4. **Evidence before claims.** Preserve reproducible artifacts, hashes, inputs, outputs, and measurements. Label authored fixtures, historical regression tests, and production observations according to what they actually demonstrate.
5. **Fresh evaluation after learning.** Keep final evaluation out of tuning and selection. Once results inform a repair, retain those cases as regression evidence and obtain fresh evidence for the next candidate.
6. **Simplicity before expansion.** Improve a bounded, useful capability before adding model tiers, training techniques, serving infrastructure, or integrations.

## Where we stand

As recorded in the repository on September 10, 2026, Wrench-Pro V21 is a packaged LoRA adapter for Qwen2.5-0.5B-Instruct. Its release and context suites demonstrate success on specific authored scenarios. The packaged runtime generates proposals and validates them afterward; it does not execute them.

Practical workflow benefit remains unproven. Historical regression results do not establish independent generalization, and measured GPU prediction times do not establish a service guarantee. A validated CPU/edge tier, production router integration, and measured cloud savings remain future work.

## Current practical direction

Maximize useful selective offload. The local component can serve a small,
reliably identified subset and send everything else to a stronger model.
Broad standalone accuracy and high coverage are not prerequisites for value.
Measure accepted correctness, fallback behavior, final task outcomes, and net
cloud tokens saved after corrections and verification. Any positive savings
can be useful; report uncertainty and latency tradeoffs honestly.

Prefer deterministic handling where sufficient. The learned component earns
its place only through incremental measured benefit. Expand accepted scope
from evidence rather than forcing local responses or training indefinitely.
The active goal defines the bounded experiment and its current gates.

## How to use this document

Use this north star to decide which work deserves attention. Before starting a feature or experiment, state which user outcome it should improve and what evidence would show that improvement.

[goal.md](goal.md) owns the active execution plan. The V2 usefulness protocol preserves the historical broad evaluation; the new selective protocol required by the active goal will own its frozen experimental rules. The [release handoff](docs/reference/MODEL_RELEASE_HANDOFF.md) owns artifact details and release evidence. This document provides durable direction; it does not replace those records or turn historical architecture targets into achieved results.
