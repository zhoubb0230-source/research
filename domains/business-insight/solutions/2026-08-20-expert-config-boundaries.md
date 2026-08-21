---
id: business-insight-solution-0006
title: 数字专家的配置、人格与技能边界
domain: business-insight
type: solution
status: draft
created: 2026-08-20
updated: 2026-08-20
tags: [architecture, multi-agent, orchestration, landing]
vendors: [openclaw, deepseek-harness]
related: [business-insight-solution-0001, business-insight-solution-0003, business-insight-solution-0004, business-insight-solution-0005]
summary: 三层不是两层：能配置的必须配置，但每轮注入的散文和按需加载的技能要分开
---

# 数字专家的配置、人格与技能边界

> **面向**：把一个多角色专家团落到具体 harness 时，决定"每一句约束写在哪"
> **交付**：`../assets/expert-team/BOUNDARIES.md`（规范）+
> `../assets/expert-team/experts/`（12 位专家的独立目录）+ 两个 harness 的装配包
> **状态说明**：`draft`。平台事实来自两家的官方文档（2026-08-20 查阅），
> 装配脚本已在本仓库环境实测；**两家的配置形状均有待实机校验项**，
> 分别见各自 NOTES 的「上线前必须校验」。

## TL;DR

- **目标**：给"这句约束该写进配置、人格文件，还是技能"一个可执行的判据。
- **推荐方案**：**三层**（配置 T1 / 人格 T2 / 技能 T3），依次判定、命中即停。
- **关键取舍**：
  - "能提取到专家配置的优先提取到专家配置"——**上半句要加强成"必须"**，
    因为散文是请求自觉、配置是运行时不给路；
  - **下半句要反驳**——人格层每轮全量注入并且有硬上限，
    把流程往里塞会挤掉真正需要每轮压着的立场与禁令。
- **代价**：同一位专家的定义被拆成三处，改动要同时看意图（`expert.yaml`）与
  平台字段（`entry.json5` / `spawn.json`）。这是为可读性付的价。

---

## 1. 背景与目标

### 1.1 问题陈述

`solution-0003`（OpenClaw）与 `solution-0005`（dsh）各自把专家团落了地，但两份落地包
存在三个结构问题：

1. **没有"一位专家一个交付件"**。角色定义散在 `roles.json` + `prompts/` + 模板里，
   要看懂"质疑审查专家到底被约束成什么样"，得同时打开四个文件。
2. **约束层次混淆**。"你必须与分析师使用不同模型"这种**能被配置强制**的话，
   和"你的 KPI 是推翻数"这种**只能靠自觉**的话，写在同一份提示词里，
   读的人无从分辨哪些是真的拦得住。
3. **两个包的名册不一致**。OpenClaw 包用旧角色名，dsh 包用泛化后的名，
   `DSH-NOTES` 自己都记了一笔"尚未同步"。

### 1.2 目标与非目标

**目标**

- 每位专家一个独立目录，边界清晰，可单独阅读、单独验收
- 给出"这句话写在哪一层"的可操作判据
- 两个 harness 共用同一份专家正本，名册对齐
- 把两家平台的**真实**配置能力查清楚，不再靠推断

**非目标**

- 不重新调判据、权重、算力档位（本次只重构装配，不动调参）
- 不实机跑通任一 harness（本环境没有 gateway，也没有 dsh 运行时）

---

## 2. 结论：三层，不是两层

| 层 | 载体 | 谁执行 | 成本 | 违反的后果 |
|---|---|---|---|---|
| **T1 配置** | OpenClaw `agents.entries.<id>`；dsh provider 路由 + preset + `spawnTeammate` 实参 | **运行时** | 零 token | 做不到——路不存在 |
| **T2 人格** | `IDENTITY.md` / `SOUL.md` / `AGENTS.md` / `USER.md`；dsh 的 `spawnTeammate(prompt)` | 模型自觉 | **每轮全文注入** | 模型可能不遵守 |
| **T3 技能** | `skills/<name>/SKILL.md` | 模型按需调用 | 提示词里只占 name + description | 模型可能不去调用 |

判定顺序：

