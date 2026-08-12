---
id: ai-coding-insight-0003
title: 编码 Agent 的外挂记忆中间件：OpenViking、Mem0 与同类工具横向洞察
domain: ai-coding
type: insight
status: review
created: 2026-08-12
updated: 2026-08-12
tags: [memory, context-engineering, memory-middleware, mcp, coding-agent, cli-agent, market-landscape, tech-route, selection, eval]
vendors: [openviking, mem0, zep, graphiti, letta, cognee, supermemory, byterover-cipher, claude-mem, openmemory, opencode, claude-code]
related: [ai-coding-insight-0002, ai-coding-solution-0001, ai-coding-vendor-0001]
summary: 外挂记忆分四条路线；接入点比存储结构更决定成败，OpenViking 的 AGPL 与 Mem0 的云依赖各自卡住企业内嵌
---

# 编码 Agent 的外挂记忆中间件：OpenViking、Mem0 与同类工具横向洞察

> 本文归属 `ai-coding` 领域 **「记忆与上下文管理」专题**，是 [ai-coding-insight-0002](2026-08-12-memory-context-management-landscape.md) 的**外部供给侧补篇**。
> insight-0002 回答的是"编码 Agent 自己把记忆做到了什么程度"；本文回答的是"如果不自建，外面有什么可以买/接，以及接进来会付什么代价"。
> 事实核对日期：2026-08-12。**本文所有性能数字均为厂商自报或第三方转述，未经我方复现**，引用前请读 §5。

## TL;DR

- **归属判定：这两个工具属于本领域的「记忆与上下文管理」专题，但它们本身是跨领域基础设施。** 它们不是编码工具，是通用 Agent 记忆层；只有"接进编码 Agent"这一侧属于 `ai-coding`。**不为它们新开专题**，判定规则见 §1。
- **外挂记忆已经分化成四条互不兼容的路线**：事实抽取+向量（Mem0、Supermemory）、时序知识图谱（Zep/Graphiti、Cognee）、分层文件系统（OpenViking、Claude Code auto memory）、有状态运行时（Letta）。**它们解决的失效模式不同，不是同一个东西的不同实现**，横向比"谁准"没有意义。
- **决定成败的不是存储结构，是接入点。** MCP 工具形态把召回决策交给模型自主发起，实测普遍"模型根本不调"；hook 前置注入才是确定性的。OpenViking 的 Claude Code 插件明确走 hook 路线（`UserPromptSubmit` 前置检索 + 注入 `<openviking-context>` 块），这比它的 L0/L1/L2 分层更值得抄。详见 §4。
- **两个主角各自有一处硬约束卡住企业内嵌**：OpenViking 主体是 **AGPLv3**（CLI crate 与 examples 才是 Apache 2.0），我们若把它嵌进对外提供的内部平台需走法务；Mem0 是 Apache 2.0 但**能力最完整的部分在云端**，自建 server 与 Cloud 不等价。选型时这两条比任何 benchmark 分数都靠前。
- **OpenViking 的三层加载（L0 ~100 token / L1 ~2k token / L2 全文）+ 目录递归检索 + 可见轨迹，正面命中了 insight-0002 §3.6 提出的"记忆不可见即不可维护"。** 这是它相对 Mem0 一类"黑盒抽事实"路线的真实差异点，也是最值得我们借鉴的设计。
- **对 opencode 定制的结论：不引入外部记忆服务作为依赖，但抄两个设计。** 抄 OpenViking 的分层加载与轨迹可见，抄 hook 前置注入的接入形态；不抄它的向量服务栈。这与 insight-0002 §5 第二档（M5–M8 + M11/M12 的 FTS5 最小闭环）不冲突，是对它的细化。详见 §6。

## 1. 归属判定：它们属于哪个专题

用户问题的第一层是分类问题，先答清楚。

### 1.1 结论

| 判定项 | 结论 |
|---|---|
| 领域（domain） | `ai-coding`（本文）**且** `agent-platform`（本体） |
| 专题 | **「记忆与上下文管理」**（`ai-coding` 领域内已有专题，见领域索引） |
| 在六层框架中的位置 | 主要落 **L4 跨会话记忆**，OpenViking 额外覆盖 **L2 按需知识** 与 **L5 检索** |
| 是否新开专题 | **否** |

### 1.2 判定依据

`docs/taxonomy.md` 对两个领域的边界写得很明确：`agent-platform` 收录"记忆与上下文工程"，`ai-coding` 不收录"通用 Agent 平台机制"。按字面，OpenViking 与 Mem0 的本体应归 `agent-platform`。

