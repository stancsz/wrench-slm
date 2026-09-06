# Wrench-SLM: Project Goal & Core Purpose (目标定位与立项初衷)

```
Document Classification : NORTH STAR CHARTER / FOUNDATIONAL MISSION
Target Architecture     : Wrench-SLM (Native from-scratch Nano-Transformer, 0 External Base Weights)
Hardware Baseline       : NVIDIA GeForce RTX 5070 Ti (16GB GDDR7, BF16 / FP8), 48GB Host RAM
Gateway Routing Target  : http://localhost:4000/v1 (Teachers: minimax, gpt5.6-luna)
Deployment Mode         : LeanRouter Gateway Sidecar (Autonomous In-a-Loop Daemon, Port 4010)
Scope                   : Motivation, Philosophy, Division of Labor, Anti-Goals, Decision Rules
```

---

## 1. 核心宗旨 (The Core Mission)

> ### 🎯 北极星目标 (The North Star Objective)
> **在单张消费级 GPU (RTX 5070 Ti 16GB) 上，构建一个具备真实泛化力、100% 结构化协议交付的端侧执行小模型（Wrench-SLM）。在保证交付可靠性不低于旗舰模型的前提下，将 70% ~ 80% 的高频机械工具调用就地在本地毫秒级（< 30ms）消灭，为整个智能体系统实现端到端 0 云端 Token 消耗与 10 倍延迟削减。**

Wrench-SLM 不是一个通用的聊天机器人，不是一个泛化的世界知识问答引擎，更不是一个写散文抒情诗歌的模型。

**Wrench（扳手）的唯一定位是工程智能体的“一线机械装配工”（Hands-On Execution Worker）**：
* 专门负责拧紧软件工程中最琐碎、最繁重、最机械的螺丝钉；
* 专精于精准提取参数、无缝装配结构化 JSON、验证环境状态并直接执行工具调用；
* 绝不越权，在遇到长链逻辑、架构规划与高难思考时，毫秒级将控制权交回云端旗舰模型。

---

## 2. 为什么必须做 Wrench-SLM？(The Economic & Engineering Reality)

### 2.1 真实生产环境的 80/20 法则
通过对真实的路由生产日志（`lean-router/logs/` 中的数万条真实轨迹）进行全量深度审计，我们发现一个不可忽视的事实：

$$\textbf{生产环境中 74.8\% 到 81.2\% 的 Agent 工具调用是纯机械、低熵的日常操作}$$

这些操作包括但不限于：
1. **基础 Shell 探测与环境感知**：
   * `git status`, `git diff`, `git log --oneline -n 10`
   * `head -n 20 <file>`, `cat <file>`, `wc -l <file>`
   * `pytest tests/unit/`, `ruff check scripts/`
   * `ls -la`, `cd <dir>`, `echo ok`
2. **交互式进程的标准输入写入**：
   * `write_stdin`（向 REPL 或正在运行的命令发送交互字符串或 `q` 退出信号）
   * `send_input`（向运行中的子任务分发输入）
3. **状态与目标轮询**：
   * `get_goal`（获取当前激活目标的状态与进度）
   * `update_goal`（更新任务步骤完成度）
4. **子 Agent 生命周期编排**：
   * `spawn_agent`, `wait_agent`, `multi_agent_v1`

### 2.2 传统架构的三大灾难性瓶颈
将上述机械操作无差别打包发送给 6000 亿参数的云端前沿大模型（如 Claude 3.5 Sonnet、GPT-4o），在工程上是极度不可接受的：
1. **公网与首字延迟（TTFT）灾难**：
   每一次工具调用需要经历公网往返 + 云端大模型排队与 Prefill，耗时 **800ms 到 2500ms**。在一个需要几十步探索的 Agent 循环中，仅等待工具返回就要消耗数分钟。
2. **资金与 Token 惊人浪费**：
   为了执行一行 `git status`，不得不把前文几万字的项目上下文一次次重新编码，单次任务花费可达 **\$2.00 ~ \$12.00**，造成巨大的经济失血。
3. **外部网络抖动与脆弱性**：
   依赖公网 API 会随时遭遇 HTTP 429 限流、供应商宕机或网络丢包，导致整个自动化运维与编程流水线完全卡死。

### 2.3 硬件与端侧边缘计算的契机
随着现代消费级 GPU 算力的飞跃，我们本地拥有的硬件底座是极其强大的：
* **GPU**：NVIDIA GeForce RTX 5070 Ti（16GB GDDR7，最新架构，原生硬件级 BF16/FP8 矩阵运算）；
* **Host**：48GB 物理内存，PCIe 高速通道。

