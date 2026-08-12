---
id: ai-coding-insight-0002
title: AI Coding 工具的记忆与上下文管理：机制拆解与 opencode 差距分析
domain: ai-coding
type: insight
status: review
created: 2026-08-12
updated: 2026-08-12
tags: [cli-agent, coding-agent, context-engineering, memory, agent-skills, repo-understanding, tech-route]
vendors: [opencode, claude-code, codex, cursor, mimo-code]
related: [ai-coding-insight-0001, ai-coding-solution-0001, ai-coding-vendor-0001]
summary: opencode 有压缩无记忆；六层能力里它缺第四层，且第一、三、六层只做到及格线
---

# AI Coding 工具的记忆与上下文管理：机制拆解与 opencode 差距分析

> 本文是 `ai-coding` 领域下**「记忆与上下文管理」专题**的主报告，服务于"基于 opencode 定制记忆与上下文能力"的实现方案与排期决策。
> 事实核对日期：2026-08-12。opencode 与 MiMo Code 的结论来自**源码级核对**（opencode `dev` @ `d041eee`；MiMo-Code `main`），非文档转述。

## TL;DR

- **opencode 有上下文压缩，但完全没有记忆。** 源码级证据：`packages/opencode/src/` 全目录搜索 `memory` 仅命中 xAI 插件与堆栈调试 CLI，不存在任何记忆子系统。会话结束即失忆，唯一的延续手段是 `--continue` / `--session` / fork。
- **把能力拆成六层看，opencode 的缺口分布很不均匀**：L4 跨会话记忆 = 0；L1 静态指令层、L3 会话内调度、L6 可见性 = 及格线；L2 按需知识（Skills）与 L5 检索（LSP）反而不弱。**不要平均用力**。
- **opencode 的压缩只在窗口打满时触发**（`isOverflow` 判定为 `已用 >= limit.input - reserved`），没有 Claude Code 的可配置提前阈值（`/autocompact 500k`）。这是**单点改动、收益立刻可见**的一处。
- **两个未写进官方文档的配置项是现成的调优面**：`compaction.tail_turns`（默认 2）与 `compaction.preserve_recent_tokens`（默认 `min(8000, max(2000, usable×0.25))`）。文档只提到 `auto` / `prune` / `reserved`。
- **MiMo Code 的模块清单就是一张投入分布图**：checkpoint 相关 8 个文件 > 跨工具导入 5 个 > memory 6 个。真正难的不是"把记忆存下来"，而是**检查点与任务进度的对齐、校验、重试**。这决定了我们的排期应该把"检查点"和"记忆"当成两件事。
- **优先级建议（详见 §5）**：先做 ①提前压缩阈值 + ②开启并调优 prune + ③压缩后指令重注入 + ④记忆最小闭环（文件 + BM25），这四件覆盖了大部分收益且都不需要动内核。

## 1. 分析框架：把"记忆与上下文"拆成六层

业界讨论这个话题时最大的混乱，是把"写一个 AGENTS.md"、"压缩会话"、"跨会话记住结论"、"检索代码库"混为一谈。它们的触发时机、生命周期、失效模式完全不同。本文统一按下面六层拆解，后续所有对比都落在这个框架里。

| 层 | 名称 | 解决什么 | 生命周期 | 典型失效 |
|---|---|---|---|---|
| **L1** | 静态指令层 | 每次会话都必须知道的规范 | 每会话全量加载 | 太长→稀释注意力；冲突→随机取一条 |
| **L2** | 按需知识层 | 只在特定任务/路径下需要的知识 | 命中时才进上下文 | 描述写不好→模型不去加载 |
| **L3** | 会话内调度 | 窗口不够用时留什么、丢什么 | 单次会话内 | 压缩丢关键前提；剪枝破坏缓存 |
| **L4** | 跨会话记忆 | 上一次学到的东西下一次还在 | 跨会话持久 | 记忆污染；陈旧结论被反复注入 |
| **L5** | 检索层 | 从代码库/知识库里找到相关片段 | 按查询触发 | 召回不足；索引成本与新鲜度 |
| **L6** | 可见性与控制 | 看得见、改得动、关得掉 | 全程 | 无法审计→记忆无法维护 |

## 2. 五个工具的横向定位