```
能表达成运行时的配置字段吗？ ── 能 ──→ T1（必须，不允许只写散文）
              │ 不能
              ↓
是每一轮推理都要压着的判断底色？ ── 是 ──→ T2
              │ 不是（只在某个动作里用）
              ↓
                                          T3
```

### 2.1 为什么 T1 是"必须"而不是"优先"

散文是**请求模型自觉**，配置是**运行时不给这条路**。
两者不是同一种东西的强弱版本，是"承诺"与"机制"的区别。

本次从散文搬进 T1 的约束（OpenClaw 侧）：

| 原来的提示词句子 | 现在落在哪 |
|---|---|
| "你必须与分析师使用不同模型" | `entries.red-team-challenger.model` |
| "你不看分析师的推理过程" | `sessions_spawn(context: "isolated")` |
| "报告生成专家不得执行命令绕过发布闸" | `entries.report-writer.tools.deny` |
| "报告生成专家只能写自己的工作区" | `entries.report-writer.sandbox.mode: "all"` |
| "分析师不取数" | `tools.deny: ["browser","web_search","web_fetch"]` |

最后一条最能说明问题：原方案只写了"你不取数"。一个能检索的分析角色，
会在"缺一个数"的时候顺手查一下，从而**同时绕过取证与核证两道闸**，
而产出看起来完全正常，事后极难追查。现在它的工具表里没有这三项。

### 2.2 为什么 T2 与 T3 必须分开（这里反驳"都往配置塞"）

**T2 与 T3 的分界不是重要性，是"每一轮要不要"。**

- OpenClaw 的 bootstrap 文件**每轮全量注入**，单文件上限 20000 字符、
  合计 60000 字符，**超出即截断**；运行时只说"有文件被截断了"，不说截了哪个。
  被截掉的总是文件末尾——也就是"我绝不做的事"那一段。
- dsh 的 teammate 人格走 `spawnTeammate(prompt)`，整段进入提示词前缀，同样每轮都在。
- 而技能是**懒加载**的：两家都只把 `name` 与 `description` 放进提示词目录
  （OpenClaw 给的量化是每个约 97 字符 + 字段长度），正文在被调用时才读。

所以判据是：

| 内容性质 | 层 |
|---|---|
| 判断底色（立场、KPI、禁令） | T2 |
| 交接契约（输入输出、schema、给谁） | T2 |
| 操作流程（只在我那个动作里用到的步骤、清单、判定表） | **T3** |
| 长表格（来源清单、锚点表、类型路由表） | **T3** |

最典型的一例：洞察总调度原先把 220 行运行手册拼进 `AGENTS.md`，装配后 7824 字符。
现在手册变成技能 `run-insight-batch`，`AGENTS.md` 只留"什么时候去读这本手册"，
降到 1001 字符。**判断留 T2，流程进 T3。**

> **一处更正**：早先的 `OPENCLAW-NOTES.md` 说这个文件"约 18 KB，逼近 20000 上限"。
> 那是拿 **UTF-8 字节数**比一个**字符数**上限——中文一字三字节。
> 实测旧装配是 7824 字符，离 20000 还有一半余量，**截断风险当时被高估了**。
> 但拆分的理由不受影响：真正的问题不是会不会截断，
> 而是那 6000 多字符只在推进状态时用得上，却在每一轮推理里被重新注入。

---

## 3. 平台事实：两家的"专家配置"到底是什么

### 3.1 OpenClaw：工作区文件 + `agents.entries`

工作区文件（= T2 人格层）：

| 文件 | 官方定义 | 本方案怎么用 |
|---|---|---|
| `AGENTS.md` | 操作指令，每次会话开始加载 | 输入输出契约、schema、何时读技能 |
| `SOUL.md` | 人格、语气、边界 | 立场、KPI、禁令；护栏内联在最前 |
| `IDENTITY.md` | 名字、vibe、emoji | 名字 + emoji + 在骨架里的位置 |
| `USER.md` | 用户模型，指令式条目，**独立 4000 字符预算** | 委托方模型（12 位共用一份） |
| `MEMORY.md` | 精选长期记忆，**只在主会话加载** | **不用**，见 §3.2 |
| `skills/` | 工作区技能，该工作区优先级最高 | T3 |
| `BOOT.md` / `BOOTSTRAP.md` | 启动检查单 / 首次运行仪式 | 不用；`skipBootstrap: true` |