一个精细剪裁、高质量微调并结合语法约束的 **0.5B ~ 1B 参数小模型**，在 RTX 5070 Ti 上常驻仅占 **1GB 左右显存**，端到端推理时间 **< 30ms**，吞吐高达 **> 150 tokens/s**。
这意味着：**80% 的机械劳动完全可以在本地免费、瞬间、零 Token 消耗地直接完成！**

---

## 3. 能力边界与分工架构 (Division of Labor)

Wrench-SLM 与云端旗舰 Teacher 之间不是互相替代的关系，而是严格明确的流水线分工合作：

```
                    [ 用户的真实复杂工程任务 ]
                               │
                               ▼
        ┌─────────────────────────────────────────────┐
        │        Cloud Frontier Teacher (P0/P1)       │
        │  (minimax / gpt5.6-luna @ localhost:4000)   │
        │  * 架构设计 / 复杂推导 / 宏观战略 / 代码重构 │
        └─────────────────────────────────────────────┘
                               │
              拆解出具体离散的机械行动指令 (Action Intent)
                               │
                               ▼
        ┌─────────────────────────────────────────────┐
        │            Wrench-SLM Edge Worker           │
        │       (0.5B + Nano 本地常驻，<30ms)         │
        │  * 精准参数提取 (exec_command, stdin, goal) │
        │  * 100% 格式合法交付 (FSM 语法状态机约束)   │
        │  * 跨平台抹平 (Windows PowerShell / POSIX)  │
        │  * 本地环境直接探查与测试闭环               │
        └─────────────────────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
   [ 任务确信 P >= 0.85 ]               [ 遇到模糊/长链复杂逻辑 ]
   在本地直接消灭，0 Token 消耗          立即回抛 ROUTER_FALLBACK
   单次耗时 < 30ms                      退回云端 Teacher 处理
```

### 3.1 属于 Wrench-SLM 的领地（坚决就地拿下）
* 明确指令下的文件读写与行号提取；
* 标准构建、测试、代码扫描命令拼装（`pytest`, `cargo check`, `npm test`）；
* Git 版本控制检查、提交信息组装与 diff 获取；
* 正在运行的子进程标准输入交互（REPL 喂入、日志 tail、退出确认）；
* 跨平台命令语法转译（自动适配 Windows PowerShell 与 macOS/Linux Bash）。

### 3.2 严禁 Wrench-SLM 越权的领地（坚决主动放弃）
* 模糊需求的开放性架构设计与需求澄清；
* 跨越十几个文件的深层业务逻辑重构；
* 复杂的安全合规审查与伦理仲裁；
* 复杂数学证明与长程算法推导。
* **准则**：**宁可退回云端花几分钱，绝不在端侧瞎猜导致系统死循环。一旦小模型对参数或工具的置信度低于 0.85，必须立即返回 `ROUTER_FALLBACK` 触发兜底。**

### 3.3 闭环飞轮：网关生产数据自进化与循环训练 (The Gateway-Mining Continuous Loop)

Wrench-SLM 绝不是一次微调就封板的静态死模型，而是**与生产网关 (`http://localhost:4000/v1`) 共生、永远在后台循环训练的自进化有机体 (Self-Evolving Flywheel)**：

```
           [ 网关生产生态 Gateway (localhost:4000 / lean-router) ]
                                    │
                       真实流量驱动 │ 捕获每一次工具调用
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │ 1. 成功样本实时采掘器 (Tool Call Success Miner)          │
       │    * 强成功过滤: 仅采集 real success (exit_code==0 / 正常)│
       │    * Wrench 相关性过滤: 专精机械工具 (exec, stdin, goal)  │
       │    * 绝对防污染: 自动对 Prompt 哈希比对，隔离测试集 0 渗透│
       └─────────────────────────────────────────────────────────┘
                                    │
                      高质量增量样本 │ + 20%~30% 黄金历史回放
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │ 2. 常驻循环微调守护者 (Continuous In-a-Loop Trainer)     │
       │    * RTX 5070 Ti 单卡常驻 (BF16, LoRA / GRPO 小步快跑)    │
       │    * 持续自监督微调与环境奖励自进化 (No Refusal DPO)     │
       └─────────────────────────────────────────────────────────┘
                                    │
                         候选新权重 │ 自动化全量门禁审计
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │ 3. 影子金丝雀验收与热重载 (Canary Verification & Reload) │
       │    * 影子双跑验证: 分歧率 <= 1.0%, 显存零泄漏            │
       │    * 持续循环训练，直到系统彻底达到 Mature & Useful 标准  │
       └─────────────────────────────────────────────────────────┘
```

