# Wrench Small Language Model (Wrench-SLM)

For a source-based assessment of implemented techniques, possible integrations, and unverified performance claims, see [AI engineering techniques and Wrench coverage](docs/AI_ENGINEERING_TECHNIQUES.md). The [active goal](goal.md) prioritizes validated standalone model weights.

For the current V21 training state, verified receipts, independent evaluations,
and weight-release decision, see the [model release handoff](docs/MODEL_RELEASE_HANDOFF.md)
and [model release progress](docs/MODEL_RELEASE_PROGRESS.md). The exact
adapter package is `artifacts/model-release/package-selected-v21`.

The architecture and performance targets described below are project vision and
historical design context. The measured V21 scope is the local adapter contract
documented in the model card. It does not establish router savings, hosted
service behavior, or the older millisecond targets.

> **"The Speculative Tool Execution & Draft Verification SLM."**
> *推测性工具预执行与草稿审核反薅羊毛架构：Flash 135M (树莓派/CPU 常驻网关) + Pro 0.5B (工作站/GPU 旗舰).*
> *Built to eliminate cloud frontier token fleecing locally, speculatively pre-executing routine tools and submitting drafts for cloud verification.*

---

## 1. Core Identity & Philosophy (项目核心定位与初衷)

在真实的智能体（Agent）工作流与网关架构中，**超过 70% ~ 80% 的请求属于确定性、机械性、低风险的日常事务**（如环境探查 `git status`、端口排查 `netstat`、依赖管理 `pip list`、读文件与基础参数组装）。

传统架构盲目地将这些琐碎请求连同庞大的系统提示词打包发送给昂贵的云端旗舰模型（如 Claude 3.5 Sonnet、GPT-4o），带来了严重的 **“Token 薅羊毛” 现象**：
- 云端模型必须逐字生成冗长、繁琐的 JSON 工具调用信封；
- 用户为了得到几个简单的参数，付出了高额的 Prompt Prefill + Output 费用与数百毫秒的公网往返排队延迟；
- 整个 Agent 执行链陷入等工具调用、跑工具、再把结果喂回云端的低效往返循环。

**Wrench（扳手）的诞生就是为了彻底终结这种 Token 浪费。**

我们坚决不要唐诗宋词、百科百科等无关通用泛化杂质，**Wrench 专精单一神圣使命：推测性工具预执行与草稿审核（Speculative Tool Pre-Execution & Draft Verification）**：
- **拒绝虚名**：不搞假大空的百科问答，专注成为极速、精准的边缘执行硬件引擎；
- **推测预执行（Speculative Pre-Execution）**：在云端大模型排队/深度思考的毫秒窗口期内，Wrench 提前推测工具调用意图。对于只读/幂等工具，直接就地执行完毕，将执行结果随 Prompt 一同打包递交云端审核，**一枪省掉整整一轮网络往返与云端生成工具调用的全部 Token**；
- **草稿审核防篡改（Draft & Verify）**：对于破坏性写操作，仅生成推测 JSON 草稿，由云端旗舰大模型充当“法官”进行最终审计签批，杜绝越权副作用；
- **双阶梯软硬协同**：提供 **Flash 135M (树莓派/CPU 5W 超低功耗静音网关)** 与 **Pro 0.5B (RTX 5070 Ti 极速旗舰)** 两套落地形态。

---

## 2. The North Star Goal & Decision Benchmark (北极星目标与决策基准)

> ### 🎯 项目终极目标 (The North Star Objective)
> **在单张消费级 GPU (RTX 5070 Ti 16GB) 上，构建一个具备真实泛化力、100% 结构化协议交付的端侧执行小模型（Wrench）。在保证交付可靠性不低于旗舰模型的前提下，将 70% ~ 80% 的高频机械工具调用就地在本地毫秒级（<30ms）消灭，为整个 Agent 系统实现端到端 0 云端 Token 消耗与 10 倍延迟削减。**

### ⚖️ 每一个决定的“一票否决”评估准绳 (The Decision Rule)
**从今天起，本项目的所有代码提交、算法引入、数据构建与架构演进，必须逐字对照以下 4 条基准严格审查。任何偏离目标的方案直接一票否决：**

