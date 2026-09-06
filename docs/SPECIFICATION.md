# Wrench-SLM: Master Engineering Specification & Operational Standard

```
Document Version : 1.0.0-PROD
Classification   : HARD SPECIFICATION / NON-NEGOTIABLE
Target System    : Wrench-SLM (100% Pure-Blood Nano-Transformer, 0 External Base Weights)
Hardware Baseline: NVIDIA GeForce RTX 5070 Ti (16GB GDDR7, BF16 / FP8), 48GB Host RAM
Gateway Routing  : http://localhost:4000/v1 (Teachers: minimax, gpt5.6-luna)
Deployment Mode  : LeanRouter Gateway Sidecar (Daemon / Docker, Port 4010)
Scope            : Engineering Standards, Motivation, Training, Experimentation, Acceptance Gates
```

---

## 1. Motivation & Architectural Anti-Goals

### 1.1 The Fundamental Problem
Modern autonomous software engineering agent loops generate tens of thousands of intermediate tool-call requests. Empirical analysis of production routing logs (`lean-router/logs/`) reveals that **74.8% to 81.2% of all agent tool invocations are purely mechanical, deterministic, and low-entropy**:
* Running shell commands (`git status`, `git diff`, `pytest`, `ruff check`, `head -n 20 <file>`, `ls`, `wc -l`)
* Feeding stdin input to interactive sub-processes (`write_stdin`, `send_input`)
* Polling goal and task status (`get_goal`, `update_goal`)
* Orchestrating sub-agent life-cycles (`spawn_agent`, `wait_agent`)

Routing these routine, mechanical operations to 600-billion-parameter cloud frontier models (e.g., Claude 3.5 Sonnet, GPT-4o) introduces three catastrophic engineering bottlenecks:
1. **Latency Overhead**: Network roundtrips plus cloud time-to-first-token (TTFT) consume **800ms to 2,500ms** per tool call.
2. **Economic Waste**: Routine commands burn millions of tokens per task, inflating per-run operational costs by up to \$12.00/hour.
3. **External Vulnerability**: Network jitter, rate limits (HTTP 429), and cloud provider outages stall the entire agent loop.

### 1.2 The Wrench-SLM Mission
**Wrench-SLM** is an edge-native, sub-1-billion parameter model (0.5B base architecture) purpose-built to act as the agent's mechanical "wrench":
* Offload **>= 70%** of routine, mechanical tool invocations locally on consumer GPU hardware.
* Deliver tool predictions in **< 30ms (p99)** with **0 cloud tokens consumed**.
* Yield immediately to cloud frontier teachers (`minimax`, `gpt5.6-luna` via `http://localhost:4000/v1`) whenever semantic complexity, open-ended reasoning, or architectural planning is detected.

---

### 1.3 Post-Mortem of Flawed Past Attempts (Strictly Prohibited Anti-Patterns)

Future contributing agents and developers are **strictly prohibited** from repeating the design pathologies that compromised earlier projects (such as `leanrouter-token-shield`):

| Anti-Pattern | Root Pathology | Why It Failed | Strict Wrench-SLM Mandate |
| :--- | :--- | :--- | :--- |
| **Fake Safety Shields** | Keyword substring filters (`unsafe_fragments = ["rm -rf", "drop table"]`) | High false-positive rate on routine commands (`rm -rf build/`, `git clean -fd`); bypassed trivially by whitespace/aliases (`rm -r -f`). | **NO pseudo-safety substring filtering.** Tool execution safety is handled exclusively by OS sandboxing and file-permission jails. |
| **Synthetic Template Delusion** | Handcrafting synthetic tool-call templates (`"send this to local"`) | Model memorizes artificial phrasing; suffers 90%+ out-of-distribution failure when deployed on real developer queries. | **100% Real Production Data.** All training data is extracted from verified production agent logs (`tool_calls.log*`, `events/*.jsonl`). |
| **Unconstrained DPO Refusal Collapse** | Applying Direct Preference Optimization (DPO) to train refusal behavior | Reward hacking: the model learns that refusing all queries minimizes KL penalty, collapsing JSON syntax validity from 100% to 63% and rendering the model useless. | **Subjective DPO is BANNED.** Policy optimization is performed solely via GRPO with deterministic Python runtime compiler/execution rewards. |
| **Mock / Buzzword Theater** | Declaring success using mock test functions or synthetic benchmarks | Code that does not actually execute in real runtimes breaks immediately when deployed. | **Rigid Execution Verification.** Every training split must pass AST/runtime parser execution verification with >= 95% pass rate. |

