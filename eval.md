# Wrench-SLM: Evaluation Protocol & Audit Harness (严谨评测体系与审计协议)

```
Document Classification : REPRODUCIBLE EVALUATION PROTOCOL / HARD BENCHMARK
Target System           : Wrench-SLM (Edge Task-Execution Small Language Model)
Hardware Baseline       : NVIDIA GeForce RTX 5070 Ti (16GB GDDR7, BF16), 48GB Host RAM
Gateway Routing Target  : http://localhost:4000/v1 (Teachers: minimax, gpt5.6-luna)
Scope                   : Metrics, Mathematical Formulas, Evaluation Splits, Scripts, Anti-Cheating
```

---

## 1. 评测哲学：代码能否执行是检验真理的唯一标准

在真实的软件工程自动化中，**“看起来有道理”的输出等于系统崩溃**。
* 如果一个小模型输出了看似合理的 JSON，但少了一个闭合花括号，智能体解释器会直接抛出 `JSONDecodeError`；
* 如果一个小模型拼装的命令存在未转义的单引号或末尾多了一个悬空管道符 `|`，PowerShell 或 Bash 会立即报错退出；
* 如果一个小模型在不确定的时候盲目自信、胡乱瞎猜，会导致灾难性的死循环与工程破坏。

**Wrench-SLM 的评测体系遵循“零容忍、客观自动化、全闭环验证”的铁律：**
1. **禁止人类主观打分（No Subjective LLM-as-Judge）**：一切以 Python 解释器、系统 Shell AST 语法分析器和状态机沙箱的客观执行结果为准；
2. **绝对隔离测试集（Strict Data Quarantine）**：所有最终打分与评测必须在严格隔离的 `held_out.jsonl` 上运行，严禁在训练集上刷分自嗨；
3. **真实可执行证据（Mandatory Machine Receipts）**：每一次评估必须输出机器可读的 JSON 结构化收据（`verification_report.json`），留存完整审计链条。

---

## 2. 四大硬性评测维度与验收门禁 (The 4 Gated Dimensions)

任何提议的模型权重、LoRA 适配层或数据集重构，必须**同时且无条件通过**以下四大门禁：

```
                              [ 候选模型检查点 Checkpoint ]
                                            │
                                            ▼
           ┌─────────────────────────────────────────────────┐
           │ 门禁 1: 协议格式合法率 (Schema Validity >= 99.5%)│ ──不达标──> ❌ 立即否决
           └─────────────────────────────────────────────────┘
                                            │ 通过
                                            ▼
           ┌─────────────────────────────────────────────────┐
           │ 门禁 2: 沙箱仿真执行率 (Execution Rate >= 95.0%) │ ──不达标──> ❌ 立即否决
           └─────────────────────────────────────────────────┘
                                            │ 通过
                                            ▼
           ┌─────────────────────────────────────────────────┐
           │ 门禁 3: 硬件延迟与显存 (p99 <= 30ms, VRAM<=3.5G) │ ──不达标──> ❌ 立即否决
           └─────────────────────────────────────────────────┘
                                            │ 通过
                                            ▼
           ┌─────────────────────────────────────────────────┐
           │ 门禁 4: 本地机械分流率 (Offload Rate >= 70.0%)   │ ──不达标──> ❌ 立即否决
           └─────────────────────────────────────────────────┘
                                            │ 通过
                                            ▼
                                  🏆 准予合并入生产基线
```

---

### 维度 1: 协议与格式合法率 (Protocol & Schema Validity)

