# Wrench-SLM 语料体系规范与设计目标 (Dataset Provenance & Design Specification)

```
Document Classification : PRODUCTION DATASET ARCHITECTURE & INGESTION CONTRACT
Repository Location     : data/
Target Models           : Wrench-Flash (135M) & Wrench-Pro (0.5B)
Current Total Samples   : 19,388 records (train: 13,572 | val: 2,909 | held_out: 2,907)
Latest Version          : v2.1.0-enriched-balanced
Status                  : FROZEN FOR REPRODUCIBILITY / ZERO MUTATION GUARANTEE
```

---

## 1. 语料从哪里拿？五大来源与采集管道 (Where Does the Data Come From?)

Wrench-SLM 坚持**拒绝爬取互联网通用泛化垃圾（唐诗宋词、闲聊问答、百科常识）**。所有语料均来自一线研发智能体的真实执行痕迹与高阶合成管道：

```
                                 [ 数据源采集总线 ]
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
【来源 1: 真实网关日志】        【来源 2: 双轨 Teacher 蒸馏】     【来源 3: 跨平台语法转译】
c:\...\lean-router\logs          http://localhost:4000/v1           PowerShell AST <-> POSIX
  • 真实 Agent 执行轨迹            • MiniMax: 口语倒装变异生成        • Windows / Linux 双盲对齐
  • 真实 Exit Code & Stdout        • Luna: 金标仲裁与负样本注入       • 参数转义与多层引号强化
        │                                │                                │
        └────────────────────────────────┼────────────────────────────────┘
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │        【来源 4: 机械工具专项工程矩阵】         │
                 │   网络诊断 / 环境管理 / 文件生命周期 / Git分支  │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │       【来源 5: P0 越权逃逸对抗负样本】        │
                 │   代码重构 / 复杂推导 -> ROUTER_FALLBACK 注入  │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                 [ 严格 70 / 15 / 15 确定性哈希切分 (无污染) ]
                 data/train.jsonl (13,572) | data/val.jsonl (2,909) | data/held_out.jsonl (2,907)
```

### 1.1 来源一：真实生产网关镜像与流量日志 (Production Gateway Replay Traces)
* **物理路径**：`c:\Users\stanc\github\lean-router\logs`
* **采集机制**：通过 `scripts/ingest_production_logs.py` 与 `scripts/stream_sidecar.py` 旁路只读读取，严格遵循**零侵入、零修改保证（Zero Mutation Guarantee）**。
* **数据实质**：真实智能体（Agent）在终端执行命令的完整上下文，包括用户的初始意图、模型发起的原始 Tool Call、工作目录（`workdir`）、执行平台、退出码与标准输出。
* **覆盖率**：贡献基础的 16,376 条日常真实研发任务切片。

### 1.2 来源二：网关双轨 Teacher 教师模型高阶蒸馏 (Dual-Teacher Distillation Pipeline)
通过统一网关（`http://localhost:4000/v1`）调动两大云端旗舰 Teacher 模型进行高质量数据增强：
1. **MiniMax (`minimax` / `minimax-m3`)** —— **多样性口语合成工厂**：
   - 针对单调的机械指令进行多模态口语化重述（例如将 `git status` 变异为“看看当前仓库干净不干净”、“检查下工作区有没有未提交文件”）；
   - 引入中英文混杂、语法倒装、打字缩写与同义词变异，彻底摧毁小模型靠死记硬背训练集的作弊路径。
2. **GPT-5.6 Luna (`gpt5.6-luna`)** —— **金标判官与消歧裁判**：
   - 负责复杂参数依赖提取（多标志位、正则过滤、管道连接）；
   - 审核高争议样本的槽位合法性，充当训练集的严格质检法官。

### 1.3 来源三：确定性跨平台语法转译 (Deterministic Cross-Platform Transpiler)
针对智能体必须同时在 Windows 和 Linux/macOS 环境稳定执行的痛点，构建确定性语法转译器：
* 将 PowerShell 命令（如 `Get-Content file -TotalCount 10`、`Test-Path ./build`、`Stop-Process -Id 1234`）
* 与 POSIX Bash 命令（如 `head -n 10 file`、`test -e ./build`、`kill -9 1234`）
* 进行严格语义对齐的互转与成对注入，使模型具备跨平台双语指令理解力。