| 层 | Claude Code | Codex CLI | Cursor | MiMo Code | **opencode** |
|---|---|---|---|---|---|
| L1 静态指令 | ★★★ 目录树全量拼接 + `.claude/rules/` + 托管策略层 + 排除机制 | ★★ `AGENTS.md` | ★★★ `.cursor/rules/*.mdc` 四种加载模式 + `AGENTS.md` | ★★ 继承 opencode | ★★ `AGENTS.md`/`CLAUDE.md`，**首类命中即停**，无作用域 |
| L2 按需知识 | ★★★ Skills + `paths:` 作用域规则 + 压缩后按配额重注入 | ★★ Skills | ★★★ 规则四模式（always / globs / description / manual） | ★★★ 50+ 内置技能 + BM25 自动加载 | ★★ Skills（渐进披露），**剪枝时受保护**；无路径作用域 |
| L3 会话内调度 | ★★★ 阈值可配 + 带指示压缩 + 磁盘重注入 + 子智能体隔离 | ★★★ 阈值可配 + 循环边界触发 + 请求回放 | ★★ 自动摘要 | ★★★ 独立 prune + 预算化读取 + `/context-limit` | ★★ 打满才压缩 + 可选剪枝 + 压缩插件钩子 |
| L4 跨会话记忆 | ★★★ auto memory（自动写、索引化、分主题） | ★ 靠 `AGENTS.md` 人工维护 | ★★ 项目级 Memories（现状有分歧，见 §3.4） | ★★★ SQLite FTS5 + 检查点 + `/dream` `/distill` | **✗ 无** |
| L5 检索 | ★★ 自主探索 + 子智能体 + tool search | ★★ 自主探索 | ★★★ AST 分块 + 向量库 + Merkle 增量 | ★★★ 继承 + 记忆 BM25 | ★★ ripgrep + LSP（含实验性符号级工具） |
| L6 可见性 | ★★★ `/context` `/memory` `InstructionsLoaded` hook | ★★ | ★★ 设置页可审阅规则/记忆 | ★★ `/context-limit` 等 | ★ 无 `/context`、无 `/memory` |

## 3. 机制深挖

### 3.1 L1 · 静态指令层

**opencode（源码：`session/instruction.ts`）**

- 全局：`~/.config/opencode/AGENTS.md`，若不存在则回落 `~/.claude/CLAUDE.md`，**取到一个就 break**。
- 项目：按 `AGENTS.md` → `CLAUDE.md` → `CONTEXT.md`（已废弃）顺序 `findUp`。注释写得很直白——"The first project-level match wins so we don't stack AGENTS.md/CLAUDE.md from every ancestor"，即**第一类文件命中后不再尝试其他文件名**；但同一文件名在多级祖先目录中的多个匹配**会全部堆叠**。
- `instructions` 配置项：支持 glob 与 `http(s)` 远程 URL，远程拉取 5 秒超时，**失败静默降级为空字符串**（`Effect.catch(() => "")`）——这一点在企业强制注入场景下是隐患：网络抖动会让公司规范悄悄消失。
- **嵌套指令懒加载**（`resolve()`）：当模型读取某个文件时，从该文件所在目录向上走到项目根，沿途发现的 `AGENTS.md`/`CLAUDE.md` 会被附加进上下文，**每条 assistant 消息只附一次**（`claims` Map 去重），并跳过已在系统层加载或已被读过的。值得注意的是判定"已读过"的 `extract()` 会跳过 `state.time.compacted` 为真的读取记录——也就是说**剪枝之后，嵌套指令有机会被重新附加**，这是一个隐性的正确设计。

**对标做法与差异**

| 差异点 | opencode | Claude Code | Cursor |
|---|---|---|---|
| 多文件组织 | 只有单一入口文件 | `.claude/rules/*.md` 递归发现，可分主题、可符号链接共享 | `.cursor/rules/*.mdc` |
| 路径作用域 | **无** | `paths:` frontmatter，glob 匹配时才载入 | `globs` frontmatter（auto-attached） |
| 模型自主拉取 | 无（靠 Skills 代偿） | 无（靠 Skills） | **有**：`description` 驱动的 agent-requested 规则 |
| 引用展开 | 无 `@import` | `@path` 递归展开，最多 4 跳，跳过代码块内的 `@` | — |
| 组织级强制 | 靠托管配置里的 `instructions` 远程 URL（有静默失败风险） | 托管策略路径下的 `CLAUDE.md`，或 `managed-settings.json` 的 `claudeMd` 键，**个人设置无法排除** | — |
| 降噪/排除 | 无 | `claudeMdExcludes`（glob，跨设置层合并）；HTML 块注释在注入前剥离 | — |
| 体积约束 | 无提示 | 建议单文件 < 200 行；`/doctor` 会提出裁剪建议 | — |

> **判断**：L1 层 opencode 最实际的两个缺口是**路径作用域规则**与**远程指令的失败可见性**。前者在大仓里直接决定"每次会话浪费多少 token 读无关规范"，后者是合规风险。`@import` 与排除机制优先级可以放低。