但真正决定归属的是**这份材料要服务什么决策**。本次调研的落点是"我们基于 opencode 做记忆能力时，要不要用现成的"——这是 `ai-coding` 领域 [ai-coding-solution-0001](../solutions/2026-08-11-opencode-enterprise-customization-roadmap.md) 的排期输入，不是通用平台选型。因此：

> **判断**：按**服务的决策**归档，不按**工具的本体**归档。本文放 `ai-coding/insights/`，并入「记忆与上下文管理」专题；若将来出现"公司统一 Agent 记忆底座"这类平台级议题，再在 `agent-platform` 另立条目，用 `related` 与本文互链，不复制内容。

不新开专题的理由：专题的定义是"围绕同一问题成组的条目"。本文与 insight-0002 回答的是同一个问题的两面（自建 vs 外购），拆成两个专题会让检索时必须读两遍才能拿到完整结论。

### 1.3 顺带修正一个易混点

「记忆与上下文管理」专题名下现在有两类条目，检索时注意区分：

- **insight-0002**：编码 Agent **内建**的记忆/上下文机制（Claude Code、Codex、Cursor、MiMo Code、opencode 源码级）。
- **insight-0003（本文）**：**外挂**的记忆中间件（OpenViking、Mem0 及同类）。

两者的 L4 层可以互相替代，L1/L3 层不能——**没有任何外挂中间件能替你解决压缩阈值和摘要衰减**，那是宿主 Agent 的事。这一点在 §6 会再强调一次。

## 2. 两个主角

### 2.1 OpenViking — 火山引擎的"Agent 上下文数据库"

**基本事实**

| 项 | 内容 |
|---|---|
| 出品 | 字节跳动火山引擎 Viking 团队，2026-01 开源（`volcengine/OpenViking`） |
| 定位 | Agent **上下文数据库**（不自称记忆库），统一管 memory / resources / skills |
| 许可 | **主项目 AGPLv3**；`crates/ov_cli` 与 `examples/` 为 Apache 2.0 |
| 形态 | 自建 server（`pip install openviking` + `openviking-server`）/ 火山托管 SaaS / 私有化（含离线，需激活码） |
| 依赖 | Python 3.10+，需 embedding 与 LLM provider（火山、OpenAI、Kimi、GLM、本地 Ollama 皆可） |
| 热度 | 开源一个月 4.5k star，2026 年中已到 2 万量级（**各来源口径差异很大，仅作热度参考，不作选型依据**） |

**核心范式：`viking://` 虚拟文件系统**

这是它与所有其他记忆中间件的根本分歧点。别人把记忆存成"一条条事实"或"一张图"，它存成**目录树**：

```
viking://
├── resources/                 # 外部内容：文档、代码库、网页
└── user/{user_id}/
    ├── memories/              # 用户偏好、Agent 经验
    ├── skills/                # Agent 能力（如 search_code、analyze_data）
    └── peers/                 # 交互历史
```

Agent 用 `ls` / `tree` / `find` 这类**开发者本来就懂的操作**浏览自己的上下文，而不是对一个黑盒向量库发查询。

**三层加载（L0 / L1 / L2）**

写入时每份内容被处理成三层，**每个目录自己也带 L0/L1**：

| 层 | 体量 | 用途 |
|---|---|---|
| L0 摘要 | ~100 token | 一句话，用于快速粗筛相关性 |
| L1 概览 | ~2k token | 结构与适用场景，用于规划决策 |
| L2 详情 | 全文 | 只有真正需要时才加载 |

检索流程是**目录递归检索**：向量检索先定位得分最高的**目录**（而非文档片段），再逐层向下钻取，返回结果时带上所在路径的上下文。**每次检索留下可浏览的轨迹**——官方原话是"结果看着不对时，你能确切看到是哪条路径产出的"。

> **判断**：这一条是 OpenViking 全部设计里对我们最有价值的。insight-0002 §3.6 的结论是"记忆一旦不可见就不可维护，`/context` 类能力必须与记忆同期交付"——OpenViking 是把可见性做进检索协议本身，而不是事后补一个查看命令。**这是设计层面的差异，不是功能层面的。**

**会话→记忆的沉淀**：会话提交后异步抽取"用户偏好"与"Agent 经验"落入长期记忆，即所谓 self-evolving。