### 1.4 来源四：机械工具专项工程矩阵 (Targeted Mechanical Domain Injection)
针对早期数据集中“工具调用单一、全集中在简单命令”的结构性缺陷，通过 `scripts/enrich_mechanical_tools.py` 注入 **3,012 条高价值工程样本**，覆盖 5 大关键工程领域：
1. **网络与端口诊断**：`netstat -ano`, `Test-NetConnection -Port 4000`, `curl -s http://...`, `lsof -i :8080`, `ps aux | grep node`；
2. **环境与依赖管理**：`pip install -r requirements.txt`, `uv pip install`, `npm list`, `where.exe python`, `which bash`, `env`；
3. **文件生命周期 CRUD**：`New-Item -ItemType Directory`, `Remove-Item -Recurse`, `mkdir -p`, `rm -rf`, `cp -r`, `Test-Path`；
4. **代码质量与静态测试**：`pytest -v`, `ruff check --fix`, `black --check`, `npm test`；
5. **细粒度 Git 高级操作**：`git checkout -b feature/xxx`, `git branch -a`, `git stash`, `git diff --staged`, `git restore`；
6. **交互式 Agent 工具**：`write_stdin`（带 `y/n/q/exit` 交互式确认）、`send_input`、`get_goal`、`update_goal`、`spawn_agent`。

### 1.5 来源五：P0 越权逃逸对抗负样本 (Adversarial Negatives & Complexity Gate)
* **内容**：注入 100+ 条需要复杂架构设计、长长链逻辑推导、跨模块重构的高难 Prompt。
* **真值标注**：强制标注为 `tool="fallback"`, `args={"reason": "requires_deep_reasoning"}`。
* **设计意图**：训练模型识别自身能力的边界（Boundary Awareness），在遇到无法安全执行的超纲任务时，毫秒级放弃并主动回抛云端，严禁在本地自作主张损坏工程。

---

## 2. 数据集核心设计目标 (Dataset Design Objectives)

```
                            [ 数据集设计四大军规 ]
                                      │
     ┌──────────────────┬─────────────┴────────────┬──────────────────┐
     ▼                  ▼                          ▼                  ▼
【1. 零语义杂质】    【2. 推测预执行反薅羊毛】   【3. 100% 格式严密性】 【4. 双阶梯硬件对齐】
 坚决不要唐诗宋词     安全只读直跑 / 写操作草稿    严格 JSON + FSM    Flash 135M / Pro 0.5B
 专精工具参数槽位     省去整轮云端 Token 消耗     杜绝括号错乱破坏   轻量低功耗 / 极速工作站
```

### 目标 1：零语义杂质与专精执行 (Zero Semantic Bloat)
* **核心教条**：坚决不要文学、诗歌、百科、闲聊等无关语料。
* **设计意图**：小模型参数量极为珍贵（Flash 135M / Pro 0.5B），每一组神经元权重必须全部用于记忆工具 Schema、参数提取正则表达式、AST 语法树与执行环境约定。

### 目标 2：推测预执行与反薅羊毛对齐 (Speculative Tool Execution & Anti-Fleecing)
* **反薅羊毛机制**：
  - 云端大模型每生成一次工具调用的 JSON 信封，需消耗大量 Output Tokens 与昂贵的网络延迟；
  - 数据集针对这一痛点设计了**推测预执行标注机制**：
    1. **Safe-Read (只读探查)**：标记为可本地推测执行（`read_only=True`），端侧在 15ms 内跑完并直接把结果注入云端首包 Context，**彻底消灭云端生成该调用的全部 Token 费用**；
    2. **Mutation (破坏性写操作)**：标记为草稿模式（`mutation=True`），端侧仅输出推测 JSON 草稿，由云端大模型做最后一道审核放行，确保绝对安全。

### 目标 3：100% 格式严密性与有限状态机对齐 (100% Schema & FSM Conformity)
* **单一真理标准**：
  ```json
  {"tool": "<canonical_tool_name>", "args": { ... }}
  ```
* 数据集中的每一条样本均经过 `wrench.protocol.validate_call` 与 `wrench.fsm.JsonToolCallFSM` 的双重语法检验，杜绝多余引导词、Markdown 废话包装或转义缺陷，保证与端侧 FSM 约束解码器（Grammar-Constrained Decoding）100% 贴合。