#### 3.3.1 样本采掘三项硬铁律 (Continuous Mining Strict Rules)
1. **Tool Call 必须真实成功 (Success Verification)**：
   严禁采集执行失败、报错抛出异常或超时截断的脏轨迹。只有返回 `exit_code == 0`、通过 Python AST 验证或在环境中成功产生期望动作的样本，才准许进入增量训练池。
2. **严格收敛于 Wrench 领域 (Wrench Domain Relevance)**：
   专注采掘属于 Wrench 领地的机械指令（环境探查、文件读写定位、进程交互、测试驱动、状态轮询）。凡涉及长篇发散对话、宏观需求推演等任务，直接剔除或仅保留 Fallback 标准范例。
3. **隔离测试集防污染与去重 (Strict Quarantine & Deduplication)**：
   每次进入循环训练队列前，严格校验 Prompt 哈希，确保 `data/held_out.jsonl` 等测试切片绝对物理隔离，防止过拟合与刷分自欺。

#### 3.3.2 终极收敛：何为“成熟可用”？(Definition of "Mature & Useful Enough")
循环训练不是无休止的盲目发散，而是必须向明确的工程标准收敛。当系统在网关真实流量中**连续 72 小时稳定满足以下全部 5 项硬性验收指标**时，方可判定为正式“成熟可用 (Mature & Useful Enough)”：
1. **协议合法率 100%**：挂载 FSM 状态机输出数学级 100% 合法，模型裸输出 JSON 结构合法率 $\ge 99.5\%$；
2. **跨平台真实执行成功率 $\ge 96.5\%$**：在 Windows PowerShell、POSIX Bash 和 Agent 内存沙箱中命令执行率稳定超越云端 Teacher 基线；
3. **日常机械分流率稳定 $\ge 80.0\%$**：真实生产环境中 80% 以上的高频机械工具调用在本地毫秒级闭环，0 云端 Token 消耗；
4. **影子金丝雀分歧率 $\le 1.0\%$**：与云端 Teacher (`minimax` / `gpt5.6-luna`) 的真实意图分歧低于百分之一；
5. **本地毫秒级与显存恒定**：单次推理耗时 $p_{99} \le 25\text{ms}$，模型及 KV Cache 常驻显存严格锁定在 $2.5\text{ GB}$ 以内，零内存泄漏。

达到该标准后，模型即转入“稳态巡航期”——继续常驻监听，仅对新引入的工具协议或低频边界用例做自适应吸纳。

---

## 4. 彻底反思：前期失败尝试的血泪教训 (Anti-Goals)

做这个项目的 Agent 与开发者必须彻底汲取前置探索（如 `leanrouter-token-shield`）走入歧途的教训，**以下 4 项病态做法永久列入黑名单，严禁再碰**：

### ❌ 禁令一：严禁做“伪安全关键词过滤盾牌”（Fake Safety Shields）
* **历史教训**：试图让小模型通过 `unsafe_fragments = ["rm -rf", "drop table"]` 这种简陋的字符串匹配充当安全防火墙。
* **为什么失败**：白名单/黑名单关键词过滤极易被多余空格、变量替换（`rm -r -f` 或 `python -c "import shutil; shutil.rmtree(...)"`）绕过，而真正的合规清理命令（`rm -rf build/`）又被疯狂误杀。
* **严正结论**：小模型不承担安全防御职能！安全性由操作系统沙箱（Docker/AppContainer/Jail）、执行权限和网关策略负责。小模型的任务只有一个：**把螺丝拧准、把命令敲对**。

### ❌ 禁令二：严禁搞“自欺欺人的合成数据模板”（Synthetic Template Delusion）
* **历史教训**：闭门造车，编写大量类似 `"send this to local"`、`"please execute foo"` 的合成模板生成虚假数据集。
* **为什么失败**：模型在合成数据上得分 100%，但在面对真实开发者复杂、带上下文、混杂脏数据的提问时，发生严重的分布外（OOD）崩溃。
* **严正结论**：**必须 100% 取材于真实生产日志**。所有训练语料均来源于已确认执行完成的 `tool_calls.log*` 和 `events/*.jsonl`。

### ❌ 禁令三：严禁无脑使用 DPO 训练拒答对齐（Refusal Collapse）
* **历史教训**：引入直接偏好优化（DPO）强行训练小模型“拒答危险指令”。
* **为什么失败**：由于奖励模型过度惩罚未拒答，导致小模型奖励作弊（Reward Hacking）——模型学会了对一切输入都输出拒绝词，最终导致模型最基本的 JSON 结构化输出能力从 100% 塌缩到 63%，彻底沦为不可用的砖头。
* **严正结论**：**严禁在 Wrench-SLM 上使用主观偏好 DPO**。模型对齐只通过客观编译器/执行器奖励（GRPO）推进，不训练无意义的拒答。