1. **真实干活准绳（Does it do real work?）**  
   这项改动是否直接提升了模型在本地“提取参数、调用工具、终结请求”的能力？如果只是为了做虚假的元标签预测、分类自嗨或无法转化为实际动作的玩具，**直接否决**。
2. **交付完整性准绳（Does it protect protocol delivery?）**  
   任何技术（无论是微调、量化还是强化学习）如果损害了最核心的 JSON 语法合法率（Schema Validity）与工具执行成功率，**无论理论叙事多么高大上，必须立刻撤回**。
3. **极简可复现准绳（Is it reproducible on bare-metal?）**  
   方案是否能在单张 RTX 5070 Ti 和 Windows/Linux 原生 Python 环境下稳定运行？如果引入了极度脆弱的特定环境编译依赖或不可控黑盒，**直接否决**。
4. **反假大空准绳（Is it free of buzzword theater?）**  
   坚决不为了凑概念而硬塞与执行无关的模块（如所谓的越狱防护、防注入拒答 DPO）。安全交由网关层规则与审计，小模型只专注把螺丝拧紧。凡有虚名者，**直接切除**。

---

## 3. System Topology & Gateway Integration (系统拓扑与统一网关)

整个系统的中央路由与大模型聚合中心常驻在统一网关：

* **统一网关地址 (Gateway Endpoint)**: `http://localhost:4000` (或 `http://127.0.0.1:4000`)
* **协议标准**: 标准 OpenAI-compatible API (`http://localhost:4000/v1`)
* **网关职责**:
  1. 接收前端或业务系统的全量请求并路由；
  2. 聚合上游云端大模型资源（MiniMax、GPT-5.6 Luna、Claude 等）；
  3. 与本地常驻的 Wrench 执行小模型形成“边缘快道”协同。

```
                          [ Incoming User Request ]
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │      LeanRouter Gateway         │
                    │      http://localhost:4000      │
                    └────────────────┬────────────────┘
                                     │
            ┌────────────────────────┴────────────────────────┐
            ▼                                                 ▼
   [ Speculative Local Fast-Path ]                   [ Cloud Frontier Audit & Escalation ]
   • Tier 1: Wrench-Flash (135M CPU / Pi)            (via localhost:4000)
   • Tier 2: Wrench-Pro (0.5B GPU / 5070 Ti)         • MiniMax (数据生成 / 高并发 Teacher)
   (Pre-execute read tools in 15ms, 0 Token fleeced) • GPT-5.6 Luna (金标判官 / 审核 Teacher)
```

---

## 4. The Dual-Tier Model Family (双阶梯产品架构)

根据工业落地场景的能耗与算力差异，Wrench 采用分工明确的“双阶梯”模型矩阵：

### 1. `Wrench-Flash (135M)`（树莓派 24/7 低功耗静音硬件网关版）
- **核心规格**：135M 参数 (Hidden Dim = 768, Layers = 12, Heads = 12, Context = 2,048)。
- **目标硬件**：树莓派 4/5 (ARM Cortex-A72/A76, 4 核心)、低功耗软路由、迷你主机（N100 等）或办公 PC CPU。
- **能耗与体积**：INT4 GGUF 权重体积 **< 85 MB**，常驻运行内存 **< 180 MB**，整机功耗仅 **3W ~ 5W**。
- **核心定位**：
  1. **日常工具秒杀**：以 35ms ~ 50ms 的极速在端侧就地预执行只读探查（`git status`、`dir/ls`、`netstat`、`curl`）；
  2. **反薅羊毛第一哨**：将工具执行输出组装为已完成上下文，连同用户 Prompt 递交云端，直接省去 100% 的云端工具调用生成 Token；
  3. **静音守护**：无需独显，24 小时开机无噪音无发热，作为家庭/工位网络第一道智能网关。

