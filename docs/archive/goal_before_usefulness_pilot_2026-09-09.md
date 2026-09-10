# Wrench-SLM: Project Goal & Core Purpose (目标定位与立项初衷)

```
Document Classification : NORTH STAR CHARTER / FOUNDATIONAL MISSION
Target Architecture     : Dual-Tier Wrench-SLM: Flash (135M) & Pro (0.5B)
Flash Specification : Wrench-Flash 135M (~135M-150M Params, INT4 ~85MB, Raspberry Pi / CPU, 5W)
Pro Specification   : Wrench-Pro 0.5B (~490M-500M Params, BF16 ~1.0GB, RTX 5070 Ti / GPU, 15ms)
Hardware Baselines  : 1) Raspberry Pi 4/5 (ARM64, 4GB/8GB RAM); 2) RTX 5070 Ti 16GB GDDR7
Gateway Routing     : http://localhost:4000/v1 (Teachers: minimax, gpt5.6-luna)
Deployment Modes    : 1) Raspberry Pi LAN Gateway (5W); 2) LeanRouter Workstation Daemon
Core Mission        : Speculative Tool Execution & Draft Verification to End Cloud Token Fleecing
```

---

## 1. 核心宗旨 (The Core Mission)

> ### 🎯 北极星目标 (The North Star Objective)
> **构建以“Flash 版本（135M 树莓派硬件网关版）”与“Pro 版本（0.5B 工作站旗舰版）”为基石的双阶梯推测性工具预执行引擎（Speculative Tool Execution Engine）。**  
> **它们不做通用闲聊，不写散文诗歌，只做一件事：在云端 Frontier 旗舰大模型接管前，提前洞察工具调用意图、抢跑预执行安全读命令，并将推测草稿与真实环境结果前置打包喂给大模型做审核。**  
> **以此将 Agent 传统的“两轮网络往返 + 大模型生成冗余 JSON 包装 + 重复上下文 Prefill”彻底消灭，把端侧延迟削减 10 倍，并终结云端提供商对开发者 Token 的恶意消耗与“薅羊毛”。**

---

## 2. 战略转折：废弃 28M 玩具假说，确立“双阶梯”产品架构

在项目早期，曾立项探索过“纯手搓 25M~28M 从零微型模型”的设想。经过严格工程审计与实测，**本项目正式宣布彻底废弃 28M 玩具假说**。
针对真实生产与家庭/办公室边缘硬件，确立**“双阶梯（Dual-Tier）”产品定位**：

```
                    ┌──────────────────────────────────────────────────────────┐
                    │      Wrench-SLM 双阶梯产品架构 (Dual-Tier Architecture)   │
                    └──────────────────────────────────────────────────────────┘
                                                 │
                   ┌─────────────────────────────┴─────────────────────────────┐
                   ▼                                                           ▼
┌──────────────────────────────────────────────┐ ┌──────────────────────────────────────────────┐
│  Tier 1: Wrench-Flash (135M / 0.15B)         │ │  Tier 2: Wrench-Pro (0.5B)                   │
│  【树莓派 / CPU 低功耗硬件网关版】           │ │  【工作站 / GPU 旗舰版】                     │
│  * 目标设备: 树莓派 4/5 (ARM64), 纯 CPU 机器   │ │  * 目标设备: RTX 5070 Ti, 消费级独立显卡     │
│  * INT4 权重体积: ~85 MB (GGUF / llama.cpp)  │ │  * BF16 显存常驻: ~1.0 GB (INT8 < 600MB)    │
│  * 内存开销: < 180 MB (5W 超低功耗静音常驻)   │ │  * 端侧推理延迟: ~12-15 ms (极致毫秒响应)   │
│  * CPU 推理延迟: ~35 ms ~ 50 ms              │ │  * 意图解析力: 极限深层槽位提取与多工具协同 │
│  * 使命: 全屋/办公室局域网硬件级 Token 盾牌  │ │  * 使命: 单机重度开发者本地毫秒级推测闭环   │
└──────────────────────────────────────────────┘ └──────────────────────────────────────────────┘
```

### 树莓派硬件网关部署拓扑 (The Raspberry Pi Hardware Gateway)
用户无需在每一台电脑上都配置昂贵显卡，只需在局域网内插上一台 **树莓派 5 (5W 功耗，全天候静音常驻)**：
1. 树莓派运行 `LeanRouter` + `Wrench-Flash (135M GGUF)`；
2. 局域网内所有电脑（MacBook、轻薄本、台式机）上的 Cursor、VSCode、Cline、Claude Code 将 Base URL 统一指向：
   `http://raspberrypi.local:4000/v1`；
3. **整间办公室或整个家庭的所有 AI 编程助手工具调用，全天候 24 小时被树莓派在本地拦截并推测执行，每月直接省掉上千美元的云端 Token 费用！**

---

## 3. 帕累托 20/80 定律：掌握 20% 核心工具，通吃 80% 真实业务场景 (The 20/80 Pareto Tool Principle)