**编码 Agent 接入**：官方 examples 覆盖 Claude Code、Codex、OpenCode、Cursor、Trae、OpenClaw、Hermes 等。Claude Code 插件的实现细节值得单独看（§4.2）。

**厂商自报效果**（v0.3.22）：

| 维度 | 数字 |
|---|---|
| 用户记忆（LoCoMo） | 三个 Agent 接入后准确率 80–83%，原生 24–57%；其中 Claude Code 57.21% → 80.32% |
| 输入 token | 下降 34.3%–91.0% |
| 延迟 | 改善 58.45%–66.10% |
| Agent 经验（tau2-bench） | retail 任务成功率 +6.87pp，airline +11.87pp |

> ⚠️ 这组数字的基线是"Agent 原生记忆"，而 Claude Code 原生 auto memory 的 57.21% 是否代表其真实配置下的表现，无独立复现。**不要在对外汇报中引用为既成事实。**

### 2.2 Mem0 —— 通用记忆层的事实标准

**基本事实**

| 项 | 内容 |
|---|---|
| 出品 | Mem0（Taranjeet Singh / Deshraj Yadav），有配套论文 |
| 定位 | **通用记忆层**（universal memory layer），不限编码场景 |
| 许可 | **Apache 2.0** |
| 形态 | 库（pip/npm，原型用）/ 自建 server（Docker Compose，团队用）/ Cloud（`app.mem0.ai`，生产用） |
| 热度 | 63.1k star / 7.3k fork（2026-08-12 核对） |
| 免费额度 | Cloud 免费层 10,000 条记忆 + 1,000 次检索/月 |

**架构（2026-04 算法更新后）**

- **单遍 ADD-only 抽取**：一次 LLM 调用累积记忆，不覆盖旧数据。
- **Agent 生成的事实是一等公民**：Agent 确认过的动作与用户陈述同等权重——这一条对编码场景很关键，"我改了什么、为什么这么改"本来就是 Agent 侧的产物。
- **实体链接**：抽出的实体做 embedding 并交叉链接。
- **多信号检索**：语义 + BM25 关键词 + 实体匹配**并行**后融合。
- **时序推理**：区分"当前状态 / 历史事件 / 未来计划"排序。
- **图记忆**：从自然对话中抽取实体（人、主题、工具、日期）及其关系。

**厂商自报效果**（README，2026-04）：

| Benchmark | 旧 | 新 | token | 延迟 |
|---|---|---|---|---|
| LoCoMo | 71.4 | **92.5** | 7.0K | 0.88s |
| LongMemEval | 67.8 | **94.4** | 6.8K | 1.09s |
| BEAM (1M) | — | **64.1** | 6.7K | 1.00s |

**编码 Agent 接入**：官方 Claude Code 插件 = MCP server + 生命周期 hook + 两个 skill（`mem0` 教 SDK 用法、`mem0-mcp` 教 MCP v2 filter 形状）。另有 **OpenMemory** —— Mem0 的 local-first MCP 记忆服务，完全跑在本机，对接 Claude Desktop、Cursor、Windsurf、VS Code。

> **判断**：Mem0 的工程成熟度（生态、文档、22 个框架的接入指南、Apache 2.0）明显领先，但它的产品重心在**用户个性化**（客服、助手、陪伴），不在编码。"记住用户爱吃什么"和"记住这个仓库的鉴权中间件为什么不能加缓存"是两类召回问题——前者短事实、低歧义，后者长上下文、强路径依赖。**LoCoMo 92.5 分不能外推到编码场景。**

### 2.3 两者最本质的三点差异

| | OpenViking | Mem0 |
|---|---|---|
| **记忆的形状** | 层级目录树（保留结构与路径） | 扁平事实 + 实体图（丢弃原始结构） |
| **谁来决定加载什么** | Agent 自己"逛"目录，逐层下钻 | 检索服务算好了推给你 |
| **可解释性** | 检索轨迹可浏览，路径即证据 | 靠分数，出错难归因 |

第三行是我认为的胜负手：**在编码场景，记忆出错的代价不是"回答不个性化"，而是"照着一条过时结论改坏了代码"**。这时"是哪条记忆导致的"必须能查。

## 3. 横向格局：外挂记忆中间件的四条路线

把当下热门的开源记忆层按**记忆的组织结构**分类，而不是按知名度排列。

### 路线 A · 事实抽取 + 向量检索

**代表**：Mem0、Supermemory