### 3.2 L2 · 按需知识层

三种工具在这一层的核心机制是同一个——**渐进披露**：只把 `name` + `description` 放进工具描述里，正文等模型主动调用才加载。opencode 已完整实现（`skill` 工具 + `<available_skills>` 列表 + 按名通配的权限控制）。

真正的差异在**压缩之后会发生什么**：

- **Claude Code**：已调用的技能正文在压缩后**从磁盘重注入**，单技能上限 5,000 token、总计 25,000 token，超额时丢最老的；截断保留文件开头（所以官方建议把最重要的指令写在 `SKILL.md` 顶部）。
- **opencode**：技能正文**不重注入**，压缩后只剩摘要里的只言片语。但有一个补偿设计——剪枝时 `PRUNE_PROTECTED_TOOLS = ["skill"]`，**技能工具的输出永不被剪掉**。所以在"未压缩但已剪枝"的区间里技能是安全的，一旦真正压缩就丢失。

> **判断**：这是一处"改动极小、收益明确"的差距。在 `experimental.session.compacting` 钩子里把本次会话已加载的技能列表写进压缩上下文，或压缩后重新触发加载，都能在插件层解决，**不需要动内核**。

### 3.3 L3 · 会话内调度（opencode 源码级拆解）

这一节是全文最重要的部分，因为它决定了我们能在**不改内核**的前提下调多少。

#### 触发条件（`session/overflow.ts`，34 行）

```
usable = model.limit.input
         ? model.limit.input - reserved
         : context - maxOutputTokens
reserved = cfg.compaction.reserved ?? min(20000, maxOutputTokens)

isOverflow = (input + output + cache.read + cache.write) >= usable
```

**关键结论**：opencode 只在**上下文几乎打满**时才压缩。对比：

| 工具 | 触发点 | 可配置性 |
|---|---|---|
| opencode | 已用 ≥ `limit.input − reserved`（≈100%） | 只能通过调大 `reserved` 间接提前 |
| Claude Code | 按模型有默认阈值，`/autocompact 500k` 可显式设定 | ✅ 直接配置 |
| Codex CLI | 200k 窗口下约 167k（≈83%） | ✅ `config.toml` 可覆盖 |

打满才压缩的代价是：**压缩发生在模型状态最差的时刻**（上下文最拥挤、注意力最稀释），摘要质量最低，且一次性丢弃最多。而**调大 `reserved` 是一个纯配置项**，可以立刻把触发点前移。

#### 保留策略（`session/compaction.ts` 的 `select()`）

1. 把消息切成 turn（以非压缩类 user 消息为界）。
2. 取最后 `tail_turns` 轮（`cfg.compaction.tail_turns ?? 2`）作为候选。
3. 预算 `preserve_recent_tokens ?? min(8000, max(2000, usable × 0.25))`。
4. 从最新一轮往回累加，装得下就整轮保留；装不下就调用 `splitTurn` 在这一轮内部**从前往后找一个能塞进剩余预算的起点**，实现"半轮保留"。
5. 其余为 head，送去做摘要。

> **`tail_turns` 与 `preserve_recent_tokens` 均未出现在官方文档中**（文档只写了 `auto` / `prune` / `reserved`）。这意味着我们有两个现成但无人知道的调优旋钮。

#### 摘要输入的构造（`serialize()`）

head 消息被序列化成纯文本：`[User]:` / `[Assistant]:` / `[Assistant reasoning]:` / `[Assistant tool call]:` / `[Tool result]:`。其中**工具输出被截断到 2,000 字符**（`TOOL_OUTPUT_MAX_CHARS`），已剪枝的直接显示 `[Old tool result content cleared]`。

另一个重要细节是 `completedCompactions()`：它识别出历史上已完成的压缩产生的 user/assistant 消息对，**把它们从摘要输入里整体剔除**，只把**上一次的摘要文本**作为 `previousSummary` 传给 `buildPrompt`。所以 opencode 的长会话是**摘要链式传递**——第 N 次摘要是基于"第 N−1 次摘要 + 这期间的新对话"。这个设计的固有风险是**误差累积**：早期的关键前提每经过一次摘要就衰减一次。

#### 剪枝（`prune()`，默认关闭）

```
PRUNE_MINIMUM = 20_000      // 可剪总量低于此值就不动手
PRUNE_PROTECT = 40_000      // 最近这么多 token 的工具输出受保护
PRUNE_PROTECTED_TOOLS = ["skill"]
```