---

## 2. Non-Negotiable Acceptance Criteria (Gated Quality Benchmarks)

Before any model checkpoint, adapter, or dataset modification can be merged or deployed, it must pass **all four Acceptance Gates** synchronously. Failure in any single gate results in an immediate, automated rejection.

```
       [ Proposed Wrench-SLM Checkpoint / Artifact ]
                            │
                            ▼
         ┌─────────────────────────────────────┐
         │ GATE A: Schema & Syntactic Validity │ ──Fail──> [ REJECTED ]
         │ (>= 99.5% valid JSON, 0 format bug) │
         └─────────────────────────────────────┘
                            │ Pass
                            ▼
         ┌─────────────────────────────────────┐
         │ GATE B: Runtime Execution & Accuracy│ ──Fail──> [ REJECTED ]
         │ (>= 95.0% pass in execution sandbox)│
         └─────────────────────────────────────┘
                            │ Pass
                            ▼
         ┌─────────────────────────────────────┐
         │ GATE C: Hardware Latency & Footprint│ ──Fail──> [ REJECTED ]
         │ (p99 <= 30ms, VRAM <= 3.5GB on 5070)│
         └─────────────────────────────────────┘
                            │ Pass
                            ▼
         ┌─────────────────────────────────────┐
         │ GATE D: Offload Rate & Safety Floor │ ──Fail──> [ REJECTED ]
         │ (>= 70% routine offload, 0 P0 drop) │
         └─────────────────────────────────────┘
                            │ Pass
                            ▼
               [ ACCEPTED FOR PRODUCTION ]
```

### Gate A: Schema & Syntactic Validity (Threshold: >= 99.5%)
* **Metric**: Ratio of generated outputs that strictly parse into valid JSON matching the canonical tool schema:
  $$\text{Schema Validity} = \frac{N_{\text{valid\_json\_conforming}}}{N_{\text{total\_eval}}} \ge 0.995$$
* **Evaluation Set**: Held-out production evaluation split (`data/held_out.jsonl`, $N = 2,455$).
* **Requirement**: 0 schema violations. If a tool expects `{"cmd": "...", "workdir": "..."}`, generating stringified JSON, markdown code blocks, or missing keys is an automatic failure.

### Gate B: Runtime Execution & Accuracy (Threshold: >= 95.0%)
* **Metric**: Pass rate in the automated Tool Execution Sandbox (`scripts/verify_execution.py`):
  $$\text{Execution Pass Rate} = \frac{N_{\text{syntax\_and\_exec\_valid}}}{N_{\text{total\_samples}}} \ge 0.950$$
* **Platform Distribution**:
  * **Windows PowerShell**: Verified via structural AST lexer and PowerShell parser -> **>= 95.0%**.
  * **POSIX Bash (Linux / macOS)**: Verified via `shlex` stream tokenization and `bash -n` -> **>= 98.0%**.
  * **Cross-Platform Agent Tools**: Schema and argument integrity verified -> **>= 95.0%**.
* **Zero Syntax Hallucinations**: No unescaped newlines, trailing pipes (`|`), unclosed quotes, or nonexistent cmdlet parameters.

### Gate C: Hardware Latency & Memory Footprint (Threshold: p99 <= 30ms, VRAM <= 3.5GB)
* **Target Hardware**: Local NVIDIA GeForce RTX 5070 Ti (16GB GDDR7, Blackwell/Ada architecture, CUDA 12.8).
* **Latency Benchmarks**:
  * $p_{50} \le 15.0\text{ ms}$
  * $p_{95} \le 25.0\text{ ms}$
  * $p_{99} \le 30.0\text{ ms}$
* **Memory Ceiling**:
  * Model Weights (BF16 / FP8 quantized) + KV Cache $\le 3.5\text{ GB}$ VRAM.
  * Must run concurrently alongside heavy IDE processes without triggering CUDA Out-Of-Memory (OOM).

