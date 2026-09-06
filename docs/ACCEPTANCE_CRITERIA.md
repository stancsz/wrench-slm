# Wrench-SLM: Acceptance Criteria & Audit Protocol

```
Document Version : 1.0.0-PROD
Classification   : GATED AUDIT CHECKLIST / AUTOMATED PASS-FAIL
Target System    : Wrench-SLM (Edge Task-Execution Small Language Model)
```

---

## 1. Executive Summary

This document defines the **concrete pass/fail gates** that every proposed checkpoint, LoRA adapter, fine-tuning run, or pull request MUST satisfy before being accepted into the Wrench-SLM production baseline.

There are **no exceptions**, **no subjective reviews**, and **no waivers**. All criteria are verified programmatically via deterministic scripts.

---

## 2. Gated Acceptance Matrix

| Gate | Category | Target Metric | Evaluation Command | Minimum Threshold | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Gate A** | Format & Syntax | JSON Schema Validity | `verify_execution.py --split held_out` | **>= 99.5%** | REQUIRED |
| **Gate B1** | Execution (Win) | Windows PowerShell AST | `verify_execution.py --split held_out` | **>= 95.0%** | REQUIRED |
| **Gate B2** | Execution (POSIX) | Linux/macOS Bash (`shlex` + `bash -n`) | `verify_execution.py --split held_out` | **>= 98.0%** | REQUIRED |
| **Gate B3** | Execution (Agent) | In-Memory Sandbox State Transitions | `verify_execution.py --split held_out` | **>= 95.0%** | REQUIRED |
| **Gate C1** | Latency | Time-To-First-Token ($p_{99}$) | Local RTX 5070 Ti benchmark harness | **<= 30.0 ms** | REQUIRED |
| **Gate C2** | Memory | GPU VRAM Footprint | `nvidia-smi` peak allocated memory | **<= 3.5 GB** | REQUIRED |
| **Gate D1** | Routing | Routine Local Offload Rate | Production trace replay suite | **>= 70.0%** | REQUIRED |
| **Gate D2** | Safety Floor | High-Complexity Escalation | Held-out P0/P1 regression set | **0% false locals** | REQUIRED |
| **Gate E** | Code Hygiene | Ruff Static Lint & Style | `ruff check scripts/ docs/` | **0 errors** | REQUIRED |

---

## 3. Mathematical Definitions & Formulas

### 3.1 Gate A: Schema Validity ($S_{\text{valid}}$)
A generation $y$ is valid if and only if:
1. It parses without error via `json.loads(y)`.
2. It contains exactly the required top-level keys: `tool` (string) and `args` (dictionary).
3. The `args` schema conforms to the tool signature specified in the canonical registry.

$$S_{\text{valid}} = \frac{1}{N} \sum_{i=1}^{N} \mathbb{I}\Big(\text{IsValidSchema}(y_i)\Big) \ge 0.995$$

### 3.2 Gate B: Runtime Execution Rate ($E_{\text{rate}}$)
Evaluated across all supported runtime targets:
$$E_{\text{rate}} = \frac{1}{N} \sum_{i=1}^{N} \mathbb{I}\Big(\text{SandboxExec}(y_i) == \text{SUCCESS}\Big) \ge 0.950$$

Where $\text{SandboxExec}$ checks:
* PowerShell commands: Non-empty, no trailing unclosed quotes/braces/parentheses, no dangling pipeline operators.
* POSIX Bash: Valid token stream via `shlex.split` and exit code 0 under `bash -n`.
* Agent Tools (`write_stdin`, `get_goal`, etc.): Valid parameter structures matching production agent signatures.

### 3.3 Gate C: Latency Constraints ($L_{p99}$)
Measured on a loaded host running Windows 11 with NVIDIA GeForce RTX 5070 Ti (16GB GDDR7, BF16 compute):
$$L_{p99} = \text{Percentile}_{99}\Big(\{T_{\text{end}} - T_{\text{start}} \mid i \in [1, N]\}\Big) \le 30.0\text{ ms}$$

### 3.4 Gate D: Local Offload Rate ($O_{\text{rate}}$)
Evaluated on the routine task partition ($\text{Category} == \text{"routine"}$):
$$O_{\text{rate}} = \frac{N_{\text{executed\_locally}}}{N_{\text{total\_routine}}} \ge 0.700$$

---

## 4. Mandatory Pre-Commit Verification Script

Any agent or contributor submitting changes must run the following automated pipeline:

```powershell
# 1. Verify code linting and formatting (0 errors required)
ruff check scripts/

# 2. Run full execution verification on held-out split (>= 95% pass rate required)
py -3 -X utf8 scripts/verify_execution.py --split held_out --limit 1000

# 3. Confirm LeanRouter source isolation (0 modified files required)
git -C c:\Users\stanc\github\lean-router status --porcelain
```

If any command returns a non-zero exit code or fails a threshold, **the submission is immediately rejected**.