倒序遍历消息：跳过最近 2 轮；遇到 summary 消息立即停止；遇到已剪枝的 part 立即停止（说明再往前都剪过了）。累计工具输出超过 `PRUNE_PROTECT` 之后的部分进入待剪列表。**只有待剪总量 > `PRUNE_MINIMUM` 才真正执行**——这是为了避免频繁小额剪枝反复击穿 prompt cache 前缀。

执行方式是给 tool part 打上 `state.time.compacted` 时间戳，渲染进上下文时替换为占位符；**原始输出仍然完整保存在存储里**。这是一个好设计：上下文瘦身与数据留存解耦，事后可追溯。

触发点在 `prompt.ts` 中以 `Effect.forkIn(scope)` 异步执行，不阻塞主循环。

#### 压缩后的行为

- 若 `auto=true` 且非 overflow 场景，注入一条**合成 user 消息**："Continue if you have next steps, or stop and ask for clarification if you are unsure how to proceed."，带 `metadata.compaction_continue` 标记；可被 `experimental.compaction.autocontinue` 插件钩子关闭。
- overflow 场景（请求体超出 provider 限制）会**回放最后一条真实 user 消息**，并把媒体附件降级为 `[Attached <mime>: <name>]` 文本占位。
- **opencode 不做压缩后的指令重注入**。对比 Claude Code：项目根 `CLAUDE.md` 与 auto memory 在压缩后**从磁盘重新注入**，`paths:` 作用域规则与嵌套 `CLAUDE.md` 则丢失直到再次触发。Codex CLI 存在同类问题并已被社区提为 issue（自动压缩后不重读 `AGENTS.md`）。

#### 可用的插件扩展点（这是我们定制的主要着力点）

| 钩子 | 能做什么 |
|---|---|
| `experimental.session.compacting` | 向压缩提示词**注入额外上下文**（`output.context`），或**整体替换压缩提示词**（`output.prompt`，此时 `context` 被忽略） |
| `experimental.chat.messages.transform` | 在序列化前改写送入摘要的消息数组 |
| `experimental.compaction.autocontinue` | 决定压缩后是否自动续跑 |
| `session.compacted` 事件 | 压缩完成后做后处理（如重注入指令、写记忆） |

### 3.4 L4 · 跨会话记忆

#### opencode：空白

源码级证据：`grep -rl memory packages/opencode/src/` 只命中 `plugin/xai.ts` 与 `cli/heap.ts`，与记忆无关。生态里已有第三方插件（`opencode-supermemory`）在填这个坑，**反证了需求真实存在且上游没做**。

#### Claude Code auto memory

- 存储：`~/.claude/projects/<project>/memory/`，`<project>` 由 git 仓库路径派生，**同仓库的所有 worktree 与子目录共享一个记忆目录**；机器本地，不跨机同步。
- 结构：`MEMORY.md` 作为索引 + 若干主题文件（`debugging.md`、`api-conventions.md`…）。
- **加载策略是这个设计的核心**：每次会话只加载 `MEMORY.md` 的**前 200 行或前 25KB，以先到者为准**；主题文件不预加载，模型按需用普通文件工具读。超限后写入仍成功，但会返回错误提示模型重写索引（因为超出部分下次加载会被丢弃）。frontmatter 与块级 HTML 注释在计量前剥离。
- 元数据：写入时自动记录 `modified` ISO 8601 时间戳，**让模型自己判断这条记忆有多旧**。
- 隔离：主会话的 auto memory **不进入子智能体**；子智能体可有自己独立的记忆目录。
- 控制：`autoMemoryEnabled` / `CLAUDE_CODE_DISABLE_AUTO_MEMORY` / `autoMemoryDirectory`；`/memory` 可浏览编辑；界面显示 "Saved N memories" / "Recalled N memories"。
- 压缩后 auto memory **从磁盘重注入**。

> **最值得抄的三个设计**：①索引文件 + 主题文件的两级结构（把"每次都载"的量压到 200 行）；②写入时自动打时间戳；③超限时用错误反馈驱动模型自我整理。

#### MiMo Code（源码级，`packages/opencode/src/memory/`）

这是最贴近我们处境的参照——它就是 opencode 上加记忆。

**存储与寻址**（`paths.ts`）

```
<data>/memory/global/<key>.md
<data>/memory/projects/<project_id>/<key>.md      project_id = sha256(abs_repo_path)[:12]
<data>/memory/sessions/<session_id>/<key>.md
```