用 LLM 从对话里抽"事实"，embedding 存向量库，查询时向量+关键词混合召回。工程最简单、生态最成熟。

- **Supermemory**：MCP 优先、明确宣称为编码 Agent 场景优化；自称在 LongMemEval / LoCoMo / ConvoMem 三项均第一，事实召回 81.6%（次优 Zep 71.2%）。设计理念带脑科学隐喻——"遗忘平庸的、强化近期用过的、按当前上下文重写记忆"。opencode 生态里已有第三方插件 `opencode-supermemory`（insight-0002 §3.4 已记录）。
- **失效模式**：抽取即有损。长因果链（"因为 A 所以我们否决了 B，改用 C"）被拆成三条独立事实后，召回一条就可能得出相反结论。

### 路线 B · 时序知识图谱

**代表**：Zep / Graphiti、Cognee

- **Zep / Graphiti**：**双时态**模型是它的核心资产。每条边带四个时间戳——`t_created`/`t_expired`（系统何时录入/作废）与 `t_valid`/`t_invalid`（事实何时成立/失效）。摄入单位是 episode（消息、原始文本、结构化 JSON），落成 Episodic 节点，再抽出实体与语义边，双向索引可回溯到来源 episode。发现时间上重叠的矛盾时，把旧边的 `t_invalid` 设为新边的 `t_valid`——**作废而非删除**，历史完整保留。第三方对比给出 Graphiti 在 LongMemEval（GPT-4o）63.8% vs Mem0 49.0%。
- **Cognee**：ECL（Extract–Cognify–Load）管线，Cognify 阶段用 LLM 建实体+类型化关系的知识图谱，落进图库+向量库的混合存储，图遍历与向量检索融合，并能按反馈重新加权。
- **失效模式**：建图成本高（每次摄入都要 LLM 抽实体关系）、schema 设计敏感、对"没有清晰实体关系的知识"（比如一段调试心得）表达力反而不如一段自然语言。

> **判断**：双时态作废机制是**唯一正面解决 insight-0002 §6"记忆污染"风险的机制**——它让"这条结论在哪段时间成立"变成可查询的一等属性。对编码场景（技术选型会随版本失效）价值很高。但把它当成"照抄的架构"是错的，**值得抄的是概念：记忆条目必须带有效期语义，而不只是 insight-0002 M8 说的 `modified` 时间戳。**

### 路线 C · 分层文件系统

**代表**：OpenViking、Claude Code auto memory、basic-memory 一类 markdown 方案

记忆就是文件，模型用普通文件工具读写，结构即语义。

- 优点：零抽取损失、人可直接编辑、天然可审计、可进 git。
- 缺点：召回靠检索质量（BM25/向量/模型自主浏览），大规模下平坦目录会退化。
- OpenViking 的 L0/L1/L2 + 目录递归检索，正是为了解决"文件多了怎么找"这个路线 C 的固有短板。

> insight-0002 §3.4 的结论是"最值得抄的三个设计"来自 Claude Code auto memory（两级结构、时间戳、超限反馈驱动自整理）——那三条本质上就是路线 C 的最小实现。**OpenViking 是同一路线的重工业版本。**

### 路线 D · 有状态运行时

**代表**：Letta（原 MemGPT）

不是"给 Agent 加记忆"，而是"Agent 本身就是记忆"。核心是**memory block**——上下文窗口里带字符上限的具名段落，**可在多个 Agent 之间共享**。

关键设计是 **sleep-time compute**（2025-04 论文）：主 Agent **没有**编辑 core memory 的工具，这些工具挂在一个独立的 **sleep-time agent** 上，由它在空闲时异步重组主 Agent 的 in-context 记忆。相比原始 MemGPT 把"对话"和"管记忆"塞进同一个 Agent，这样既降延迟又提记忆质量。

> **判断**：Letta 是四条路线里唯一自带 Agent 运行时的——**这意味着它不是"接进 opencode"，而是"替换 opencode"**。对我们不适用，但"记忆整理放到主循环之外异步做"这个思路，可以直接用在 opencode 插件里（`session.compacted`/会话结束事件触发离线蒸馏），且成本极低。MiMo Code 的 `/dream`、`/distill`（insight-0002 §3.4）走的就是这条。

### 路线 E · 编码场景专用封装（严格说不是独立路线）

它们大多是路线 A 或 C 的封装，但因为只服务编码 Agent，产品形态更贴近我们：

