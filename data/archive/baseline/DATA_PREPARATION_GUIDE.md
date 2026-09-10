# Wrench-SLM 语料获取与准备终极实战指南 (Data Acquisition & Preparation Guide)

```
Document Classification : REPRODUCIBLE DATA ENGINEERING RUNBOOK
Location                : data/DATA_PREPARATION_GUIDE.md
Target Dataset          : data/train.jsonl, data/val.jsonl, data/held_out.jsonl
Execution Script        : scripts/acquire_and_prepare_data.py
Rule                    : 20% Core Tools Covering 80% Scenarios (Pareto Principle)
```

---

## 一、语料从哪里拿？全量数据源全景图 (Where to Get the Data)

为了确保小模型在 135M / 0.5B 极小体积下具备真实的工业级执行泛化力，我们**坚决不爬取任何互联网通用闲聊与百科（唐诗宋词）**，数据必须来自以下四大真实工程源：

```
                                   [ 数据采集四大源头 ]
                                            │
        ┌───────────────────┬───────────────┴───────────────┬───────────────────┐
        ▼                   ▼                               ▼                   ▼
【源 1: Hugging Face 金矿】 【源 2: 真实生产网关日志】   【源 3: 双轨 Teacher 蒸馏】 【源 4: 跨平台正交转译】
  • InterCode-Bash            • lean-router/logs              • MiniMax (口语倒装)       • PowerShell AST
  • The-Stack CLI             • 真实 Agent 执行轨迹           • Luna (金标仲裁负样本)    • POSIX Bash
  • BFCL / Gorilla CLI        • 真实 Exit Code & Stdout       • http://localhost:4000    • 成对正交互转
```

### 1. 源头一：Hugging Face 开源高质量子集 (Hugging Face Repositories)
Hugging Face 上虽充斥着 80% 的假大空玩具 API，但有**三大官方认证金矿库**值得抽取：

| 仓库名称 (Hugging Face Repo) | 推荐子集 / Config | 抽取内容与价值 |
| :--- | :--- | :--- |
| **`intercode/intercode-bash`** | `bash` | 真实的交互式 Bash 命令序列、环境变量探查与管道流，带真实 OS 评测。 |
| **`bigcode/the-stack`** | `data/shell` | 开源项目中 Dockerfile、Makefile、CI/CD 脚本中的真实工程命令。 |
| **`gorilla-llm/Berkeley-Function-Calling-Leaderboard`** | `exec_cli` / `rest_cli` | 权威函数调用评测集中的 CLI 命令行子集，具备严密的参数槽位依赖。 |
| **`Salesforce/xlam-function-calling-60k`** | `system_tools` (过滤后) | 抽取其中的系统管理、网络检测、进程管理等纯机械子集。 |

### 2. 源头二：本地 LeanRouter 真实生产网关镜像 (`c:\Users\stanc\github\lean-router\logs`)
* **读取策略**：**严格只读（Zero Mutation Guarantee）**。
* **文件清单**：
  - `logs/tool_calls.log*`：包含历史每一次工具调用的输入、输出、参数与执行结果；
  - `logs/events/*.jsonl`：包含网关审计事件流、耗时、模型路由记录；
* **价值**：最贴近真实业务痛点，包含真实开发者口语与各种边缘异常。

### 3. 源头三：统一网关双轨 Teacher 蒸馏 (`http://localhost:4000/v1`)
* **MiniMax (`minimax` / `minimax-m3`)**：针对一条标准命令（如 `git status`），批量合成 20~30 种不同口吻的口语描述（倒装、缩写、中英混杂）；
* **GPT-5.6 Luna (`gpt5.6-luna`)**：生成对抗性负样本（长链推导、微服务重构架构等要求回抛云端的 `<fallback>` 样本）。

### 4. 源头四：跨平台正交转译器
* 将 Windows 原生命令（PowerShell AST: `Get-Content`, `Test-Path`, `Test-NetConnection`, `Select-String`）
* 与 POSIX 原生命令（Bash: `cat`, `test -e`, `curl`, `grep`）
* 进行一对一真实语法映射扩充，确保模型具备跨平台双语指令理解力。

---

## 二、怎么获取数据？具体获取方法与命令 (How to Acquire the Data)

### 方法 1：从 Hugging Face 自动化下载与抽取
使用 Python `datasets` 库或 `huggingface_hub` 下载特定子集：

```python
# 安装依赖
# pip install datasets huggingface_hub

from datasets import load_dataset

# 1. 抓取 InterCode-Bash 数据集
ds_intercode = load_dataset("intercode/intercode-bash", split="train")

# 2. 抓取 Salesforce XLAM 数据集
ds_xlam = load_dataset("Salesforce/xlam-function-calling-60k", split="train")
```