类型由 key 的命名约定推断：`memory` / `memory-*`（大小写不敏感，为兼容 `memory.md` → `MEMORY.md` 的历史改名）、`checkpoint` / `checkpoint-*`、`tasks/<id>/progress`、`tasks/<id>/notes`，其余为 `free`。`buildPath` 对调用方传入的 `scope_id` 与 `key` 做**路径穿越防护**（拒绝 `..` 段与绝对路径注入）。

**索引与检索**（`fts.sql.ts` / `service.ts` / `fts-query.ts`）

- SQLite：元数据表 `memory_fts`（`path` 唯一、`scope`、`scope_id`、`type`、`body`、`fingerprint`、`last_indexed_at`，按 `(scope, scope_id)` 与 `type` 建索引）+ FTS5 虚拟表 `memory_fts_idx`，`bm25()` 排序、`snippet()` 出摘要。
- **查询构造是这套设计里最有工程含量的部分**：用 `/[\p{L}\p{N}_]+/gu` 做 Unicode 分词（`\p{L}` 覆盖 CJK，注释里明确说明是为中文召回加的），每个 token 加短语引号规避 FTS5 语法字符，然后**用 OR 而非 AND 连接**。注释给了实测依据——AND 连接在 80 篇真实记忆的语料上"几乎所有多词查询返回 0 结果"，连 "permission deadlock" 这样的两词查询都归零。
- OR 连接带来的常见词噪音用**相对分数下限**处理：保留分数 ≥ 最高分 × `ratio`（默认 0.15）的结果，且**永远保留第 1 名**。用相对而非绝对阈值的理由也写在注释里——BM25 数值依赖语料规模，小语料下所有分数都趋近 0，固定阈值会误杀。检索时超额取 3 倍（上限 50）再过滤。
- 搜索前**惰性 reconcile**（`checkpoint.memory_reconcile_on_search`，默认开），用 `fingerprint` 把磁盘状态同步进索引 —— 这样人工直接编辑 md 文件也能被检索到。

**跨工具兼容**：开启 `memory.cc_index` 后会一并索引 `~/.claude/projects/<slug>/memory/**/*.md`，并从 frontmatter 的 `metadata.type` 判定类型——**直接读 Claude Code 的自动记忆**。

**写开关**（`write-gate.ts`）：`memory.disable_write` 只关写不关读；实现刻意用 `!== true` 判定，使配置写错时退化为"允许写"而不是静默失效。这个防御性细节值得学。

**投入分布**——MiMo Code `session/` 目录相对上游新增的文件，是一张诚实的成本地图：

| 子系统 | 新增文件 | 说明 |
|---|---|---|
| 检查点 | `checkpoint.ts` `-align` `-context` `-paths` `-progress-reconcile` `-retry` `-templates` `-validator`（**8 个**） | 最大投入 |
| 跨工具导入 | `claude-import` `codex-import` `opencode-import` `external-import` `external-import.sql`（5 个） | 会话/配置迁移 |
| 记忆 | `memory/` 下 6 个文件 | 反而是最小的一块 |
| 上下文调度 | `prune.ts`（独立成模块）`budgeted-read.ts` `boundary.ts` `trajectory.ts` `visibility.ts` | 读文件预算、边界、轨迹 |
| 自进化 | `auto-dream.ts` `goal.ts` `classify.ts` `skill-search-reminder.ts` | `/dream` `/distill` 的支撑 |

> **这条证据直接影响排期**：把"记忆"和"检查点/任务进度"当成一件事会严重低估工作量。记忆（存 + 检索）是可控的；检查点（状态对齐、进度校验、失败重试）才是投入大头。**建议先做记忆，检查点单独立项**。

#### Cursor

Cursor 在 2025 年中的 v1.0 引入项目级 Memories（自动生成、可在设置中审阅与删除、可让 AI 主动记住），其后与 Rules 体系合流。

> ⚠️ **事实存疑**：不同来源对 Cursor Memories 当前状态说法不一致——有来源称 2.1.x 起该特性被移除、建议导出转为 Rules；也有 2026-06 的来源称其演进为"编辑器与 CLI 共用一个记忆库"。`cursor.com` 在本次网络环境下不可达，未能核对一手文档。**引用 Cursor 现状前需自行验证**。本文只采信其**机制层面**的可靠部分：规则的四种加载模式（always / globs 自动附加 / description 驱动的模型自主拉取 / 手动 `@`）与项目级自动记忆的产品形态。

### 3.5 L5 · 检索层