- **Byterover Cipher**（现演进为 `byterover-cli`，npm `@byterover/cipher` 已废弃）：明确"专为编码 Agent 设计的记忆层"。分三类记忆——**System 1**（编程概念/业务逻辑/历史交互）、**System 2**（模型生成代码时的推理步骤）、**Workspace Memory**（团队共享上下文，带作用域权限）。通过 MCP 兼容 Cursor / Windsurf / Claude Code / Cline / Gemini CLI / Kiro / VS Code / Roo Code / Trae / Amp / Warp。
- **claude-mem**：纯本地方案。5 个生命周期 hook（`SessionStart` / `UserPromptSubmit` / `PostToolUse` / `Stop` / `SessionEnd`）捕获工具使用轨迹 → 语义压缩成摘要 → 按**渐进披露**分层注回后续会话。SQLite 存会话与观察 + Chroma 向量库做混合检索，暴露 4 个 MCP 工具（search / timeline / get_observations / filtering）。Apache 2.0，支持 Claude Code、OpenClaw、Codex、Gemini、Hermes、Copilot、opencode。
- **OpenMemory**（Mem0 出品）：local-first MCP 记忆服务，跨 MCP 工具共享一层记忆，实现"工具间上下文交接"。

> **判断**：**System 2 记忆（存推理步骤而非结论）是 Cipher 提出的、其他路线都没有的东西**，值得关注但风险明显——推理步骤体量大、复用率低，容易变成噪音源。**Workspace Memory（团队共享）才是编码场景真正的差异化需求**，也是我们企业化定制里唯一无法从个人向工具白嫖的部分。

### 3.1 汇总对比

| 工具 | 路线 | 记忆结构 | 许可 | 是否需外部服务 | 编码场景专用 | 对我们的可用性 |
|---|---|---|---|---|---|---|
| **OpenViking** | C | 分层目录树 + 向量 | **AGPLv3**（CLI/examples Apache） | 是（自建或 SaaS） | 否（有官方编码插件） | **借鉴设计，不引依赖** |
| **Mem0** | A | 事实 + 实体图 | Apache 2.0 | 库模式否 / 完整能力是 | 否 | 可评估，重心不在编码 |
| Supermemory | A | 事实 + 用户画像 | Apache 2.0 | 是 | **是**（自称） | opencode 已有第三方插件 |
| Zep / Graphiti | B | 双时态知识图谱 | Apache 2.0 | 是（图库） | 否 | **借鉴双时态概念** |
| Cognee | B | 图 + 向量混合 | Apache 2.0 | 是 | 否 | 低 |
| Letta | D | memory block + 运行时 | Apache 2.0 | 是（是运行时） | 否 | **不适用**（会替换宿主） |
| Byterover Cipher | E(A) | 三类记忆 + 工作区 | 开源 | 是 | **是** | 借鉴 Workspace Memory |
| claude-mem | E(C) | 观察摘要 + 向量 | Apache 2.0 | **否（纯本地）** | **是** | **最贴近的参照实现** |
| OpenMemory | E(A) | Mem0 内核 | 开源 | 否（本地） | 是 | 中 |

## 4. 接入形态：比存储结构更决定成败

这一节是本文最工程化的部分，也是最容易被"比谁准"的评测叙事盖过去的部分。

### 4.1 四种接入点

| 接入形态 | 触发者 | 确定性 | token 成本 | 对 prompt cache 的影响 |
|---|---|---|---|---|
| **MCP 工具** | 模型自主决定调用 | **低**（模型经常不调） | 只在调用时付 | 小（在对话尾部） |
| **Hook 前置注入** | 宿主 Agent 生命周期 | **高** | 每轮都付 | **大**（改动前缀） |
| **SDK / 库内嵌** | 应用代码 | 高 | 可控 | 可控 |
| **运行时替换** | 中间件即宿主 | 高 | — | — |

**这张表解释了为什么所有认真做编码场景的方案最后都上了 hook。** 仅暴露 MCP 工具意味着把"要不要回忆"的决策交给模型——而模型在专注写代码时几乎不会主动去查记忆。Mem0 的 Claude Code 插件是 MCP + hook 双管，OpenViking 是 hook 为主 + MCP 为辅，claude-mem 是纯 hook（5 个）。

> **判断**：这一条直接改写 insight-0002 M5 的实现要点。原文说"自定义 `memory` 工具（读/写/搜）"——**只做工具是不够的，必须同时在 opencode 的消息前置钩子里做确定性注入**，否则做出来的记忆系统会因"模型不查"而看起来毫无效果。同时要接受它必然击穿 prompt cache 前缀（insight-0002 §6 已列此风险），因此注入内容必须**在一次会话内保持稳定**（只在会话启动与压缩后重算，不每轮重算）。