### Gate D: Offload Rate & Safety Floor (Threshold: >= 70.0% Offload, 0% P0 Regressions)
* **Local Offload Rate**:
  $$\text{Offload Rate} = \frac{N_{\text{routine\_tasks\_handled\_locally}}}{N_{\text{total\_routine\_requests}}} \ge 0.700$$
* **Zero P0 Regressions**: If a request involves architectural refactoring, complex logic, multi-file code synthesis, or multi-modal analysis, Wrench-SLM must emit an escalation token (`ROUTER_FALLBACK`) to route the request to Teacher (`minimax` / `gpt5.6-luna`).
* **Under-confidence over Delusion**: A false prediction executed locally causes catastrophic loop failures; a deferred task simply costs a few cents on the cloud. When uncertain ($P(\text{tool}) < 0.85$), the model **must yield**.

---

## 3. Frozen Training Methodology

All training runs must adhere strictly to the following three-phase pipeline. Deviating from these phases or inserting arbitrary fine-tuning techniques (such as DPO or PPO with subjective LLM-as-judge) is prohibited.

```
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Supervised Fine-Tuning (LoRA SFT)                             │
│ - Base Model : Qwen2.5-0.5B-Instruct / Llama-3.2-1B                     │
│ - Precision  : BF16 native (RTX 5070 Ti)                                │
│ - Data       : data/train.jsonl (11,469 augmented real traces)         │
│ - Targets    : q_proj, k_proj, v_proj, o_proj, gate_proj, up/down_proj  │
│ - Rank / Alpha: r=16, alpha=32, dropout=0.05                           │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: Finite State Machine (FSM) Guided Decoding                     │
│ - Engine     : Outlines / LM-Format-Enforcer / Guidance                │
│ - Mechanism  : Regex-constrained token masking at inference step       │
│ - Guarantee  : 100% JSON syntactic validity by construction             │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: Group Relative Policy Optimization (Local GRPO)               │
│ - Algorithm  : GRPO (DeepSeek-R1 style, no separate Critic model)      │
│ - Rollouts   : G=4 completions per prompt                              │
│ - Reward 1   : JSON Syntax Validity (+1.0 / -2.0)                      │
│ - Reward 2   : AST Runtime Executability (+1.5 / -1.5)                 │
│ - Reward 3   : Parameter Exact Match with Teacher (+2.0 / 0.0)         │
│ - Reward 4   : Escalation Honesty (+1.0 for yielding on complex tasks) │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Phase 1: LoRA Supervised Fine-Tuning (SFT)
* **Dataset**: `data/train.jsonl` containing 11,469 real production tool calls (Windows PowerShell, POSIX Bash, and cross-platform agent tools).
* **Format Conditioning**: Every input is conditioned with explicit platform context:
  * Windows: `Execute shell command (powershell on Windows): <intent>`
  * Linux/macOS: `Execute shell command (bash on Linux/macOS): <intent>`
  * Cross-Platform: `Execute agent tool: <intent>`
* **Loss Function**: Cross-entropy loss computed **strictly on the tool call tokens** (canonical JSON), with prompt tokens masked (`label = -100`).

### 3.2 Phase 2: Finite State Machine (FSM) Guided Generation
* Standard language model decoding is prone to minor syntax errors (missing closing braces, stray quotes).
* At runtime, Wrench-SLM generation is constrained via an FSM grammar mask. The vocabulary distribution at step $t$ is masked so that only tokens consistent with the JSON tool grammar are assigned non-zero probability:
  $$P(y_t \mid y_{<t}, x) = 0 \quad \forall y_t \notin \text{AllowedTokens}(\text{FSM\_State}_t)$$
* This ensures that 100% of generated outputs are well-formed JSON objects.

### 3.3 Phase 3: Local GRPO (Group Relative Policy Optimization)
To eliminate reliance on fragile subjective preference models, Wrench-SLM employs **GRPO with deterministic runtime reward functions**:
* For each input $x$, sample a group of $G=4$ candidate outputs $\{y_1, y_2, y_3, y_4\}$.
* Compute reward $R(y_i)$ via pure Python automated execution verification:
  $$R(y_i) = r_{\text{json\_valid}}(y_i) + r_{\text{ast\_exec}}(y_i) + r_{\text{param\_match}}(y_i, y^*) + r_{\text{escalation}}(y_i)$$
* Normalize advantages across the group:
  $$A_i = \frac{R(y_i) - \text{mean}(\{R(y)\})}{\text{std}(\{R(y)\}) + \epsilon}$$
* Update policy parameters $\theta$ without requiring a memory-heavy critic network, allowing full GRPO training within the 16GB VRAM of the RTX 5070 Ti.

---

## 4. Frozen Experimental Protocol & Replay Harness

### 4.1 Deterministic Evaluation Harness
To prevent statistical cherry-picking, all experimental results must be generated using the frozen evaluation script:
```powershell
py -3 -X utf8 scripts/verify_execution.py --split all --limit 1000
```
* **Random Seed**: Fixed to `42` for all data splits, shuffles, and initialization.
* **Data Isolation**: `data/held_out.jsonl` ($N = 2,455$) is strictly isolated. Under no circumstances may held-out data be used for SFT training, reward calculation, or prompt few-shot examples.

### 4.2 Teacher Model Gateway Configuration
When training involves distillation or comparative evaluation, Teacher completions must be sourced from the local router gateway:
* **Gateway Endpoint**: `http://localhost:4000/v1`
* **Default Fast Teacher**: `minimax` (`minimax/minimax-m3`)
* **Default Frontier Teacher**: `gpt5.6-luna` (or configured Claude/OpenAI high-tier fallback)
* **Timeout Budget**: 15,000ms. If the Teacher does not respond within the timeout, the gateway falls back to deterministic local rule engines.