⚠️ **没有 `TOOLS.md`。** 文档明确：环境相关的工具约定放在 `AGENTS.md` 的
`## Tools` 小节，而且原话是 *"It does not control tool availability; it is only guidance."*
**工具可用性由 `agents.entries.<id>.tools.{profile,alsoAllow,allow,deny}` 决定。**

关键事实：**用 `agentId` 派发子会话时，子会话加载的是目标 agent 工作区的引导文件**
（*"Native sub-agents still load bootstrap files from the target agent workspace"*）。
这是"一位专家一个工作区"这套装配能成立的前提。

### 3.2 为什么本方案不给专家配 `MEMORY.md`

洞察是**批次任务**。跨批次沉淀的东西应该是 `baseline.json`——结构化、可被 `trend`
算子消费、可被校验——而不是自然语言记忆。

具体风险：上一批次"某某市场大约多少"的记忆，会在下一批次变成一个**没有 `evidence_id`
的数字**。它绕过了取证与核证两道闸，而且看不出来，与全员护栏第一条直接冲突。

### 3.3 DeepSeek Harness：四个完全不同的机制

dsh **没有等价的一套文件**。同样的职责被拆到四处：

| OpenClaw 的东西 | dsh 的对应物 | 逐专家？ |
|---|---|---|
| `SOUL.md` | `spawnTeammate(prompt)` | ✅ **唯一的逐专家人格通道** |
| `IDENTITY.md` | `spawnTeammate` 的 `name` + `description` | ✅ |
| `AGENTS.md` | `dsh-agent-instructions` 加载的 `AGENTS.md` 链 | ❌ 按目录加载，队友共享 cwd |
| `USER.md` / `MEMORY.md` / `TOOLS.md` | 无对应物 | — |
| `agents.entries.<id>` | `agent-loop.agents[]`（字段极少）+ preset 目录 | ❌ preset 是整队一份 |

**dsh 确实有"一目录一组合"的机制——agent preset**：
`<preset-root>/<preset-id>/agent.cordis.yml` + `preset.yml` + 随目录搬家的相对路径资源。
但它**不是逐专家的**：文档明确子代理的孩子通过 `composeFrom()` 加入父的常驻组合，
**从不走 `mount()`**。所以一个专家团 = 一个 preset，不是 12 个。

**结论：dsh 上逐专家能配的只有四样**——`name` / `description` / `prompt` / `provider`
（外加 `context: 'fresh' | 'fork'`）。
`AgentOptions` 经查只有 `{ provider?, model?, maxTokens? }`，**没有 prompt，也没有 effort**。

---

## 4. 两家的能力差与它的后果

| 能力 | OpenClaw | dsh |
|---|---|---|
| 逐专家模型 | ✅ `entries.*.model` | ✅ `spawnTeammate(provider)` |
| 逐专家思考档 | ✅ `thinkingDefault`（含 `xhigh`/`max`） | ⚠️ 只能"一档一条 provider 路由"（`reasoningEffort` 是 provider 级） |
| 逐专家工具面 | ✅ `tools.{profile,alsoAllow,allow,deny}` | ❌ **队友共用 Lead 的组合** |
| 逐专家沙箱 | ✅（需 Docker 等后端） | ❌ 且队友共享同一 cwd |
| 逐专家技能白名单 | ✅ `entries.*.skills` | ❌ 目录共用 |
| 逐专家人格文件 | ✅ 各自工作区 | ⚠️ 只有 `spawnTeammate(prompt)` 一条 |
| 上下文隔离 | ✅ `context: "isolated"` | ✅ `context: 'fresh'` |

### 4.1 后果：同一条约束，两边的强度不同

OpenClaw 上"对比分析专家不取数"是**它的工具表里没有 browser**；
dsh 上是**它答应了不去查**。