### 2. `Wrench-Pro (0.5B)`（工作站 / GPU 旗舰小钢炮）
- **核心规格**：0.5B 参数 (Hidden Dim = 1024, Layers = 24, Heads = 16, Context = 4,096)。
- **目标硬件**：单张消费级 GPU（如 NVIDIA GeForce RTX 5070 Ti 16GB / RTX 4060 等）或具备 Apple Silicon 的工作站。
- **显存与吞吐**：原生 BF16 占用仅 **~1.0 GB**（INT8 量化下 **< 600 MB**），首字延迟 **12ms ~ 15ms**，推理吞吐 **> 200 tok/s**。
- **核心定位**：
  1. **深层意图理解与复杂参数提取**：胜任长命令拆解、多层转义引号、复杂代码差异校验与多工具组合推测；
  2. **破坏性写操作推测草稿**：对写操作仅输出推测 JSON 草稿，由云端大模型做最后一道审核确认；
  3. **难度仲裁一票否决**：遇到需要重构架构、反思推导的 P0 任务，毫秒级抛出 `ROUTER_FALLBACK` 移交云端。

---

## 5. Teacher-Student Distillation Pipeline (双轨教师模型蒸馏体系)

彻底告别旧项目的硬编码假模板，Wrench-0.5B 的全部训练数据与黄金评估标准由位于网关 (`http://localhost:4000`) 的两大 Teacher 模型协同构建：

| 教师模型 (Teacher) | 接入网关模型标识 | 核心定位与职责 |
| :--- | :--- | :--- |
| **MiniMax** | `localhost:4000/v1` (`minimax`) | **海量多样性合成工厂**：高并发、低成本生成 5,000 ~ 10,000 条真实人类口语多样化 Prompt，涵盖倒装、口语、缩写与多维度同义扰动。 |
| **GPT-5.6 Luna** | `localhost:4000/v1` (`gpt5.6-luna`) | **高维金标判官 (Gold Oracle & Judge)**：攻坚 500 条高难多参数依赖、模糊意图消歧样本；在测试集上充当 LLM-as-a-Judge 权威裁判。 |

---

## 6. The Three Value Pillars (最值钱的三大核心价值)

| 价值支柱 | 传统大模型方案痛点 | Wrench-SLM 解决方案 | 带来的实际收益 |
| :--- | :--- | :--- | :--- |
| **1. 本地工具直出 (Local Execution)** | 简单查天气、提取发票等机械任务调用 GPT-4o，花费数美分且等待近 1 秒。 | 0.5B 本地显存常驻，~30ms 内直接输出严格 Schema 合法的工具调用参数。 | **大模型 Token 消耗为 0**，延迟降低 10 倍，隐私不出内网。 |
| **2. 难度守门分流 (Arbitration)** | 全量请求无差别送给顶尖模型，或者用关键词规则造成高误判。 | 0.5B 语义把关，简单任务就地终结，超纲复杂推理毫秒级转派。 | 真正实现“把钱花在刀刃上”，系统整体吞吐量提升数倍。 |
| **3. 严丝合缝的结构化合规 (Schema Compliant)** | 通用大模型经常多吐引导词、废话解释，导致下游解析器异常。 | 专精 SFT + FSM 语法约束，严格对齐 JSON / Tool-Call Schema，输出即代码。 | 100% 的数学级协议交付率，系统下游极其稳固。 |

---

## 7. Frontier Algorithmic Pillars & Architectural Design (前沿算法与核心技术底座)

Wrench 绝不是简单的关键词匹配或基础 LoRA 微调，而是将当前大模型研究界最火热的前沿优化算法与边缘执行场景深度融合：

### 7.1 GRPO 规则自验证强化学习 (Rule-Based Reinforcement via Python Interpreter)
借鉴 **DeepSeek-R1** 核心技术思想，完全摒弃主观、脆弱的 Critic 网络与人类对齐偏好，改用**客观代码环境反馈（Verifiable Environment Feedback）**作为奖励：
- **执行环境闭环**：以本地 Python 解释器、JSON Schema 校验器及 Mock API 作为 Reward Model。
  - 格式正确解析 $\rightarrow$ `Reward +1.0`
  - 必需字段完整无缺失 $\rightarrow$ `Reward +1.0`
  - 参数类型完全合法、Python 函数执行成功不抛异常 $\rightarrow$ `Reward +2.0`
  - 产生预期的正确结果 $\rightarrow$ `Reward +3.0`