### 4.2 OpenViking Claude Code 插件的召回管线（值得逐步照抄）

从官方 README 与文档还原的流程：

```
用户输入
  → hook 在模型看到之前触发
  → 用 query 检索 OpenViking
  → 排序：向量分数 + query profile 加权 + 词面重叠
  → 在 token 预算内解析内容（L0→L1→L2 按需下钻）
  → 注入 <openviking-context> 块进 prompt
  → 模型开始工作
（会话结束）
  → 自动分析并沉淀本轮对话
  → 剥离此前注入的 context 块，防止自指污染
```

三个实现细节特别值得记：

1. **排序是三信号融合**（向量 + 画像加权 + 词面重叠），不是纯向量。这与 insight-0002 §5 的建议（先上 BM25、别急着上向量）方向一致——**词面信号在记忆语料上从来不是可选项**。
2. **"剥离此前注入的 context 块"**：不做这一步，注入的记忆会被当作新对话内容再次沉淀，形成自我强化的污染循环。这是 insight-0002 §6"记忆污染"风险的一个**具体触发路径**，我们自建时必须防。
3. **hook 是轻量 `.mjs` 脚本直接 HTTP 调服务** + 一个 stdio MCP 代理桥接到 `/mcp`，**不需要 TypeScript 编译或 npm bootstrap**。这个工程取舍（插件保持零构建）对企业内分发很友好。

配置优先级为 环境变量 > 配置文件（`~/.openviking/ov.conf`、`ovcli.conf`）> 内置默认；可调项包括召回 token 预算与条数、压缩位置（客户端/服务端/自动）、按会话或目录 bypass、检索与沉淀分别设超时。**"按目录 bypass"和"检索/沉淀分别设超时"是两个很务实的设计**，前者对应敏感仓库，后者避免记忆服务抖动阻塞主流程。

## 5. 这些评测数字该怎么读

本文引了四组分数，它们**互相之间不可比**，理由如下。

| 问题 | 说明 |
|---|---|
| **基线不同** | OpenViking 的基线是"Agent 原生记忆"，Mem0 的基线是自己的旧版本，Zep 的对比用 GPT-4o 跑 |
| **模型不同** | Mem0 默认 GPT-5-mini，Zep 论文用 GPT-4o，OpenViking 跑在三个不同 Agent 上 |
| **时间不同** | 数字跨 2025-01 到 2026-04，中间模型能力本身涨了一大截 |
| **都是自评** | Mem0、Supermemory、Zep、OpenViking 各自的博客里都是自己第一 |

LoCoMo 本身的局限也已被普遍讨论：约 300 轮、平均 ~9K token 的对话，问题分单跳/多跳/时序/开放域四类；文本重叠指标（BLEU/ROUGE/F1）会惩罚措辞不同的正确答案，LLM judge 也不完美；且它是**静态**语料，覆盖不了生产环境的边缘情况。2026 年出现的替代评测（LongMemEval、BEAM、ConvoMem，以及主张"评测应像真实部署那样让写入/更新/检索/个性化随时间交互"的 Agent-native 评测思路）说明这个方向本身还没收敛。

> **判断**：**这些分数只能用来判断"某个方向是否值得看"，不能用来选型。** 对我们真正有意义的评测只有一个——用我们自己的仓库、自己的记忆语料、自己的任务集跑一遍。insight-0002 §7 已列了"BM25 在中文为主记忆语料上的召回"这一项待验证问题，本文把它升级为：**任何外部记忆方案进入候选前，必须先过这个自建评测集**，不看厂商分数。

另外值得单独记一笔的是宿主侧的对照数据：Anthropic 的 context editing（服务端清理旧工具调用/思考块，**不破坏 prompt cache 前缀**）在 100 轮 web search 评测中降低 84% token 消耗，memory + context editing 组合在 agentic search 上带来 39% 提升。这组数字的价值在于——**它说明 L3（会话内调度）的收益量级不低于 L4（跨会话记忆）**，而 L3 是外挂中间件完全帮不上忙的部分。

## 6. 对 opencode 定制的启示

### 6.1 买还是自建