### ❌ 禁令四：严禁花拳绣腿与假大空（Buzzword Theater）
* **历史教训**：引入花哨的概念名词、复杂的空头理论，评测时使用 Mock 函数自欺欺人，代码一落地到真实环境直接抛出语法错误。
* **严正结论**：所有成果必须以“在 Windows/Linux 真实解释器下能否成功执行”为唯一标准。

---

## 5. 每一项技术决定的“一票否决”准绳 (The 4 Decision Rules)

本项目的所有代码提交、算法引入、数据构建与架构演进，必须逐字对照以下 4 条基准严格审查。**任何一项不合格，直接一票否决**：

1. **真实干活准绳 (Does it do real work?)**  
   这项改动是否直接提升了模型在本地“提取参数、调用工具、终结请求”的能力？如果只是为了做虚假的元标签预测、分类自嗨或无法转化为实际动作的玩具，**直接否决**。
2. **交付完整性准绳 (Does it protect protocol delivery?)**  
   任何技术（无论是微调、量化还是强化学习）如果损害了最核心的 JSON 语法合法率（Schema Validity）与工具执行成功率，**无论理论叙事多么高大上，必须立刻撤回**。
3. **极简可复现准绳 (Is it reproducible on bare-metal?)**  
   方案是否能在单张 RTX 5070 Ti 和 Windows/Linux 原生 Python 环境下稳定运行？如果引入了极度脆弱的特定环境编译依赖或不可控黑盒，**直接否决**。
4. **反假大空准绳 (Is it free of buzzword theater?)**  
   坚决不为了凑概念而硬塞与执行无关的模块。安全交由系统层规则与审计，小模型只专注把任务做成。凡有虚名者，**直接切除**。

---

## 6. 核心交付与演进路线 (Key Milestones)

| 阶段 | 核心抓手 | 严格验收标准 | 状态 |
| :--- | :--- | :--- | :--- |
| **M1: 真实基座数据流** | 只读解析 `lean-router/logs`，建立跨平台（Win/Linux）标准化数据集 | 16,376 条高质量样本，跨平台语法验证通过率 $\ge 98\%$，`lean-router` 源码 0 碰触 | ✅ **已达成** |
| **M2: 规范与准绳固化** | 制定严谨的技术规范与防作弊军规，建立自动化门禁 | `goal.md`, `eval.md`, `docs/SPECIFICATION.md` 全部就绪，Ruff 0 警告 | ✅ **已达成** |
| **M3: 纯血 NanoWrench 筑基** | 纯手搓 28M Transformer，0 借用外部底座，从零随机初始化，专属高密词表预热 | Held-out 结构合法率 $\ge 98.5\%$，工具参数准确率 $\ge 95\%$ | ⏳ **准备就绪** |
| **M4: FSM 语法约束装配** | 集成轻量静态 Trie/Regex 状态机，解码步实施 Token 掩码 | 结构化交付合法率达到**数学级 100%**，CPU 掩码延迟 $< 0.1\text{ms}$ | ⏳ **待执行** |
| **M5: 规则驱动本地 GRPO** | 以 Python AST 语法器与沙箱为 Reward，单卡 500 步 GRPO 自进化 | 边缘调用泛化鲁棒性提升，未见工具异常处理成功率提高 $20\%$ | ⏳ **待执行** |
| **M6: 端到端投机分流** | 与 `http://localhost:4000/v1` 联动，实施双通道分流 | 生产系统端到端节省 $70\%+$ 旗舰 Token，端到端延迟降低 10 倍 | ⏳ **终极验收** |
| **M7: 网关共生自进化飞轮** | 作为 LeanRouter 伴生 Sidecar (Docker/Native 守护常驻)，持续监听成功调用增量闭环训练 | 自动化采掘与过滤闭环，模型持续进化至成熟可用（分流率 $\ge 80\%$，分歧 $\le 1.0\%$） | ⏳ **自演进中** |

---

## 7. 终极防忽悠生产准入军规 (Anti-Cheat Production Acceptance)

为杜绝任何 Agent 偷懒、刷分或利用指标漏洞欺骗，本项目确立了无情的一票否决准入法典：
* 🛡️ **[Production Acceptance Standard (真实生产就绪与防欺骗终极验收标准)](docs/PRODUCTION_ACCEPTANCE_STANDARD.md)**:
  涵盖抗死记硬背扰动盲测、真实操作系统双盲执行、P0 越权一票否决、10 QPS 零显存泄漏压测以及 24 小时生产影子金丝雀准入协议。

---

*“把螺丝拧准，把时间省下，让云端只为真正的思考买单。”*  
*—— Wrench-SLM 核心研发原则*