在模型架构设计中，试图让一个 135M 或 0.5B 的小模型去强行背诵 5,000 个生僻第三方 API 是注定失败的歧途。这会导致严重的参数容量过载、灾难性遗忘与语法幻觉。

**真实的软件研发与智能体工作流，完全符合严苛的帕累托法则（Pareto Principle）：**
> **20% 的核心与专用工具，吃下了整个 Agent 生产环境中 80% 以上的高频调用流量。**

```
                             [ 全量 Agent 工具调用流量 ]
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼ (占总调用量 80%+)                             ▼ (占总调用量 < 20%)
   ┌──────────────────────────────────────────────┐ ┌──────────────────────────────────────────────┐
   │       【20% 黄金机械工具箱 (Golden 20%)】     │ │       【80% 长尾生僻与高难推理工具】          │
   │  Mastered by Wrench-Flash (135M) & Pro (0.5B)│ │      Escalated to Cloud Frontier Models      │
   │  --------------------------------------------│ │  --------------------------------------------│
   │  1. exec_command (Git/Files/Net/Search/Deps) │ │  1. 跨系统多跳复杂事务、长链规划              │
   │  2. read_file / view_file (精确切片探查)     │ │  2. 极生僻 SaaS 第三方 Webhook API            │
   │  3. write_to_file / replace_file_content     │ │  3. 开放式创意生成、微服务重构架构设计         │
   │  4. write_stdin / send_input (交互式管道)    │ │                                              │
   │  5. get_goal / update_goal (生命周期同步)     │ │                                              │
   │  --------------------------------------------│ │                                              │
   │  ⚡ 目标: 100% 格式合法, 15ms 端侧即刻预执行  │ │  ☁️ 处理策略: 毫秒级 ROUTER_FALLBACK 转派云端 │
   │  💰 效果: 为全系统直接砍掉 80% 的云端 Token  │ │                                              │
   └──────────────────────────────────────────────┘ └──────────────────────────────────────────────┘
```

### 黄金 20% 工具箱的五大基石：
1. **`exec_command`（全能终端与系统工兵）**：
   - 占终端调用的 75% 以上。涵盖 Git 状态比对（`status/diff/log`）、文件探查（`cat/head/tail/wc`）、快速检索（`rg/fd/grep`）、服务诊断（`curl/netstat/docker`）与依赖同步（`pip/uv/npm`）。
2. **`read_file` / `view_file`（精确文件切片探查）**：
   - 查看指定行号代码或配置，是 Agent 阅读工程的最基础传感器。
3. **`write_to_file` / `replace_file_content`（精准局部修改）**：
   - 代码 Patch 与配置文件增量替换。
4. **`write_stdin` / `send_input`（交互式输入响应）**：
   - 响应命令行提示符（`y/n/q/exit`、确认继续）。
5. **`get_goal` / `update_goal`（任务目标与状态同步）**：
   - 智能体状态机心跳同步。

**把这 20% 的工具在 135M/0.5B 权重中练到炉火纯青（99.5%+ 准确率、0 语法错误、15ms 响应），就能直接在端侧就地消灭 80% 的云端流量与 Token 消耗！**

---

## 4. 反薅羊毛：为什么传统 Agent 会被大模型持续“放血”？

在传统 Agent 系统中，每一次日常的工具调用都在产生惊人的经济与时间损耗：
1. **第 1 次被薅：昂贵输出 Token 买废话 JSON**  
   云端 Output Token 价格是 Input 的 3~4 倍。为了执行一行简单的 `git status`，大模型慢吞吞吐出几十个甚至上百个 Token 的 JSON 括号与键名。
2. **第 2 次被薅：强制两轮往返与网络等待**  
   大模型先输出工具调用 JSON（等 1.5 秒），传回本地执行；执行后再把结果发给大模型（再等 1.5 秒），单步任务耗费 3~4 秒。
3. **第 3 次被薅：巨额上下文重复计费（反复 Prefill）**  
   第二轮把工具结果送回大模型时，前文积累的 3 万、5 万个上下文 Token 必须重新计费计算一次，造成极大的资金浪费。

---

## 5. 核心系统架构：推测预执行与草稿审核协议 (Speculative Execution & Draft Verification)

Wrench-SLM 0.5B 在网关层（`LeanRouter`）实施颠覆性的推测注入：