| | 机制 | 成本 | 新鲜度 |
|---|---|---|---|
| **opencode** | ripgrep（`grep`/`glob`，尊重 `.gitignore`）+ LSP，实验性 `lsp` 工具暴露 `goToDefinition`/`findReferences`/`callHierarchy` 等；`explore`/`scout` 子智能体隔离大量读取 | 零索引成本 | 实时 |
| **Cursor** | tree-sitter 构建 AST → 深度优先合并兄弟节点成 ~500 token 的语法完整块 → embedding → Turbopuffer 向量库；**Merkle 树增量**，约 10 分钟一次只重算哈希不同的分支；服务端不存明文源码，只存 embedding 与混淆元数据 | 索引 + 存储 + 同步 | 分钟级延迟 |
| **Claude Code** | 自主探索 + 子智能体隔离 + tool search（工具多时 schema 按需拉取） | 零索引成本 | 实时 |
| **MiMo Code** | 继承 opencode + 记忆的 BM25 全文检索 | 极低 | 惰性 reconcile |

> **判断**：代码库检索上，"Agent 自主探索 + LSP"已经是 CLI 形态的主流选择，向量索引的边际收益在有 LSP 的强类型仓库上并不明显，且要付出索引基础设施与新鲜度的代价。**对我们的建议是：记忆层先上 SQLite FTS5/BM25（低成本、可解释、可审计），代码库检索维持现状，不要用"做记忆"的名义顺手上向量库。**

### 3.6 L6 · 可见性与控制

| 能力 | Claude Code | opencode |
|---|---|---|
| 上下文构成明细 | `/context` 按类别列出占用，含加载了哪些 CLAUDE.md 与记忆文件，并给优化建议 | **无等价物** |
| 记忆浏览编辑 | `/memory` | **无** |
| 指令加载调试 | `InstructionsLoaded` hook，可记录加载了哪些文件、何时、为何 | **无**（仅事件总线） |
| 内置会话命令 | `/compact <focus>` 带指示压缩、`/clear`、`/rewind` | `/compact`、`/summarize`、`/clear`、`/new`、`/export`、`/undo`、`/redo` |
| 压缩指示 | ✅ `/compact focus on the auth bug` | ❌ 不接受指示 |

> **判断**：L6 最容易被排期砍掉，但**记忆一旦不可见就不可维护**——开发者无法判断某个错误结论是不是被固化了，也就无法信任这套系统。`/context` 类能力应与记忆能力**同期交付**，不能推到下一期。

## 4. opencode 差异点清单

这是本报告的核心交付物。每条给出实现原理与建议实现层级（层级定义见 [ai-coding-solution-0001](../solutions/2026-08-11-opencode-enterprise-customization-roadmap.md) §3.2：L1 配置 / L2 插件 / L3 旁路服务 / L4 fork 补丁）。

