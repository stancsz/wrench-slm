# Training Datasets for Wrench SLM

This directory contains curated datasets from Hugging Face specifically structured to train and specialize the **Wrench SLM (Sub-4B Parameter Model)** for high-speed local agentic tool execution, strict schema formatting, and token-absorbing triage.

---

## 1. Data Sources & Files

### A. gentic_tool_call_short_2k.jsonl (2,000 Samples, ~46.8 MB)
* **Source**: [pyromind/agentic-tool-call-dataset-12k](https://huggingface.co/datasets/pyromind/agentic-tool-call-dataset-12k) (Config: short)
* **Focus**: Short-horizon, deterministic tool-calling trajectories.
* **Why it is used for the Wrench**:
  - Teaches the model immediate, single-step and two-step tool execution (grep, iew_file, cat, terminal checks).
  - Enforces OpenAI-compatible 	ool_calls syntax.
  - Eliminates conversational preamble and chit-chat so the model emits pure JSON/XML tool calls.

### B. gentic_tool_call_long_1k.jsonl (1,000 Samples, ~225.8 MB)
* **Source**: [pyromind/agentic-tool-call-dataset-12k](https://huggingface.co/datasets/pyromind/agentic-tool-call-dataset-12k) (Config: long)
* **Focus**: Long-context, multi-turn agentic trajectories.
* **Why it is used for the Wrench**:
  - Trains the model to follow multi-turn tool observations without losing coherence or hallucinating state.
  - Teaches terminal error handling and self-correction when a tool call returns an error.
  - Absorbs long tool-navigation loops locally so frontier models are never billed for exploratory turns.

### C. glaive_function_calling_2k.jsonl (2,000 Samples, ~4.8 MB)
* **Source**: [glaiveai/glaive-function-calling-v2](https://huggingface.co/datasets/glaiveai/glaive-function-calling-v2)
* **Focus**: High-precision schema mapping and structured function calling.
* **Why it is used for the Wrench**:
  - Eliminates syntax errors (unquoted keys, missing brackets, trailing commas) when outputting JSON/Pydantic schemas.
  - Teaches the model when to call a function vs. when to respond directly.

---

## 2. Intended Role in the 3-Tier Wrench Architecture

These datasets directly specialize the small local student model to handle:
1. **Local Discovery**: Running environment inspections (ls, grep, cat) locally at 0 paid tokens.
2. **Context Compaction**: Summarizing noisy logs and error traces into minimal high-signal diffs.
3. **Deterministic Repair**: Generating fast single-pass patches against local unit tests before escalating to the Tier 2/3 Teacher at :4000.

---

## 3. Current status and audit

These files are local, ignored inputs. They are not approved training data yet.
Run the mechanical audit from the repository root with:

```powershell
py -3 tools/audit_dataset.py dataset `
  --output phases/phase-2-dataset-audit/dataset-audit.json
```

The audit currently reports parseable JSONL but broad web/research and
finance/crypto content. Source licensing, redaction, task-family fit, and
filtering must be reviewed before any calibration or training run.