**这必须写明，不能让人以为两边等价。** 验收方式也要跟着变：
dsh 侧按承诺检验（抽查产出有没有越界痕迹），不能按机制检验。

### 4.2 dsh 上仍然成立的两道机制闸

1. **preset 里整队都不装 bash / 终端类工具**——没有任何一位专家能跑脚本。
   代价是 Lead 也跑不了发布脚本，所以**发布由人在 dsh 外面执行**。
   收益是这道闸仍然是机制而不是承诺。
2. **`context: 'fresh'`**——队友没有父会话历史种子，红队的上下文隔离由平台保证。

### 4.3 dsh 上默认不成立的一条：红队异源

异源要求的是**不同模型**，不是不同 effort。只注册 DeepSeek 一家的话，
红队与刻画同源，同源盲区依然存在。
`cordis.patch.yml` 里留了注释掉的第二 provider 段；不打开就跑，
**要在验收时如实记下这一项退化**。

---

## 5. 交付物

```
assets/expert-team/
├── BOUNDARIES.md                  三层边界规范（本方案的规范正文）
└── experts/                       12 位专家的独立目录 ← 唯一真相源
    ├── README.md                  名册 + 工具面一览 + 改东西改哪儿
    ├── _shared/                   GUARDRAILS.md / USER.md / BATCH-LAYOUT.md
    └── <agentId>/
        ├── expert.yaml            T1 装配意图（平台中立）
        ├── IDENTITY.md            T2
        ├── SOUL.md                T2
        ├── AGENTS.md              T2
        ├── skills/<skill>/SKILL.md  T3
        └── README.md              边界一句话 + 怎么验收它装对了

assets/expert-team-openclaw/
├── openclaw.config.json5          编排框架（defaults / bindings / hooks）
├── experts/<agentId>/entry.json5  逐专家 agents.entries 片段
├── runtime/{coordinator,leaf}.md  OpenClaw 运行约定
└── install.py                     装配工作区 + 合并配置 + 字符预算自检

assets/expert-team-dsh/
├── orchestration/cordis.patch.yml            宿主组合覆盖
├── orchestration/preset/business-insight-team/  preset 组合（整队共用）
├── experts/<agentId>/spawn.json              逐专家 spawnTeammate 实参
├── runtime/{lead,teammate}.md                dsh 运行约定
└── install.py                                装配 AGENTS.md + PROMPTS + skills + roster
```

**`expert.yaml`（意图）与 harness 侧配置（真实字段）故意分成两份。**
合并成一份要么丢掉可读性（"这个角色不该能联网" vs `tools.deny: ["browser",...]`），
要么在平台字段变化时全体返工。代价是改算力档、工具面、派发白名单时**两处都要改**。

装配后实测：12 位专家的人格层在 3629–4072 字符之间，占 OpenClaw 合计预算的 7% 以内。

---

## 6. 风险与待办

| # | 风险 | 处置 |
|---|---|---|
| 1 | dsh 的 `cordis.patch.yml` 顶层形状未经实机确认，**错了不报错只静默失效** | 先 `dsh --profile web --dump-config` 比对，再跑批次 |
| 2 | dsh 的 provider 路由名是否等于 row id 未确认 | 同上。若只能注册一条路由，逐专家算力差异无法实现，须如实记退化 |
| 3 | OpenClaw 的 `session.reset.mode: "off"` 是推断值 | `openclaw config schema` 校验；不合法就删掉该段改用长 idle 阈值 |
| 4 | 报告生成专家的沙箱需要 Docker 等后端 | 无后端时的降级方案只是**信息隐藏不是访问控制**，见 OPENCLAW-NOTES §5 |
| 5 | dsh 上红队与刻画默认同源 | 注册第二家 provider，或在验收结论里标注该项退化 |
| 6 | 阶段硬门仍由总调度自觉执行（两家都无原生阶段网关） | 台账事后审计 + 关键不可逆动作人工签署；致命的那道闸已落到脚本上 |

**下一步**：按 `assets/insight-service/acceptance.md` 的八项验收跑一次真实批次
（建议用 `landscape-survey.brief.json`，因为结论当场可验），
并把两家 NOTES 里的待校验项逐条勾掉。