---

## 5. Agent Governance & Anti-Cheating Code of Conduct

Any AI agent, sub-agent, or human developer contributing to the Wrench-SLM repository must adhere to the following **Five Immutable Commandments**:

1. **COMMANDMENT I — NO TEST TAMPERING**: Never modify, weaken, or bypass assertions in verification scripts (`verify_execution.py`, test suites) to artificially inflate benchmark scores. Tests are immutable ground truth.
2. **COMMANDMENT II — NO HARDCODED RESPONSES**: Never write lookup tables, hash maps, or hardcoded if-else statements mapping evaluation prompts directly to target outputs. Evaluation must reflect true model generalization.
3. **COMMANDMENT III — ZERO LEANROUTER SOURCE MODIFICATIONS**: The `c:\Users\stanc\github\lean-router` repository is strictly **READ-ONLY**. Under no circumstances should any source file, configuration, or test in `lean-router` be edited or committed. All work must live exclusively inside `c:\Users\stanc\github\portfolio\wrench-slm`.
4. **COMMANDMENT IV — MANDATORY LINTING INTEGRITY**: All Python code must pass `ruff check scripts/` with **0 errors and 0 warnings**. Unused imports, trailing whitespace, bare exceptions, and unformatted code are grounds for immediate build rejection.
5. **COMMANDMENT V — VERIFIABLE AUDIT TRAILS**: Every claim of accuracy, speed, or offload improvement must be accompanied by a reproducible JSON execution receipt generated by the verification suite and committed to `data/`.

---

## 6. Repository Layout & File Manifest

```
wrench-slm/
├── README.md                      # Public project overview & quickstart
├── docs/
│   ├── SPECIFICATION.md           # This document (Master Technical Standard)
│   └── ACCEPTANCE_CRITERIA.md     # Quick-reference audit checklist & gates
├── data/
│   ├── train.jsonl                # 11,469 verified training records
│   ├── val.jsonl                  # 2,452 validation records
│   ├── held_out.jsonl             # 2,455 strictly isolated test records
│   ├── manifest.json              # Checksums, record counts & split distribution
│   └── verification_report.json   # Machine-readable execution verification receipt
├── scripts/
│   ├── ingest_logs.py             # Read-only production log extraction pipeline
│   ├── cross_platform_transpile.py# Windows -> Linux/macOS dataset transpiler
│   └── verify_execution.py        # Tool execution & runtime syntax verification suite
└── tests/                         # Unit tests & regression suites
```

---

*Authored and Ratified: 2026-09-06*  
*Standard Governing Body: Autonomous Systems Core Engineering Team*