```
                             [ 用户的真实输入 / Agent 意图 ]
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  LeanRouter 边缘网关 (localhost:4000)                                                  │
│                                                                                        │
│  1. 本地 Wrench-0.5B 抢跑 (15ms): 极速预测出工具调用 {"tool": "exec_command", "cmd": "..."} │
│  2. 安全判定 (Safety Gate)       : 读操作立即执行 / 写操作仅拟草稿                     │
│  3. 本地沙箱预执行 (5ms)         : 纯读命令直接就地跑完，拿到真实 stdout               │
│  4. 组装“既成事实”推测信封       : 拼装出【推测的完整 Tool Call + 已拿到的 Tool Result】 │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼ (只发起这 1 次请求！)
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  云端 Frontier 旗舰大模型 (GPT-5.6 / Minimax)                                          │
│                                                                                        │
│  * 接收到的 Context 里，已经包含了小模型预执行拿到的真实输出！                         │
│  * 大模型【根本不需要】浪费输出 Token 去生成工具调用 JSON！                             │
│  * 大模型直接跳过第 1 轮交互，【1 步到位】开始对真实结果进行分析与总结！                │
│  * 若审核不通过，大模型拥有最高裁判权，直接 Reject 并发出修正指令。                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 四大防翻车工业安全护栏 (The 4 Safety Harnesses)

推测执行绝不能在没有制动器的情况下狂奔。本工程确立四道不可逾越的安全红线：

### 护栏 1：只读幂等沙箱（Safe-Read Idempotent Gate）
* **纯读探查操作（允许预执行）**：`git status`, `git diff`, `cat`, `Get-Content`, `ls`, `curl -I`, `netstat`, `where.exe`, `pytest`。这些命令即使推测偏差，对系统磁盘与数据库产生 **0 副作用与 0 破坏**。
* **修改与高危操作（严禁预执行）**：`rm -rf`, `Remove-Item`, `git push`, `Drop`, `Kill`, `git reset`。**小模型只生成推测草稿（Draft Only），绝对不上手物理执行！** 草稿随请求送给大模型，必须经过云端旗舰审查核准后，本地网关才允许落盘。

### 护栏 2：状态漂移防护（Anti-State Drift）
* 严禁推测执行具有全局环境持久状态变更的命令（如 `cd` 切换全局工作区、全局环境变量变更）。所有探查命令必须显式携带 `-LiteralPath` 或工作目录隔离，防止主环境被改脏。

### 护栏 3：裁判模式提示词注入（Audit Prompt Injection）
* 为防止云端大模型产生“锚定偏见（Anchoring Bias）”被小模型带偏，注入给大模型的 Context 必须带有强制审计指令：
  ```markdown
  [SYSTEM AUDIT PROTOCOL - SPECULATIVE PRE-EXECUTION]:
  The following tool call and observation were speculatively executed by edge Wrench-0.5B:
  - Tool Call   : exec_command("netstat -ano | findstr :4000")
  - Local Output: "TCP 127.0.0.1:4000 LISTENING 1420"
  ⚠️ AUDIT MANDATE: 
  You are the supreme auditor. If this speculative execution accurately aligns with the user's intent,
  absorb the output and proceed immediately to final reasoning. 
  If MISALIGNED, REJECT it and issue your own tool call.
  ```

### 护栏 4：高置信度门限（Confidence Entropy Threshold $P \ge 0.90$）
* 只有当 Wrench-0.5B 的输出平均概率 $\ge 0.90$（极度确信、毫无悬念的机械意图）时，才触发推测预执行。
* 遇到模糊、多意图或复杂逻辑（$P < 0.90$），小模型立刻**闭嘴当观众（Abstain）**，毫秒级无损放行给云端大模型。

---

## 7. 终极交付路线图 (Milestones Evolution)

| 阶段代码 | 核心里程碑 | 验收标准 | 状态 |
| :--- | :--- | :--- | :--- |
| **M1: 数据流与全域扩增** | 1.9 万条真实与合成矩阵样本，覆盖网络/文件/Git/测试/交互 | 全域语法验证通过率 $\ge 99\%$，双平台对齐 | ✅ **已达成 (19,388条)** |
| **M2: 规范法典与准绳固化** | 固化 0.5B 规范与推测执行反薅羊毛理论法典 | `goal.md`, `eval.md`, `SPECIFICATION.md` 全绿，Ruff 0 警告 | ✅ **已达成** |
| **M3: Wrench-0.5B 引擎筑基** | 确立 0.5B 架构 (`dim=1024, layers=24, intermediate=2816`) | 纯血架构初始化与前向传播测试通过，显存常驻 $\le 1.2\text{GB}$ | ✅ **已达成** |
| **M4: FSM 语法状态机装配** | Logits 处理器强行锁定 JSON 与 Schema 语法 | 结构化合法率数学级 100% | ✅ **已达成** |
| **M5: 读写安全门禁与推测沙箱** | 落实 Safe-Read 自动预执行与 Mutation 仅出草稿机制 | 破坏性指令物理预执行拦截率 100%，只读指令执行率 $\ge 98\%$ | ⏳ **接入中** |
| **M6: 端到端推测执行旁路** | LeanRouter 网关注入“既成事实信封”，单轮结案 | 砍掉 1 轮网络往返，大模型端侧 Token 消耗节省 $\ge 50\%$ | ⏳ **终极闭环** |

---

*“小模型负责腿快，大模型负责脑好。把螺丝抢先拧好，彻底终结云端 Token 薅羊毛。”*  
*—— Wrench-SLM 核心研发宪章*