| 选项 | 结论 | 理由 |
|---|---|---|
| 引入 OpenViking 作为依赖 | **否** | ① AGPLv3 主体，内部平台若对外提供服务需法务评估；② 引入 Python 服务 + 向量后端 + embedding provider 三重运维依赖，与 insight-0002 §3.5"别用做记忆的名义顺手上向量库"的结论直接冲突；③ 分层与检索逻辑在服务端，我们无法按仓库策略定制 |
| 引入 Mem0 / Supermemory 云服务 | **否** | 记忆内容 = 公司代码库的结论性知识，出网是硬性合规问题；自建 server 又回到运维依赖 |
| 引入 claude-mem 类纯本地方案 | **可评估** | 纯本地、Apache 2.0、已支持 opencode；但它的记忆模型（工具轨迹观察）与我们要的（结论性知识）不完全一致 |
| **自建 + 借鉴设计** | **推荐** | 记忆语料量级小（单仓库百条级），FTS5 足够；企业价值在治理与私有上下文，这部分本来就买不到 |

这与 [ai-coding-insight-0001](2026-08-11-cli-coding-agent-landscape.md) 的总判断一致：**中立内核在通用能力上必然滞后，我们的价值在治理、私有上下文与流程闭环。**记忆恰恰是"私有上下文"的核心载体，外包出去等于把差异化交出去。

### 6.2 应当补进 insight-0002 优先级清单的三条

以下三条是本次横向调研的净增量，建议并入 insight-0002 §5 第二档（记忆最小闭环）一起做，**均不增加基础设施依赖**：

| 编号 | 内容 | 来源 | 增量成本 |
|---|---|---|---|
| **M18** | **记忆注入必须走 hook 前置，不能只做 MCP/工具** | §4.1 | 低（原本就要写插件） |
| **M19** | **注入的记忆块必须在沉淀前被剥离**，防自指污染循环 | OpenViking §4.2 | 极低（一个正则） |
| **M20** | **记忆条目带有效期语义**（不只是 `modified` 时间戳），过期作废而非删除 | Zep 双时态 §路线B | 低（frontmatter 加两个字段） |

另建议把 insight-0002 M7（记忆加载预算）的实现从"Claude Code 两级结构"升级为**三级**：索引常驻 → 主题文件 L1 概览 → 全文 L2 按需。OpenViking 的 ~100 / ~2k token 分层给了一个可直接采用的量级参考。

### 6.3 明确不抄的

- **不抄向量服务栈**：记忆语料百条级，BM25 + 词面重叠已足够（且 OpenViking 自己的排序里词面重叠也是必备信号）。
- **不抄知识图谱**：建图的 LLM 成本与 schema 维护成本远超收益，而"一段调试心得"本来就不适合表达成实体关系。
- **不抄 System 2 记忆**（存推理步骤）：体量大、复用率存疑，等 Cipher 那边跑出实证再说。
- **不抄 Letta 式运行时**：会替换宿主，与我们基于 opencode 的路线根本冲突。

## 7. 风险与反模式

| 风险 | 说明 | 对策 |
|---|---|---|
| **被 benchmark 叙事牵着走** | 四家都自称第一，横向不可比（§5） | 只认自建评测集；对外汇报标注"厂商自报" |
| **AGPL 传染** | OpenViking 主体 AGPLv3，网络服务形态同样触发义务 | 借鉴设计而非引用代码；若确需引入先过法务 |
| **记忆自指污染** | 注入的记忆被当作新内容再次沉淀，错误结论被指数强化 | M19：沉淀前剥离注入块（这是必做项，不是优化项） |
| **模型不主动查记忆** | 只做 MCP 工具会让整套系统"看起来没效果" | M18：hook 前置确定性注入 |
| **把外挂记忆当成万能药** | 中间件只覆盖 L4（+部分 L2/L5），**完全不解决 L1/L3** | 压缩阈值、摘要衰减必须自己修（insight-0002 §5 第一档不可跳过） |
| **记忆出网** | 记忆内容是公司代码库的结论性知识，比源码更浓缩 | 排除一切云服务方案；沉淀路径做敏感信息扫描 |
| **拿通用场景的效果外推编码场景** | "记住用户偏好"与"记住架构决策"是两类召回问题 | 评测集必须用真实研发语料构造 |

## 8. 待验证问题