- **群相对策略优化 (GRPO)**：在本地单张 RTX 5070 Ti 上，针对每个样本采样一组候选工具输出，计算组内相对优势，让 Wrench 自主探索出最严密、容错率最高的调用策略。

### 7.2 动态推理算力预算调度 (Adaptive Test-Time Compute Allocation)
对标 **OpenAI o1 / o3 / DeepSeek-R1** 的“推理期算力扩展（Inference-Time Scaling）”范式，解决大模型“杀鸡用牛刀、过度思考”的严重缺陷：
- Wrench 扮演全系统 **“算力预算分配器（Compute Allocator）”**：
  - **Tier 0 (纯机械操作)**：Wrench 本地接管，**0 思考 Token、30ms 直接终结请求**；
  - **Tier 1 (常识/直接回答)**：分流给轻量直接输出模型（如 Claude 3.5 Haiku）；
  - **Tier 2 (长链复杂反思)**：按需唤醒云端推理大模型（R1 / o1 / Sonnet），动态赋予最大深度思考 Token 预算。
- 真正实现学术界提倡的 **Compute-Optimal Inference（算力最优推理）**。

### 7.3 投机解码与系统级投机预执行 (Speculative Decoding & Pre-execution)
- **极高接受率草稿模型 (High-Acceptance Draft Model)**：
  在结构化输出中，Token 空间高度确定。经 SFT/GRPO 调优后的 `Wrench-0.5B` 在生成工具调用 Token 时，作为 70B/32B 大模型的 Draft Model 接受率高达 **85% ~ 95%**，可直接将本地大模型的结构化推理速度提升 **2 ~ 3 倍**。
- **系统级投机预执行 (Speculative Tool Pre-execution)**：
  ```
  用户请求 ───┬───> [本地 Wrench-0.5B] ──(20ms)──> 投机生成参数 ──> 【提前在本地库拉取数据】
             │                                                                 │ (数据已就绪)
             └───> [云端 Claude/GPT-4o] ──(排队+深度思考 800ms) ───────────────▼
                                                                    [即刻合并返回，总耗时暴减]
  ```
  在云端大模型处于首字排队延迟（TTFT 800ms~1500ms）的等待窗口期，本地 Wrench 在 20ms 内完成工具意图推测并触发本地 API 预取。大模型唤醒工具时，数据早已就绪，彻底折叠串行延迟。
- **投机快道与影子验证 (Optimistic Fast-Path)**：
  对高置信度操作 30ms 极速先交付，后台异步低优先级影子复核，兼顾极速体感与系统级容错。

### 7.4 多 Token 联合预测加速 (Multi-Token Prediction - MTP)
借鉴 **DeepSeek-V3 / Meta** 前沿架构，打破传统自回归逐个 Token 生成的带宽瓶颈：
- 为 Wrench 引入轻量级 MTP 头，在每次前向传播中并行预测后续 $t+1, t+2$ 等成簇出现的固定结构符号（如 `", "type": "string"`）；
- 在工具生成场景下将原生吞吐从 150 tok/s 推升至 **300+ tok/s**，压榨 RTX 5070 Ti 的张量并行能力。

### 7.5 语法引导有穷状态机解码 (FSM / CFG Grammar-Constrained Decoding)
融合 **SGLang / Outlines** 的底层硬核约束生成技术：
- 将下游工具的 JSON Schema 在运行时编译为**有限状态自动机（FSM）**；
- 在模型生成每一个 Token 时，动态将其 Logits 中所有不符合语法的词表概率彻底掩码（Masking）；
- **数学级保证**：从根本上杜绝任何少括号、错别字或键名错误的可能，彻底免除下游系统的 JSON 解析异常。

---

## 8. Implementation Feasibility & Reproducibility Notes (工程实施避坑与可复制性笔记)

为保证项目 100% 能够落地并在任何机器上一键复现，我们记录了以下实战避坑笔记：