### 目标 4：双阶梯硬件落地场景对齐 (Dual-Tier Hardware Target Compatibility)
* **针对 Wrench-Flash (135M)**：
  - 重点训练单步高频工具（`git status`、`ls/dir`、`cat`、`netstat`、`curl`）；
  - 确保模型权重在 INT4 量化后（< 85MB）仍能在树莓派 4/5 或低功耗 CPU 上以 35ms~50ms 极低延迟稳定推测。
* **针对 Wrench-Pro (0.5B)**：
  - 重点训练多标志位复杂参数组装、多工具调用组合（如 `pip install -r requirements.txt --no-cache-dir`、复杂正则文本过滤）；
  - 赋能本地工作站 RTX 5070 Ti 在 12ms 极速下输出复杂工程草稿。

---

## 3. 日常开发、工程协同与数据处理高频场景矩阵 (High-Frequency Dev, Engineering & Data Matrix)

在真实的 AI 智能体研发与生产环境中，**真正每天被调用成百上千次、严重消耗 Token 的正是以下三大业务主线**。Wrench 的训练语料全力倾斜并覆盖这三大核心支柱：

### 3.1 主线 A：日常代码开发与版本控制 (Code Development & Git Toolchain)
智能体在编写代码时，需要频繁感知上下文与工程状态：
* **工作树与代码比对 (Safe-Read)**：
  - `git status -s` / `git status`（探查仓库当前变更文件）
  - `git diff` / `git diff --staged`（比对未暂存或已暂存修改）
  - `git log -n 5 --oneline`（查看最近提交历史）
  - `git branch -a` / `git tag -l`（检查分支与标签）
* **代码搜索与符号检索 (Safe-Read)**：
  - `rg "def run_eval" src/` / `grep -rn "TODO" .`（快速定位函数或关键词）
  - `fd -e py` / `find . -name "*.jsonl"`（检索指定格式工程文件）
* **版本分支与提交动作 (Mutation Draft-Only)**：
  - `git checkout -b feature/wrench-v2` / `git switch main`（分支创建与切换）
  - `git stash` / `git stash pop`（工作区暂存管理）
  - `git add .` / `git commit -m "..."`（仅生成 Draft 草稿，待审核后提交）

### 3.2 主线 B：数据工程、数据分析与文件探查 (Data Engineering & Analysis)
数据智能体与研发人员在处理数据集、日志与格式化文件时的高频操作：
* **数据结构探查与文件首尾行 (Safe-Read)**：
  - `head -n 20 dataset.jsonl` / `Get-Content dataset.jsonl -TotalCount 20`（查看数据 Schema 样本）
  - `tail -n 50 runtime.log` / `Get-Content runtime.log -Tail 50`（排查最近错误堆栈）
  - `wc -l data/train.jsonl` / `(Get-Content data/train.jsonl).Count`（核对样本总量）
* **JSON 结构化过滤与提取 (Safe-Read)**：
  - `jq '.tool_distribution' data/manifest.json`（抽取指标字段）
  - `jq -r '.[] | .cmd' buffer.jsonl`（纯文本管道过滤）
* **轻量本地数据库与元数据查询 (Safe-Read)**：
  - `sqlite3 app.db ".schema"` / `sqlite3 app.db "SELECT count(*) FROM records;"`（库表结构与数据量探查）
  - `duckdb -c "SELECT * FROM 'data.parquet' LIMIT 5;"`（分析型文件快照）
  - `redis-cli ping` / `redis-cli get gateway_token`（缓存连通性与 Key 状态）
* **Python 动态数据快照 (Safe-Read)**：
  - `python -c "import pandas as pd; print(pd.read_csv('test.csv').shape)"`（数据维数与空值探查）

### 3.3 主线 C：本地容器、微服务与运维诊断 (DevOps, Containers & Services)
后端与系统开发中排查服务与网络的高频工具：
* **服务与端口排查 (Safe-Read)**：
  - `netstat -ano | findstr :4000` / `lsof -i :4000`（定位端口占用 PID）
  - `Test-NetConnection -Port 4000 localhost` / `curl -I http://localhost:4000/health`（网关健康探测）
  - `ps aux | grep uvicorn` / `Get-Process python`（排查常驻服务状态）
* **Docker / 容器编排运维 (Safe-Read / Mutation Gating)**：
  - `docker ps -a`（查看本地运行容器列表，Safe-Read）
  - `docker logs --tail 100 lean-router`（拉取最近服务日志，Safe-Read）
  - `docker compose ps` / `docker compose up -d`（服务编排状态与启动）