| 问题 | 为什么重要 | 验证方式 | 状态 |
|---|---|---|---|
| L0/L1/L2 三级分层在**单仓库百条级**语料上是否过度设计 | 决定 M7 做两级还是三级 | 用 100 条真实记忆构造两版加载策略对比召回与 token | 未开始 |
| hook 前置注入实际击穿多少 prompt cache | 决定 M18 的注入频率策略 | 对比注入/不注入两态的 `cache.read` 占比 | 未开始 |
| claude-mem 在 opencode 上的实际可用性 | 若可用可省掉一轮自研 | 在测试仓库实跑，重点看它的记忆模型是否匹配我们的需求 | 未开始 |
| OpenViking 自报的 Claude Code 基线 57.21% 是何种配置 | 决定这组数字是否可引用 | 需一手复现或找到独立复现 | **阻塞**（官网与文档站在本次网络环境下不可达） |
| Cipher 的 Workspace Memory 权限模型 | 团队共享记忆是我们唯一买不到的能力，值得参考其设计 | 读其开源实现 | 未开始 |
| 双时态在编码记忆上的最小可用形态 | M20 的落地形态（两个字段够不够） | 设计评审 | 未开始 |

## 参考资料

1. [volcengine/OpenViking · README](https://github.com/volcengine/OpenViking)（访问日期 2026-08-12）
2. [volcengine/OpenViking · README_CN](https://github.com/volcengine/OpenViking/blob/main/README_CN.md)（访问日期 2026-08-12）
3. [volcengine/OpenViking · examples/claude-code-memory-plugin/README_CN](https://github.com/volcengine/OpenViking/blob/main/examples/claude-code-memory-plugin/README_CN.md)（访问日期 2026-08-12）
4. [Castor6/openviking-plugins —— Claude Code 记忆插件市场](https://github.com/Castor6/openviking-plugins)（访问日期 2026-08-12）
5. [OpenViking x OpenClaw：开箱即用，解决 Agent 的长期记忆困局 · InfoQ](https://www.infoq.cn/article/ctgNSzTYmLhsRaUVZESe)（访问日期 2026-08-12）
6. [mem0ai/mem0 · README](https://github.com/mem0ai/mem0)（访问日期 2026-08-12）
7. [Mem0 官方文档 · Claude Code 集成](https://docs.mem0.ai/integrations/claude-code)（经检索结果转述，站点在本次网络环境下不可直接访问，访问日期 2026-08-12）
8. [Zep: A Temporal Knowledge Graph Architecture for Agent Memory · arXiv 2501.13956](https://arxiv.org/pdf/2501.13956)（访问日期 2026-08-12）
9. [Graphiti: Knowledge graph memory for an agentic world · Neo4j](https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/)（访问日期 2026-08-12）
10. [Sleep-time Compute · Letta](https://www.letta.com/blog/sleep-time-compute/)（访问日期 2026-08-12）
11. [Sleep-time agents · Letta Docs](https://docs.letta.com/guides/agents/architectures/sleeptime/)（访问日期 2026-08-12）
12. [Cipher Overview · Byterover Docs](https://docs.byterover.dev/cipher/overview)（访问日期 2026-08-12）
13. [campfirein/cipher（现 byterover-cli）](https://github.com/campfirein/cipher)（访问日期 2026-08-12）
14. [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem)（访问日期 2026-08-12）
15. [Architecting a Brain-Inspired Memory Engine · Supermemory](https://supermemory.ai/blog/memory-engine/)（访问日期 2026-08-12）
16. [Agent Memory Frameworks Showdown: cognee vs Mem0 vs Zep vs Letta](https://theaiengineer.substack.com/p/cognee-vs-zep-vs-mem0-vs-letta)（访问日期 2026-08-12）
17. [Persistent Memory Layer for AI Agents 2026 · Cognee](https://www.cognee.ai/blog/guides/open-source-memory-frameworks-llm-agents)（访问日期 2026-08-12）
18. [Managing context on the Claude Developer Platform · Anthropic](https://claude.com/blog/context-management)（访问日期 2026-08-12）
19. [Agent_Memory_Techniques · LoCoMo 评测局限讨论](https://github.com/NirDiamant/Agent_Memory_Techniques/blob/main/all_techniques/29_memory_benchmarks_LoCoMo/memory_benchmarks_locomo.ipynb)（访问日期 2026-08-12）
20. [ai-coding-insight-0002《AI Coding 工具的记忆与上下文管理》](2026-08-12-memory-context-management-landscape.md)
21. [ai-coding-insight-0001《CLI 形态 AI Coding 工具的技术路线与企业化差距》](2026-08-11-cli-coding-agent-landscape.md)