### 8.1 必须警惕的五大地雷与应对方案
1. **地雷一：数据虚假繁荣（模板过拟合陷阱）**
   - *风险*：纯靠硬编码模板生成数据会导致测试集满分、一进真实生产就抓瞎。
   - *解法*：基于 Teacher Model (`minimax` / `gpt5.6-luna` via `localhost:4000`) 与权威基准（BFCB/Gorilla）构建真实人类口语 Prompt，引入同义词扰动与多轮实体变异，训练真实语义模式。
2. **地雷二：Windows 系统的 C++/Triton 编译摩擦**
   - *风险*：MSVC 编译链与非标准 C++ 扩展容易导致环境搭建失败，摧毁一键复现。
   - *解法*：完全基于纯 Python + PyTorch 2.0+ 原生生态。注意力直接走原生 `F.scaled_dot_product_attention` (SDPA)，免编译且自动享受 CuDNN 硬件级加速。
3. **地雷三：GRPO 冷启动奖励塌陷（Reward Collapse）**
   - *风险*：未受约束的模型直接跑 RL 会因为全输出乱码（奖励全为0）导致梯度爆炸崩溃。
   - *解法*：**必须严格先 SFT 筑基（格式合法率稳定达 98%+），再启动 GRPO 做锦上添花**。
4. **地雷四：FSM CPU 掩码开销倒挂**
   - *风险*：每步在 CPU 上遍历 15 万词表做正则表达式匹配会导致 CPU 延迟反超 GPU。
   - *解法*：采用预编译静态 Trie 树与轻量级前缀缓存，把单步 Mask 查表时间压制在 0.1ms 以内。
5. **地雷五：紧耦合导致无法独立交付**
   - *风险*：模型与网关框架绑定过死，外部无法独立使用评测。
   - *解法*：Wrench 遵循标准 OpenAI Tool-Call 规范，作为独立代码库封装，任何开发者一行命令均可独立拉取跑分。

### 8.2 务实的四阶段落地路线 (The Phased Roadmap)

| 阶段 | 核心任务与技术抓手 | 交付产物与成功指标 |
| :--- | :--- | :--- |
| **Phase 1: 真实基座与高可用 SFT** | 通过 `localhost:4000` 调动 MiniMax/Luna 构建真实数据集 + Qwen2.5-0.5B LoRA SFT 流水线 | 参数提取准确率 > 95%，格式合法率 > 98%，单卡可一键复现 |
| **Phase 2: 零语法错误与投机草稿** | 静态 FSM 语法约束状态机集成 + SDPA 加速 + 作为 70B 草稿接入 | 100% 数学级 Schema Valid，草稿接受率 $\alpha > 85\%$ |
| **Phase 3: 本地 GRPO 规则自进化** | Python 解释器/单元测试环境作为 Reward，单卡 500 步 GRPO | 5070 Ti 单卡 10 分钟自强化收敛，异常工具调用鲁棒性显著提升 |
| **Phase 4: 投机预执行与网关联动** | 系统级投机执行 + 动态算力预算分流器（联动 `localhost:4000` 网关） | 端到端节省 70%+ 云端旗舰 Token，综合链路延迟降低 10 倍 |

---

## 9. Hardware Target & Verification (双阶梯实测硬件基准)

Wrench 针对端侧与工作站两大典型计算环境完成深度软硬协同适配与实测验证：

### Tier 1: Wrench-Flash (135M) 硬件基准
- **设备形态**：树莓派 4 / 树莓派 5 (Raspberry Pi 4/5)、工控迷你主机（Intel N100 等）或办公 PC CPU。
- **架构与计算**：4 核心 ARM Cortex-A72 / A76 (或 x86_64)，纯 CPU 原生推理。
- **内存与功耗**：
  - INT4 GGUF 量化权重体积：**< 85 MB**
  - 常驻物理内存 (RSS)：**< 180 MB**
  - 整机运行功耗：**3W ~ 5W**（支持 7×24 小时无风扇极低功耗静音常驻）
- **性能实测**：端到端首字延迟 **35ms ~ 50ms**，完全能够匹配家庭/工位网络路由吞吐。