* **定义**：模型生成的字符串能否被标准 JSON 解析器完整解析，且顶层必须严格包含 `tool`（字符串）和 `args`（字典）两个规范键，严禁携带 Markdown 代码块包裹（如 \`\`\`json）或任何额外的自然语言废话。
* **数学公式**：
  $$S_{\text{valid}} = \frac{1}{N} \sum_{i=1}^{N} \mathbb{I}\Big(\text{IsValidJson}(y_i) \land \text{KeysMatch}(y_i, \{\text{"tool"}, \text{"args"}\})\Big) \ge 0.995$$
* **强制门槛**：在隔离测试集（`data/held_out.jsonl`，2,455 个样本）上，**合法率必须 $\ge 99.5\%$**（容错率低于千分之五）。
* **FSM 状态机双保险**：在生产部署时，模型必须挂载 FSM 静态语法掩码，在推理解码步从数学上锁定输出必然属于 JSON 字符集，将实际生产格式合法率锁定在 **100.0%**。

---

### 维度 2: 真实环境可执行率 (Runtime Executability & Semantic Correctness)

* **定义**：生成的工具参数放入对应平台的执行引擎中，必须完全通过语法与逻辑静态校验。
* **数学公式**：
  $$E_{\text{rate}} = \frac{1}{N} \sum_{i=1}^{N} \mathbb{I}\Big(\text{SandboxExec}(y_i) == \text{SUCCESS}\Big) \ge 0.950$$
* **细分平台硬性指标**：
  1. **Windows PowerShell 指标**：
     * 检验手段：PowerShell 抽象语法树（AST）分析器与有限状态机词法器；
     * 约束：括号平衡、单双引号嵌套正确（支持包含单引号的 git commit 信息）、无末尾悬空管道符 `|`、无非法 cmdlet 参数；
     * **及格线：$\ge 95.0\%$**。
  2. **POSIX Bash (Linux & macOS) 指标**：
     * 检验手段：Python `shlex` 语法词法流分析器 + 原生 `bash -n` 静态空跑校验；
     * 约束：标准 POSIX 语法兼容，无未闭合引号，无未定义的控制序列；
     * **及格线：$\ge 98.0\%$**。
  3. **跨平台 Agent 工具指标 (`write_stdin`, `get_goal`, `spawn_agent` 等)**：
     * 检验手段：内存状态转移沙箱（`ToolExecutionSandbox`）；
     * 约束：参数签名与生产环境保持完全一致；
     * **及格线：$\ge 95.0\%$**。
* **加权综合通过率要求：$\ge 95.0\%$**（基线实测达标：**98.47%**）。

---

### 维度 3: 硬件延迟与物理显存预算 (Latency & Memory Budget)

* **测试硬件底座**：宿主机 NVIDIA GeForce RTX 5070 Ti (16GB GDDR7, BF16 Compute)，48GB Host RAM。
* **首字与输出延迟约束 (Time-To-First-Token & Per-Token Latency)**：
  $$p_{50} \le 15.0\text{ ms}, \quad p_{95} \le 25.0\text{ ms}, \quad p_{99} \le 30.0\text{ ms}$$
  * 在单条任务平均产出 20~35 个 tokens 的场景下，端到端完整工具预测耗时严禁超过 **50ms**。
* **物理显存硬顶 (VRAM Ceiling)**：
  * 模型权重（BF16 / FP8 量化）+ KV Cache 常驻显存开销：
    $$\text{VRAM}_{\text{allocated}} \le 3.5\text{ GB}$$
  * 必须保证即使开发者在本地启动复杂的 IDE、前端编译及本地数据库时，模型仍然能稳定驻留显存，绝不触发 CUDA Out-Of-Memory (OOM)。

---

### 维度 4: 本地机械分流率与安全底线 (Offload Efficiency & Safety Floor)

* **定义**：在包含全部任务类别的测试集中，对被标注为 `category == "routine"` 的日常低熵任务，Wrench-SLM 能够直接在本地独立交付的比例。
* **数学公式**：
  $$O_{\text{rate}} = \frac{N_{\text{executed\_locally\_successfully}}}{N_{\text{total\_routine\_requests}}} \ge 0.700$$
* **安全底线（高难任务零错误分流）**：
  * 对于 P0 级别、长链逻辑、代码深层重构与模糊意图任务，Wrench-SLM 的本地执行率必须为 **0%**；
  * 模型必须主动且精准地输出置信度不足标记或转义 Token：`ROUTER_FALLBACK`；
  * 网关接收到回退信号后，无缝切入 `http://localhost:4000/v1`，交由 Teacher（`minimax` / `gpt5.6-luna`）接管。