* **包管理与编译构建 (Safe-Read & Execution)**：
  - `pip list` / `uv pip list` / `npm list --depth=0`（依赖版本探查，Safe-Read）
  - `pytest -v -k "test_protocol"` / `npm test`（单元测试与回归检验）
  - `ruff check --fix` / `black .`（代码格式化修复）

---

## 4. 当前数据集分布与统计详情 (Current Dataset Manifest)

根据 `data/manifest.json` 最新实测统计：

| 数据切分 (Split) | 记录总数 (Records) | 占比 (%) | 用途与隔离红线 |
| :--- | :--- | :--- | :--- |
| **`data/train.jsonl`** | **13,572** | 70.0% | 仅用于 LoRA / 全参数微调与 GRPO 强化学习训练，严禁泄漏给评估集。 |
| **`data/val.jsonl`** | **2,909** | 15.0% | 训练期 Epoch 验证、Early-Stopping 判定与 Loss 监控。 |
| **`data/held_out.jsonl`** | **2,907** | 15.0% | **物理隔离盲测集**：用于生产门禁审计（`verify_execution.py`）、FSM 状态机验证与防作弊评测。 |
| **全量总计** | **19,388** | 100.0% | 全部支持真实系统环境执行验证。 |

### 操作系统平台覆盖
* **Windows (PowerShell)**: 10,306 条 (53.2%)
* **POSIX (Linux/macOS Bash)**: 8,152 条 (42.0%)
* **Cross-Platform (平台无关 / Stdin / Agent API)**: 930 条 (4.8%)

### 核心业务类别分布
* **日常机械与环境探查 (`routine`)**: 17,840 条 (92.0%)
* **Git 细粒度操作 (`git_operations`)**: 512 条
* **网络与端口诊断 (`network_diagnostics`)**: 360 条
* **代码质量与静态测试 (`code_quality`)**: 240 条
* **交互式 Agent Stdin (`agent_interaction`)**: 160 条
* **文件生命周期 CRUD (`file_crud`)**: 88 条
* **Agent 目标控制与生命周期 (`agent_lifecycle`)**: 60 条
* **云端转派负样本 (`cloud_escalation`)**: 40 条
* **依赖与包管理 (`pkg_management`)**: 36 条
* **环境变量检查 (`env_inspection`)**: 32 条
* **进程诊断与管理 (`process_management`)**: 20 条

---

## 5. 关于 Hugging Face 开源数据集的评估与引入红线 (Hugging Face Ingestion Standard)

1. **局限性**：80% 为假大空 Web API 玩具（查天气、订机票），缺乏物理可执行性，未标注读写副作用。
2. **保留金矿**：仅保留 `InterCode-Bash`、`The-Stack` 脚本切片与 `Berkeley Function Calling Benchmark (BFCL)` 的 CLI 运维工具子集。
3. **四步清洗准入**：**领域白名单过滤 -> OS 真实环境 exit code 0 验证 -> 格式对齐 FSM JSON -> Safe-Read vs Mutation 打标**。

## 6. 语料获取与准备指南 (Data Acquisition & Preparation Guide)

详细的外部开源数据源（Hugging Face、InterCode、BFCL）、本地日志抽取代码、数据五阶段清洗与质检流水线，请参阅：
👉 **[DATA_PREPARATION_GUIDE.md](DATA_PREPARATION_GUIDE.md)**

一键数据采集、清洗、安全打标与分区脚本：
```powershell
# 运行端到端数据获取与准备管道
python scripts/acquire_and_prepare_data.py
```

---

## 7. 语料质量复现与验证命令 (Reproducibility & Verification)

任何进入 `data/` 目录的语料变动，必须通过以下命令全量复核并生成签名收据：

```powershell
# 1. 验证隔离盲测集执行语义成功率 (必须 >= 95.0%)
python scripts/verify_execution.py --split held_out --limit 1000

# 2. 验证全量里程碑 (M1 数据流, M2 标准文档, M4 FSM 语法, M5 奖励, M6 旁路分流)
python scripts/verify_milestones.py
```

*“每一行训练数据，都必须是一张可在真实操作系统兑现的支票。”*  
*—— Wrench-SLM 数据工程委员会*