| # | 差异点 | opencode 现状 | 对标做法 | 实现原理 | 价值 | 难度 | 层 |
|---|---|---|---|---|---|---|---|
| M1 | **压缩触发过晚** | 打满才压缩 | Claude `/autocompact 500k`；Codex ≈83% | 调大 `compaction.reserved` 即可前移触发点；要做成"按百分比"需改 `overflow.ts` | ★★★ | 极低 | L1（进阶 L4） |
| M2 | **剪枝默认关闭** | `compaction.prune` 默认 false | Claude 的 tool result 清理默认参与 | 开启即可；`PRUNE_MINIMUM`/`PRUNE_PROTECT` 为常量，如需调需补丁 | ★★★ | 极低 | L1 |
| M3 | **压缩后不重注入指令** | 摘要之后 AGENTS.md 不回来 | Claude 从磁盘重注入项目根 CLAUDE.md 与记忆 | 监听 `session.compacted` 或在 `session.compacting` 钩子把指令写进 `output.context` | ★★★ | 低 | L2 |
| M4 | **压缩后技能正文丢失** | 不重注入（但剪枝时受保护） | Claude 按 5k/技能、25k 总量重注入 | 同 M3，在钩子里带上本次已加载技能清单 | ★★ | 低 | L2 |
| M5 | **无跨会话记忆** | 完全没有 | Claude auto memory；MiMo `memory/` | 自定义 `memory` 工具（读/写/搜）+ 磁盘 md + SQLite FTS5；会话启动时注入索引文件 | ★★★ | 中 | L2 |
| M6 | **无记忆检索** | — | MiMo：FTS5 + BM25 + OR 分词 + 相对分数下限 | 见 §3.4；CJK 分词用 `\p{L}`，OR 连接 + 相对下限是已验证的正确解 | ★★★ | 中 | L2 |
| M7 | **无记忆的加载预算** | — | Claude：索引文件前 200 行/25KB，主题文件按需 | 两级结构：`MEMORY.md` 索引常驻 + 主题文件靠工具按需读 | ★★★ | 低（随 M5） | L2 |
| M8 | **记忆无时效标记** | — | Claude 写入时打 `modified` 时间戳 | 写工具自动写 frontmatter；让模型自行判断陈旧度 | ★★ | 极低 | L2 |
| M9 | **无路径作用域规则** | 只有嵌套 AGENTS.md 懒加载 | Claude `paths:` frontmatter；Cursor `globs` | 在 `tool.execute.after` 拦 `read`，按 glob 匹配后追加规则文本 | ★★ | 中 | L2 |
| M10 | **远程指令静默失败** | 拉取失败降级为空串 | — | 插件层自建拉取 + 本地缓存 + 失败告警；或改用托管配置文件落盘 | ★★ | 低 | L2/L3 |
| M11 | **无上下文可见性** | 无 `/context` | Claude `/context` 分类明细 | 自定义 command + 读 `/session/:id/message` 统计各来源 token | ★★★ | 中 | L2/L3 |
| M12 | **无记忆审计入口** | — | Claude `/memory` | 自定义 command 列出记忆文件并可打开编辑 | ★★ | 低（随 M5） | L2 |
| M13 | **压缩不接受指示** | `/compact` 无参数 | Claude `/compact <focus>` | 自定义 command 把用户指示塞进 `session.compacting` 的 `output.prompt` | ★★ | 低 | L2 |
| M14 | **摘要链式误差累积** | 只传上一次 summary | — | 在 `output.context` 里固定注入"不可丢失事实"清单（任务目标、关键约束、已确认结论） | ★★★ | 低 | L2 |
| M15 | **无读取预算控制** | 大文件整读进上下文 | MiMo `budgeted-read.ts` | `tool.execute.before` 对 `read` 注入行数上限；或 after 截断并提示 | ★★ | 中 | L2 |
| M16 | **无检查点/任务进度** | 有 todo，无持久进度 | MiMo 8 个 checkpoint 文件；Claude 会话恢复 | 记忆的 `tasks/<id>/progress` 类型 + 会话边界写入 | ★★ | **高** | L2+L3 |
| M17 | **子智能体不共享记忆** | 无记忆可谈 | Claude：主会话记忆不入子智能体，子智能体可有独立记忆 | 设计决策而非缺陷；做记忆时需显式决定注入范围 | — | — | 设计项 |

## 5. 优先级建议

按"价值 ÷ 成本"排，给三档。**这不是排期表，是排期的输入。**

### 第一档 · 地基（建议 2–3 周内全部拿下）

`M1` `M2` `M3` `M14` —— 四项加起来的改动量很小（一个配置 + 一个插件），但直接改善的是**每一次长会话的质量**，且完全不依赖记忆系统是否建成。

特别提示 `M14`：在压缩钩子里固定注入一份"不可丢失事实"清单（当前任务目标、关键技术约束、已确认的结论与否决项），是对抗摘要链式衰减最便宜的手段，成本大约是几十行插件代码。

### 第二档 · 高杠杆（建议作为第一个正式迭代）

`M5` + `M6` + `M7` + `M8` + `M12` 打包成**记忆最小闭环**：磁盘 md 文件 + SQLite FTS5 索引 + 两级加载（索引常驻/主题按需）+ 时间戳 + 审计命令。

并行做 `M11`（上下文可见性）——**它必须和记忆同期上线**，否则记忆一旦出错没人能诊断。

三条实现上的强建议，全部来自 MiMo Code 的实测教训：

1. **分词用 OR 不用 AND**，并配相对分数下限（top × 0.15）。AND 在真实语料上几乎必然归零。
2. **Unicode 分词必须覆盖 CJK**（`\p{L}`），否则中文记忆召回为零。
3. **搜索前惰性 reconcile**，让人工直接编辑记忆文件也能生效——这决定了这套系统是"黑盒"还是"可维护"。

### 第三档 · 观望或单独立项

- `M9` `M15`：价值中等、实现要碰工具拦截，等前两档跑稳再说。
- `M16` 检查点：**单独立项**。MiMo Code 在这一块投入了 8 个源文件（对齐、校验、进度 reconcile、重试、模板），远超记忆本身。不要打包进记忆迭代。
- `M4` `M10` `M13`：机会性补齐，单项都在 1 周以内。

### 与上游的撞车判断

opencode 已有的、**不要重写**的东西：压缩框架、`experimental.session.compacting` 钩子、prune 机制（含技能保护与 `PRUNE_MINIMUM` 的缓存友好设计）、嵌套指令懒加载、剪枝后的原始输出留存。上游实验开关中与本专题相关的有 `OPENCODE_EXPERIMENTAL_EVENT_SYSTEM`（新事件系统，可能影响插件订阅方式）——**做插件时要预留事件层适配**。