### 方法 2：一键从本地生产日志中抽取
运行内置日志解析管道：
```powershell
python scripts/ingest_logs.py
```

### 方法 3：运行全自动采集与清洗总控脚本
我们提供了端到端总控脚本，自动完成数据抽取、清洗与入库：
```powershell
python scripts/acquire_and_prepare_data.py
```

---

## 三、怎么准备数据？五阶段清洗与质检流水线 (How to Prepare & Purify the Data)

数据采集下来后，**绝不直接进训练集**，必须经过以下五道严苛的工业洗水检验：

```
[ 原始混合数据流 (HF / 本地日志 / 合成数据) ]
                     │
                     ▼
┌────────────────────────────────────────────────────────┐
│ 阶段 1: 玩具 API 剔除与帕累托 20% 工具过滤               │
│ 彻底删除 weather, hotel, flight 等假大空 Web API 样本   │
│ 仅保留 Git, 终端 CLI, 文件 CRUD, 数据探查, 交互式 Stdin │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 阶段 2: 真实操作系统沙箱语法与执行校验                 │
│ POSIX shlex 词法解析 + PowerShell 引号平衡与 AST 校验   │
│ 过滤掉所有参数缺失、Flag 幻觉与无法解析的破损命令      │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 阶段 3: 协议归一化与有限状态机对齐                     │
│ 统一规范为: {"tool": "exec_command", "args": {...}}     │
│ 严格通过 JsonToolCallFSM 状态机验证                     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 阶段 4: 推测执行安全二元打标 (Safe-Read vs Mutation)    │
│ Safe-Read (只读): git status, cat, curl -> 端侧预执行  │
│ Mutation (破坏性): rm, kill, git commit -> 仅出 Draft  │
│ 注入 5%~8% P0 复杂任务负样本 -> 标记 <fallback>         │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 阶段 5: 确定性 MD5 哈希物理切分 (70 / 15 / 15)         │
│ train.jsonl (70%) | val.jsonl (15%) | held_out.jsonl   │
│ 确保训练集与评测集物理隔离，0 数据泄漏                 │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
               [ 生产就绪标准训练语料库 ]
```

### 关键步骤代码逻辑（内置于 `scripts/acquire_and_prepare_data.py`）：

#### 1. 过滤玩具 API (Drop Toy APIs)
```python
TOY_API_KEYWORDS = {"weather", "forecast", "flight", "hotel", "restaurant", "pizza", "uber", "crypto"}
def is_toy_api(record):
    for kw in TOY_API_KEYWORDS:
        if kw in record["prompt"].lower() or kw in str(record["args"]).lower():
            return True
    return False
```

#### 2. 推测执行安全打标 (Speculative Safety Classification)
```python
SAFE_READ_PREFIXES = ("git status", "git diff", "cat ", "head ", "tail ", "wc ", "netstat", "curl", "pytest", "jq", "sqlite3")
MUTATION_PREFIXES = ("rm ", "rm -rf", "kill ", "Stop-Process", "git commit", "git push", "docker stop", "DROP TABLE")

def classify_safety(tool, args):
    cmd = args.get("cmd", "").strip().lower()
    for pfx in MUTATION_PREFIXES:
        if cmd.startswith(pfx):
            return False, True, True   # safe_read=False, mutation=True, requires_cloud_audit=True
    for pfx in SAFE_READ_PREFIXES:
        if cmd.startswith(pfx):
            return True, False, False  # safe_read=True, mutation=False, requires_cloud_audit=False
    return False, False, False
```

#### 3. 确定性哈希物理切分 (Zero Leakage Partitioning)
```python
# 基于 Record ID 的 MD5 哈希值取模进行物理分割，严禁随机打乱导致的数据泄露
h_val = int(hashlib.md5(record_id.encode()).hexdigest()[:8], 16) % 100
if h_val < 70:
    train_split.append(record)
elif h_val < 85:
    val_split.append(record)
else:
    held_out_split.append(record)
```

---

## 四、一键全流程准备命令 (Run the Pipeline)

在工作区根目录下，执行以下命令即可完成从获取、清洗、打标到分区的全流程：

```powershell
# 1. 运行一键数据准备管道
python scripts/acquire_and_prepare_data.py

# 2. 运行隔离盲测集执行语义验证 (通过率必须 >= 95%)
python scripts/verify_execution.py --split held_out --limit 1000

# 3. 运行全量里程碑审计
python scripts/verify_milestones.py
```

*“不贪多，只求准。用 20% 黄金机械数据，把端侧执行打透。”*  
*—— Wrench-SLM 数据工程规范*