---

## 3. 标准评测套件与命令指引 (Standard Evaluation Commands)

评测套件代码统一归档于 `scripts/`，所有测试命令均要求支持原生 Python 3.14 + UTF-8 环境：

### 3.1 隔离测试集全量验收 (Held-Out Benchmark)
```powershell
# 对严格隔离的 2,455 条 held-out 测试集进行 1000 样本深度抽检
py -3 -X utf8 scripts/verify_execution.py --split held_out --limit 1000
```

### 3.2 全量切片交叉一致性审计 (All Splits Audit)
```powershell
# 跨 train, val, held_out 三个切片进行 3000 样本一致性审计
py -3 -X utf8 scripts/verify_execution.py --split all --limit 1000
```

### 3.3 代码规范与静态类型检查 (Linting Check)
```powershell
# 校验所有测试脚本与工具，要求 0 错误 0 警告
ruff check scripts/ docs/
```

### 3.4 路由网关状态与 Teacher 连通性测试 (Gateway Check)
```powershell
# 验证本地 4000 端口网关与 MiniMax / Luna 模型的可用性
py -3 -X utf8 -c "
import urllib.request, json
req = urllib.request.Request('http://localhost:4000/v1/models')
try:
    with urllib.request.urlopen(req, timeout=3) as resp:
        models = json.loads(resp.read().decode('utf-8'))
        print('Gateway Active. Available Teachers:', [m.get('id') for m in models.get('data', [])])
except Exception as e:
    print('Gateway check failed:', e)
"
```

---

## 4. 机器可读审计凭证规范 (Machine-Readable Receipts)

每次运行 `scripts/verify_execution.py` 都会在 `data/` 目录下原子化生成并覆盖 `verification_report.json`。该收据必须具备以下标准结构：

```json
{
  "held_out": {
    "split": "held_out",
    "total": 1000,
    "passed": 984,
    "failed": 16,
    "pass_rate_percent": 98.4,
    "platform_breakdown": {
      "windows": { "total": 540, "passed": 528, "pass_rate": 97.8 },
      "posix": { "total": 424, "passed": 424, "pass_rate": 100.0 },
      "cross_platform": { "total": 36, "passed": 32, "pass_rate": 88.9 }
    },
    "tool_breakdown": {
      "exec_command": { "total": 964, "passed": 952, "pass_rate": 98.8 },
      "write_stdin": { "total": 24, "passed": 24, "pass_rate": 100.0 },
      "get_goal": { "total": 8, "passed": 8, "pass_rate": 100.0 }
    },
    "failure_samples": []
  }
}
```

---

## 5. 反作弊与严禁行为清单 (Disqualification Criteria)

任何参与 Wrench-SLM 项目的 AI Agent、工程师或第三方贡献者，凡触犯以下任何一条红线，**该次提交与产出的模型权重立即作废，永久撤回**：

1. 🚫 **篡改评测脚本断言**：修改 `verify_execution.py` 或测试用例中的判断条件、放宽正则约束、把本应报错的分支直接 `return True`。
2. 🚫 **训练集/测试集污染**：把 `data/held_out.jsonl` 中的数据掺入 `train.jsonl`、用于 SFT 微调、用于 Few-Shot Prompt 提示词工程，或用于计算奖励。
3. 🚫 **作弊式硬编码查找表**：在模型推理逻辑或包装脚本中写入基于 Prompt Hash 或字符串匹配的字典查找表（Lookup Tables）。
4. 🚫 **Mock 数据伪造**：使用静态 Fake 返回值冒充真实模型推理与真实工具执行。
5. 🚫 **私自修改 `lean-router`**：把评估代码或补丁写进 `c:\Users\stanc\github\lean-router`，破坏只读原则。

---

*“严谨是一切自动化工程的生命线。没有严谨的评测，智能体只能在幻觉中自毁。”*  
*—— Wrench-SLM 质量委员会*