## 6. 风险与反模式

| 风险 | 说明 | 对策 |
|---|---|---|
| **记忆污染** | 模型把一个错误结论写进记忆，此后每次会话都注入，错误被不断强化 | 时间戳 + `/memory` 审计 + 让记忆可被显式否决；重要记忆需人工确认后落盘 |
| **破坏 prompt cache** | 记忆内容变化会改动请求前缀，击穿缓存推高成本 | 只在**会话启动**注入记忆，会话中途的写入不回灌当前上下文；对齐 opencode 的 `PRUNE_MINIMUM` 思路，避免高频小改动 |
| **压缩阈值调得过早** | 触发更频繁 → 摘要调用次数上升 → 成本上升 | 用 `reserved` 小步前移并度量，别一次调到 70% |
| **记忆里混入敏感信息** | 自动写入可能把密钥、客户数据固化到磁盘 | 写入路径过正则/熵值扫描；`disable_write` 开关按仓库敏感级下发 |
| **把记忆和检查点当一件事** | 严重低估工作量（见 §3.4 投入分布） | 拆成两个迭代 |
| **先上向量库** | 索引基础设施与新鲜度成本高，而记忆语料量小、BM25 已足够 | 记忆层先做 FTS5；代码检索维持 ripgrep + LSP |
| **只做能力不做可见性** | 记忆不可见即不可维护，最终被开发者关掉 | `M11` `M12` 与记忆同期交付 |

## 7. 待验证问题

| 问题 | 为什么重要 | 验证方式 | 状态 |
|---|---|---|---|
| `reserved` 调到多少能兼顾质量与成本 | 决定 M1 的落地参数 | 在 3 个真实仓库上按 20k/40k/60k 三档跑长会话，度量摘要后任务成功率与总 token | 未开始 |
| 开启 prune 后是否显著影响 prompt cache 命中率 | 决定 M2 是否默认开 | 对比开关两态的 `cache.read` 占比 | 未开始 |
| `experimental.session.compacting` 钩子在多子智能体并发下是否稳定 | M3/M14 全部依赖它 | 原型压测，覆盖嵌套子智能体与超长会话 | 未开始 |
| BM25 在我们中文为主的记忆语料上的实际召回 | 决定是否需要补向量检索 | 构造 100 条真实记忆 + 50 条查询做召回评测 | 未开始 |
| Cursor Memories 的当前形态 | 影响 L1/L4 的对标结论 | 直接核对 cursor.com 一手文档（本次网络不可达） | **阻塞** |
| 上游新事件系统是否改变插件订阅契约 | 影响所有 L2 实现的寿命 | 跟踪 `OPENCODE_EXPERIMENTAL_EVENT_SYSTEM` 相关提交 | 未开始 |

## 参考资料

1. opencode 源码（`anomalyco/opencode` @ `dev`，commit `d041eee`）：`packages/opencode/src/session/compaction.ts`、`overflow.ts`、`instruction.ts`（访问日期 2026-08-12）
2. [opencode 文档源码](https://github.com/anomalyco/opencode/tree/dev/packages/web/src/content/docs)（访问日期 2026-08-12）
3. MiMo-Code 源码（`XiaomiMiMo/MiMo-Code` @ `main`）：`packages/opencode/src/memory/{paths,service,fts-query,fts.sql,reconcile,write-gate}.ts`、`packages/opencode/src/session/`（访问日期 2026-08-12）
4. [How Claude remembers your project](https://code.claude.com/docs/en/memory)（访问日期 2026-08-12）
5. [Explore the context window](https://code.claude.com/docs/en/context-window)（访问日期 2026-08-12）
6. [Codex CLI is not rereading agents.md after auto /compact（openai/codex issue #5772）](https://github.com/openai/codex/issues/5772)（访问日期 2026-08-12）
7. [Securely indexing large codebases · Cursor](https://cursor.com/blog/secure-codebase-indexing)（经检索结果转述，站点在本次网络环境下不可直接访问，访问日期 2026-08-12）
8. [How Cursor Actually Indexes Your Codebase · Towards Data Science](https://towardsdatascience.com/how-cursor-actually-indexes-your-codebase/)（访问日期 2026-08-12）
9. [opencode ecosystem —— opencode-supermemory 插件](https://github.com/supermemoryai/opencode-supermemory)（访问日期 2026-08-12）
10. [ai-coding-insight-0001《CLI 形态 AI Coding 工具的技术路线与企业化差距》](2026-08-11-cli-coding-agent-landscape.md)