### Tier 2: Wrench-Pro (0.5B) 硬件基准
- **设备形态**：高性能本地开发工作站。
- **GPU 算力**：NVIDIA GeForce RTX 5070 Ti (16 GB GDDR7, CUDA 12.8 / 13.4, SM 10.0+)。
- **精度与显存**：
  - 原生硬件级 `bfloat16` (BF16) 混合精度加速：显存常驻 **~1.0 GB**
  - INT8 量化显存常驻：**< 600 MB**
  - LoRA / 全参数微调显存开销：**3 GB ~ 8 GB**
- **性能实测**：首字延迟 **12ms ~ 15ms**，推理吞吐 **> 200 tok/s**，支持 10 QPS 高并发无阻塞推理。
- **宿主环境**：48 GB RAM, Intel Core i5-12400F (6C/12T), Windows 11 / Linux 原生支持。

---

## 10. Permanent Architectural Guardrails (永久设计军规)

1. **北极星目标至上**：所有架构、模型、微调决定，均以“是否真正帮系统分流、就地干活、节省云端 Token”为唯一检验标准。
2. **严防“虚假安全”**：绝不在小模型上强加所谓的拒答/防越狱对齐而牺牲基本格式能力；安全交给网关层规则与专有审计。
3. **闭环自验证**：坚持使用规则与编译器环境（Python/JSON）作为奖励信号（GRPO），拒绝低效主观人工偏好标注。
4. **恪守边界**：严格按照能力矩阵分工，高难任务果断下放给后端旗舰模型，绝不在小模型上硬撑伪推理。
5. **可测量、有证据**：每一次模型升级必须拿出准确率（Tool Accuracy）、Schema 有效率（Schema Validity）、延迟（p99 Latency）与节省 Token 数（Tokens Saved）的硬核测试收据。

---

## 11. Engineering Standards & Documentation (工程规范与严谨文档)

本项目设立了硬性、不可篡改的工程规范、立项目标与自动化审计体系。所有参与本项目的 AI 代理与开发者均须无条件遵守：

* 🎯 **[Project Goal & Core Purpose (目标定位与立项初衷)](goal.md)**:
  阐述为什么要做 Wrench、生产环境 80% 机械调用的本质、与云端 Teacher (`minimax`/`gpt5.6-luna`) 的明确分工边界，以及血泪总结的四大反向禁令与一票否决决策准绳。
* 📊 **[Evaluation Protocol & Audit Harness (严谨评测体系与审计协议)](eval.md)**:
  定义四大评测维度（Schema 合法率、沙箱执行成功率、物理延迟显存开销、本地分流率）、标准评测脚本、不可篡改的 JSON 机器收据规范与防作弊红线。
* 📘 **[Master Engineering Specification (主技术与架构规范)](docs/SPECIFICATION.md)**:
  详述系统架构数据协议、三大冻结训练阶段（LoRA SFT -> FSM -> GRPO）、严格的数据分割隔离与 AI Agent 五大约束军规。
* 📋 **[Acceptance Criteria & Audit Protocol (硬性验收标准与审计清单)](docs/ACCEPTANCE_CRITERIA.md)**:
  提供四大门禁的数学公式定义（$S_{\text{valid}}$, $E_{\text{rate}}$, $L_{p99}$, $O_{\text{rate}}$）与预提交必跑脚本。
* 🛡️ **[Production Acceptance Standard (防忽悠生产准入终极法典)](docs/PRODUCTION_ACCEPTANCE_STANDARD.md)**:
  剖析常见 6 大欺骗套路，确立五重防忽悠生产准入硬门禁（对抗扰动测试、真实双盲系统执行、P0 越权零容忍、10 QPS 零泄漏压测与 24 小时影子金丝雀）。
* 📦 **[Dataset Provenance & Design Specification (语料来源与设计目标规范)](data/README.md)**:
  详述五大语料采集管道（真实网关 Replay、双轨 Teacher 蒸馏、跨平台转译、机械工具专项工程矩阵、P0 越权逃逸负样本）与推测预执行反薅羊毛四大设计目标。
