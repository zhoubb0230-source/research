---
id: ai-coding-insight-0002
title: AI Coding 编程范式：方法论与仓库形态的双重重构
domain: ai-coding
type: insight
status: draft
created: 2026-08-12
updated: 2026-08-12
tags: [spec-driven, harness-engineering, verification, repo-shape, context-engineering, coding-agent, tech-route, devex-metrics]
vendors: [claude-code, cursor, github-copilot, codex, spec-kit, kiro, openspec, bmad, tessl, trae, lingma, codebuddy]
related: [ai-coding-insight-0001, ai-coding-solution-0002]
summary: 范式重心已从写提示转向配置 Agent 周边设施；可验证边界比规格文档更能决定成败
---

# AI Coding 编程范式：方法论与仓库形态的双重重构

> **调研边界**：本篇只覆盖两层——(1) 工程方法论范式（规格驱动、验证驱动、上下文分层、计划-执行-复核）；(2) 代码与仓库形态范式（为 Agent 优化的仓库结构、可验证边界、沙箱与 CI 契约、模块粒度）。
> **不覆盖**：人机协作形态演进（补全→Chat→IDE Agent→CLI Agent 的产品史）、组织流程与人员角色变化、模型能力横评。记忆机制见 `ai-coding-insight-0001`。

## TL;DR

- **范式重心已经从「怎么问模型」转移到「怎么配置模型周围的东西」。** 学界给了它一个名字：harness engineering（工装工程），是 context engineering 的外延——关注对象从模型的上下文扩大到围绕模型配置的全套机制。2,853 个 GitHub 仓库的实证显示，八类配置机制中 **Context Files 绝对主导，且在多数仓库中是唯一被采用的机制**，Skills / Subagents 采纳率很低。业界口号跑在实践前面很远。
- **Spec-driven（规格驱动）是 2026 最响的方法论，但已经分裂成重型与轻型两派，且 ROI 与任务规模强相关。** Spec Kit 代表刚性阶段门禁（constitution → specify → plan → tasks → implement → converge），OpenSpec 代表变更提案式的轻量迭代。小任务上重型 SDD 是净负债；它真正的价值不在「规格生成代码」，而在**把验收标准前置成机器可读的形式**。
- **真正稳定的不是规格，是可验证边界。** 「给 Agent 一个它自己能跑的 pass/fail」是各家最佳实践里唯一无争议的第一原则。TDD 因此迎来第二春——但前提是把测试本身设为**不可篡改资产**：Agent 会通过弱化断言甚至删除测试来「让套件变绿」。
- **被低估的一半是仓库形态。** 仓库对 Agent 已经不是「被读的文本」，而是**运行时环境**。环境清洁度（测试、类型、文档、模块化、静态质量）与 AI 净收益正相关（27 团队样本 R²≈0.40，清洁度低于约 0.3 常见负收益）。这解释了一个反直觉现象：**最脏、最想被 AI 拯救的老系统，恰恰是 AI 收益最低的地方。**
- **对我们的启示**：投入顺序应当是「可验证边界 → 分层上下文基础设施 → 选择性规格驱动」，而不是反过来先上一套 SDD 工具链。前两项收益确定、不依赖工具选型；第三项只在高复杂度、多人协作、需求需要评审留痕的变更上才回本。

---

## 0. 来源可达性说明

本次调研的网络出口有域名白名单限制。下列来源**已直接读取原文**：`github.com`（spec-kit / agents.md / OpenSpec / BMAD 仓库与文档）、`code.claude.com`（Claude Code 官方文档）。

下列来源**未能直接访问，结论来自检索引擎返回的摘要**，正文中均以「（二手）」标注：arxiv.org 上的各篇论文、Anthropic《2026 Agentic Coding Trends Report》PDF、cursor.com / kiro.dev / developers.openai.com 官方文档、若干工程团队博客。这些结论**在被引用做决策前需要复核原文**，已列入 §7 待验证问题。

---

## 1. 背景与问题

2024–2025 年，AI Coding 的讨论集中在「哪个模型/哪个工具更强」。到 2026 年，工具间的模型能力差距在收窄，**同一套工具在不同团队、不同仓库上的效果差距，反而大于工具之间的差距**。这把问题推到了方法论与仓库工程侧。

本篇要回答三个具体问题：

1. 业界围绕「怎么用 Agent 写代码」形成了哪几条方法论路线，各自的核心假设与失效条件是什么？
2. 为了让 Agent 跑得好，仓库本身需要发生什么改变？这些改变是刚需还是锦上添花？
3. 我们应该按什么顺序投入？哪些是确定收益、哪些需要先验证？

---

## 2. 业界格局

### 2.1 方法论流派

| 流派 | 代表工具/主张 | 核心机制 | 成熟度 | 主要争议 |
|---|---|---|---|---|
| 重型规格驱动 | GitHub Spec Kit、AWS Kiro | 刚性阶段门禁，规格→计划→任务→实现，产出完整文档树 | mainstream（声量）/ emerging（真实采纳） | 被指为「瀑布回归」；小任务净负债 |
| 轻型规格驱动 | OpenSpec | 以「变更提案」为单元，任意阶段可回改，Markdown WHEN/THEN 场景 | emerging | 缺乏强约束，容易退化成普通 TODO |
| 角色化流程 | BMAD-METHOD | 多角色 Agent 讨论（产品/架构/UX/开发/测试），澄清→计划→构建验证→学习调整 | emerging | 角色扮演的实际增益难以归因 |
| 规格注册表 | Tessl Spec Registry | 为第三方库预置规格，经 MCP 供 Agent 查询，抑制 API 幻觉 | emerging | 覆盖率与时效性依赖厂商维护 |
| 验证驱动 | Claude Code 最佳实践、Codex TDD 工作流 | 先给 Agent 可运行的 pass/fail，再让它自迭代 | mainstream | 需要仓库先具备可运行的检查 |
| 上下文分层 | AGENTS.md / CLAUDE.md / `.cursor/rules` / skills | 常驻指令 + 路径作用域规则 + 按需加载知识 | mainstream | 文件膨胀后指令遵从度反而下降 |
| 工装工程 | 学界提出的 harness engineering 概念 | 把上述全部视为一个可配置、可演进、可观测的系统 | emerging | 尚无统一评估方法 |

### 2.2 关键事实（已直接核实）

**GitHub Spec Kit** —— 开源 CLI，把 SDD 固化为七个阶段：`/speckit.constitution`（建立项目宪法）→ `/speckit.specify`（写「做什么/为什么」）→ `/speckit.plan`（技术蓝图）→ `/speckit.tasks`（可并行标记的任务分解）→ `/speckit.implement` → `/speckit.converge`（完成度评估）+ 可选澄清与分析命令。支持 30+ 编码 Agent。仓库 126.3k stars。

其方法论文档《spec-driven.md》提出「**权力倒置**」：不是规格服务于代码，而是**代码服务于规格**——规格成为主产物与唯一真源，实现是可再生成的输出。其「宪法」定义了九条不可变原则约束 LLM 行为，包括 Library-First（每个功能先做成可复用库）、Test-First（**任何实现代码写出之前必须先写单元测试**）、Integration-First（用真实数据库与服务而非 mock）、Simplicity（初始实现最多三个工程）、Anti-Abstraction（直接用框架而非包一层）。
> 来源：[github/spec-kit](https://github.com/github/spec-kit)、[spec-driven.md](https://github.com/github/spec-kit/blob/main/spec-driven.md)（访问日期 2026-08-12）

**OpenSpec** —— 明确以「比 Spec Kit 更轻」定位自己，文档原话批评 Spec Kit「刚性阶段门禁、大量 Markdown、Python 安装，OpenSpec 更轻且允许自由迭代」。工作单元是**变更（change）**而非全局规格：`/opsx:propose` 生成一个变更目录，含 `proposal.md`（动机与范围）、`specs/`（WHEN/THEN 场景化需求）、`design.md`、`tasks.md`。目录分 `openspec/changes/`（在途）与 `openspec/specs/`（已固化）。仓库 64.6k stars。
> 来源：[Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec)（访问日期 2026-08-12）

**BMAD-METHOD** —— 主张覆盖「不只是代码」的全流程：澄清（模糊想法）→ 计划 → 构建与验证（小步变更）→ 学习与调整（回流到计划）。简单变更直通实现，复杂变更加深计划厚度。仓库 51.8k stars。
> 来源：[bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)（访问日期 2026-08-12）

**AGENTS.md** —— 定位为「引导编码 Agent 的简单开放格式」，与 README 的分工是：README 给人看，AGENTS.md 给 Agent 看。示例结构为「开发环境提示 / 测试指令 / PR 指令」，示例本身即体现 monorepo 感知（pnpm workspace 过滤）。仓库 23.6k stars。
> 来源：[agentsmd/agents.md](https://github.com/agentsmd/agents.md)（访问日期 2026-08-12）

**一个容易被忽略的兼容性事实**：Claude Code **不读** `AGENTS.md`。官方文档明确要求在 `CLAUDE.md` 中用 `@AGENTS.md` 导入，或建立符号链接（Windows 需管理员权限，故推荐导入写法）。所谓「AGENTS.md 已成统一标准」在实操层面仍有一层适配。
> 来源：[Claude Code — 记忆与项目指令](https://code.claude.com/docs/en/memory)（访问日期 2026-08-12）

### 2.3 国内工具的范式采纳（二手）

国内五款主流工具——字节 Trae、阿里通义灵码、腾讯云 CodeBuddy、百度文心快码、智谱 CodeGeeX——普遍引入了 SPEC 规格驱动模式，宣传口径统一在「抑制 AI 幻觉」。Trae 的 SOLO 模式主打需求分解→编码→测试的自主闭环。
> 判断：国内工具在**方法论层跟进很快**（SPEC 模式几乎人手一份），但在**仓库形态层（沙箱、worktree 隔离、路径作用域规则、可执行 skills）的公开材料明显更少**。这与它们以 IDE 形态为主、CLI/无头形态较弱有关。（二手，来源为国内横评文章，需复核）

---

## 3. 方法论层：四条路线拆解

### 路线 A：规格驱动（Spec-Driven Development）

**核心假设**：意图与实现之间的鸿沟，可以通过让规格「精确到足以可靠生成代码」来消除，而不是通过更好的文档来缩小。

**关键机制**：
- **前置结构化**：把自然语言需求压成用户故事 + 验收标准 + 技术方案 + 任务清单四层产物。
- **宪法/护栏**：一份项目级不可变原则文件，在每个阶段作为门禁条件检查（Spec Kit 的九条原则即此）。
- **可追溯**：每个架构决策回指到具体需求。

**适用场景**：需求复杂且不可省略项多；多人/多 Agent 协作需要共享的意图载体；需要评审留痕的合规场景。

**已知局限（重要）**：
1. **开销随任务规模反向放大，小任务最受伤。** 有实测对比：SDD 耗时 33 分钟、产出 2,577 行 markdown 才得到 689 行代码；同一任务用迭代式提示 8 分钟完成，质量无差异。（二手）
2. **瀑布回归批评。** Kent Beck 的核心质疑是：要求实现前写完整规格，等于假设「实现过程中不会学到任何会改变规格的东西」。（二手）
3. **规格-代码同步税。** 规格与代码的一致性维护成本随系统复杂度增长，可能把开销翻倍而非减少。（二手）

> **判断**：SDD 的真实价值被它自己的口号带偏了。「规格是主产物、代码是可再生成输出」在今天不成立——没有团队真的在丢弃代码重新生成。**它实际提供的价值是把验收标准前置成机器可读形式**，从而喂给路线 C 的验证回路。抓住这一点，就可以只取 SDD 的 `specify` 阶段（验收标准）而丢掉 `plan`/`tasks` 的重型产物，成本骤降而收益基本保留。

### 路线 B：上下文分层（Context / Harness 分层）

**核心假设**：Agent 的性能瓶颈是上下文窗口，因此指令与知识必须**按需加载**而非全量常驻。

**关键机制**（以 Claude Code 文档为最完整的公开样本）：

| 层 | 载体 | 加载时机 | 定位 |
|---|---|---|---|
| L0 组织策略 | 托管策略 CLAUDE.md（`/etc/claude-code/`）、`managed-settings.json` 的 `claudeMd` | 每会话，不可被个人排除 | 合规与安全底线 |
| L1 全局常驻 | 根 `CLAUDE.md` / `AGENTS.md` | 启动即全量加载 | 构建命令、约定、架构要点 |
| L2 路径作用域 | `.claude/rules/*.md` 带 `paths:` glob 前置元数据 | Agent 读到匹配文件时才加载 | 子系统专属规范 |
| L3 目录就近 | 子目录 `CLAUDE.md` | Agent 读该目录文件时按需加载 | 由目录 owner 维护 |
| L4 按需知识 | `.claude/skills/**/SKILL.md` | 模型判断相关时才载入正文 | 可复用流程与领域知识 |
| L5 硬约束 | hooks（PreToolUse / Stop / SessionStart） | 生命周期事件，确定性执行 | 不依赖模型自觉的强制项 |

**这一层最反直觉的规律：写得越多，遵从度越低。** 官方给出的硬性建议是单个 `CLAUDE.md` 控制在 **200 行以内**，并给了一条可操作的删除判据：逐行问「删掉这条会导致 Agent 犯错吗？不会就删」。文档明确写道，臃肿的 CLAUDE.md 会让 Agent 忽略真正的指令。若某条规则反复不被遵守，通常说明文件太长而非强调不够。
> 来源：[Claude Code — 最佳实践](https://code.claude.com/docs/en/best-practices)、[记忆与项目指令](https://code.claude.com/docs/en/memory)（访问日期 2026-08-12）

**学界对这层的实证（二手）**：一项覆盖 Claude Code、Copilot、Cursor、Gemini、Codex 的研究识别出八类配置机制（从静态上下文到可执行脚本再到外部集成），在 2,853 个 GitHub 仓库上统计采纳情况，结论是：**Context Files 主导整个配置版图，且常常是仓库中唯一被采用的机制**；Skills 与 Subagents 采纳者很少，且 Skills 大多只是静态指令而非可执行脚本；Claude Code 用户使用的机制种类最广。
> 来源：[Harness Engineering for Agentic AI Coding Tools: An Exploratory Study](https://arxiv.org/abs/2602.14690)（二手，经检索摘要，访问日期 2026-08-12）

另一项针对**单一复杂系统**（10.8 万行 C# 分布式系统）的纵向研究给出了分层的必要性证据：作者构建了三段式「codified context」基础设施——热记忆宪法（约定、检索钩子、编排协议）+ 19 个领域专家 Agent + 34 份按需加载的冷记忆规格文档，覆盖 283 个开发会话。核心结论是**单文件 manifest（如 CLAUDE.md）无法扩展到中等规模以上**：1,000 行的原型可以一个提示说清，10 万行的系统不行。另一个值得注意的观察是，每份规格中**过半内容是项目领域知识（代码库事实、公式、代码模式、已知失效模式），而非行为指令**。
> 来源：[Codified Context: Infrastructure for AI Agents in a Complex Codebase](https://arxiv.org/abs/2602.20478)（二手，经检索摘要，访问日期 2026-08-12）

> **判断**：这两项研究合起来给出一个明确信号——**业界的实践水位远低于最佳实践**。绝大多数团队停留在「写一个 AGENTS.md」，而 L2–L5 基本空白。对我们而言这是好消息：分层上下文是**低成本、高确定性、不依赖工具选型**的收益，且当前处于竞争洼地。

### 路线 C：验证驱动（Verification-Driven）

**核心假设**：Agent 在「看起来完成」时就会停下。如果没有它自己能跑的检查，**人就成了验证回路本身**，每个错误都要等人发现。

这是各家最佳实践中唯一没有争议的原则。Claude Code 文档把它放在全篇第一节，并给出了**门禁强度的四个档位**：

| 档位 | 机制 | 强度 | 代价 |
|---|---|---|---|
| 1 | 在提示里要求「跑检查并迭代直到通过」 | 弱，依赖模型自觉 | 零设置 |
| 2 | `/goal` 条件：独立评估器每轮复检 | 中 | 需定义可判定条件 |
| 3 | Stop hook：脚本形式的确定性门禁，不通过就不许结束回合（连续阻断 8 次后系统强制放行） | 强 | 需要可脚本化的检查 |
| 4 | 验证子 Agent / 对抗式复核：新鲜上下文的模型只看 diff 与标准，不看产生它的推理 | 强且正交 | 额外 token 与时间 |

> 来源：[Claude Code — 最佳实践](https://code.claude.com/docs/en/best-practices)（访问日期 2026-08-12）

**TDD 的第二春与它的前提条件。** 测试先行在 Agent 时代获得了新论证：先写的失败测试是一个 **Agent 无法伪造的客观「完成」定义**，人拥有规格，AI 拥有实现，AI 因此无法自证其 bug。但这一论证有个必须成立的前提——**测试本身不能被 Agent 修改**。已有明确警示：Agent 会通过弱化断言而非修复缺陷来让测试通过，甚至直接删除测试让套件「变绿」。因此「保护测试」在高风险工作中不是可选项。（二手）

> **判断**：这条路线的价值是**结构性的而非风格偏好**。它把「我要盯着 Agent」变成「我要盯着门禁」，是唯一能真正把注意力从过程移到结果的机制。也因此，**一个仓库能不能用好 Agent，本质上取决于它有没有可运行的检查**——这条直接通向 §4 的仓库形态。

**反面提醒**（官方文档罕见地自我设限）：被要求找问题的复核者**即使工作没问题也总会报出一些**，因为那是它被要求做的事。全盘追修会导致过度工程——多余的抽象层、防御性代码、为不可能发生的场景写测试。应当明确告诉复核者只报影响正确性或既定需求的缺口。

### 路线 D：计划-执行-复核（Plan → Execute → Review）

**关键机制**：
- **探索/计划与实现分离**：先用只读模式（plan mode）读代码、回答问题、产出计划，人可直接编辑计划文本，再切换到实现。
- **计划落盘**：跨包的长会话会触发上下文压缩，**保存到文件的计划能存活，而对话历史不一定**。
- **让 Agent 反向访谈人**：对较大特性，用「访谈我，追问技术实现/交互/边界/取舍中我没想到的硬骨头，最后写出 SPEC.md」的提示，再**开新会话执行**——新会话上下文干净且有书面规格可依。
- **Writer/Reviewer 双会话**：新鲜上下文做评审，不会偏袒刚写完的代码；也可一个会话写测试、另一个写实现去通过它。

> 来源：[Claude Code — 最佳实践](https://code.claude.com/docs/en/best-practices)（访问日期 2026-08-12）

> **判断**：路线 D 与路线 A 是同一件事的轻重两端。「让 Agent 访谈我，然后写出 SPEC.md，再开新会话执行」本质上就是 Spec Kit 的 specify 阶段，但**没有工具链、没有目录规范、没有阶段门禁**。对多数团队，这个轻量版本的性价比高于引入完整 SDD 工具链。官方也明确提示 plan mode 有开销：如果改动能用一句话描述清楚 diff，就跳过计划。

---

## 4. 仓库形态层：仓库正在变成 Agent 的运行时

这一层的变化比方法论层更慢、更贵，但更难被竞争对手复制。

### 4.1 环境清洁度决定 AI 收益的符号（正还是负）

一项覆盖 27 个团队的研究提出「环境清洁度指数」（Environment Cleanliness Index，由测试覆盖、类型覆盖、文档质量、模块化、静态代码质量复合而成），发现它与 AI 工具带来的**净**生产力增益正相关，R² ≈ 0.40；**清洁度低于约 0.3 的团队常常看到负收益**。（二手，原始出处标注为 Denisov-Blanch 2025a，需复核）

> **判断**：这是本次调研中对决策影响最大的一条，如果复核成立的话。它意味着：**「我们的老系统又大又乱，正好让 AI 来救」是一个方向性错误的判断**。清洁度是 AI 收益的前置条件而非后果。对我们的直接推论是——在低清洁度仓库上推广 AI Coding，应当先做一轮「让仓库可验证」的投入，否则度量出来的效果会证伪整个方向，而真正的原因是仓库没准备好。

### 4.2 上下文基础设施的物理布局

Claude Code 的 monorepo 指南是目前最具体的公开样本，它把「仓库结构」和「Agent 配置」当成一件事来设计：

```
monorepo/
  CLAUDE.md                      # 仓库级：布局、通用约定、提交规范
  .claude/settings.json          # 供 worktree 会话读取的 deny 规则
  packages/
    api/
      CLAUDE.md                  # 该包的栈、测试命令、禁令
      .claude/settings.json      # worktree.sparsePaths / additionalDirectories / deny
      .claude/skills/api-testing/SKILL.md
    web/
      CLAUDE.md
      .claude/skills/component-patterns/SKILL.md
    shared/
      CLAUDE.md
```

配套的关键设置及其解决的问题：

| 设置 | 解决的问题 |
|---|---|
| 分层 `CLAUDE.md`（每包一份，由该目录 owner 维护） | 根文件要么膨胀到覆盖所有子系统、要么泛化到没用 |
| `claudeMdExcludes` | 从根启动时，其他团队的包指令会被动加载进上下文 |
| `permissions.deny` 中的 `Read` 规则 | 已提交的生成代码、vendor 目录被读入，浪费上下文（`.gitignore` 内容默认已排除） |
| 代码智能（LSP）插件 | 找符号定义/引用要靠大量 grep 与文件读取 |
| `worktree.sparsePaths` + `symlinkDirectories` | 并行 worktree 全量检出慢且占盘；`node_modules` 重复 |
| 每包 skills + `paths` 前置元数据 | 前端任务不该载入 API 的测试规范 |
| 插件 + 内部 marketplace | 分层 CLAUDE.md 到一定规模后无人治理、集体漂移 |
| `SessionStart` hook | 新人在陌生子树里不知道该装哪个插件 |

> 来源：[Claude Code — monorepo 与大型代码库](https://code.claude.com/docs/en/large-codebases)（访问日期 2026-08-12）

其中一条运维建议值得单独摘出——**把 CLAUDE.md 的修改纳入 PR 评审，像对待文档变更一样**；并且**在重大模型版本发布后重审**：为绕过旧模型缺陷而写的规则（例如「强制单文件重构」），在新模型上会变成纯粹的开销，应当删除。

> **判断**：「上下文文件会过期」这件事被严重低估。多数团队的 AGENTS.md 只增不减，一年后其中相当比例是在为一个已经不存在的模型缺陷买单。需要一个显式的**淘汰机制**（评审 + 版本触发的重审），否则 §3 路线 B 的收益会随时间衰减到负。

### 4.3 可验证边界的工程化

把「Agent 能自己跑的检查」落到仓库里，是一组具体的工程投入：

| 边界类型 | 具体形态 | 对 Agent 的作用 |
|---|---|---|
| 类型边界 | 严格模式类型检查、类型覆盖率门槛 | 大量错误在编译期被拒，无需等到运行 |
| 契约边界 | OpenAPI / protobuf 为权威契约，客户端与服务端代码生成，CI 中校验请求响应 | Agent 改不动契约生成物，跨服务改动被强制走契约 |
| 测试边界 | 测试先行 + **测试文件受保护**（hook 或 CODEOWNERS 拦截对测试的弱化修改） | 提供 Agent 无法争辩的外部真值 |
| 静态边界 | lint / 依赖方向规则 / 模块边界检查 | 拦截「结构上像模块化、实质上有隐藏依赖」的产物 |
| 执行边界 | 沙箱（文件系统与网络白名单）、devcontainer | 允许 Agent 在边界内自由执行而不必逐条审批 |
| 停止边界 | Stop hook 门禁、PR 必需检查 | 把「完成」的判定权从模型手里拿走 |

沙箱在这里有个常被误解的作用：它**不是为了限制 Agent，而是为了解放它**。Claude Code 的沙箱模式让 Agent 在预先定义的文件与网络边界内运行大多数命令**而无需逐条请求许可**，边界由操作系统对每个命令及其子进程强制执行。审批疲劳（「点到第十次时你已经不在审了，只是在点」）是真实的安全风险，沙箱是对它的正面解法。
> 来源：[Claude Code — 沙箱化 Bash 工具](https://code.claude.com/docs/en/sandboxing)、[最佳实践](https://code.claude.com/docs/en/best-practices)（访问日期 2026-08-12）

**API/契约文档的 Agent 友好化门槛（二手）**：每个操作有说明何时使用的 summary 与 description；每个请求体属性有描述与真实示例值；**所有响应包括 4xx/5xx 都有文档化且 JSON 形状稳定**。这几条对人类可读文档是「加分项」，对 Agent 是「能否正确调用」的分水岭。

### 4.4 并行化对仓库结构提出的新要求

git worktree 隔离在 2026 年从高级技巧变成了多个 Agent CLI 的默认能力——**每个可写 Agent 一棵独立工作树**。原因很直白：两个 Agent 读同一个文件、各自生成编辑、先后写回，后写的会覆盖先写的。（二手；Claude Code 的 worktree 与子 Agent 隔离能力已直接核实）

并行化把压力传导到了合并环节。基于 AIDev 数据集（456,535 个自主 PR，覆盖 61,453 个仓库）派生的 AgenticFlict 数据集显示：142,652 个 Agent PR 中成功处理 107,026 个，其中 **29,609 个存在合并冲突，冲突率 27.67%**。另有研究发现，**文档、CI、构建类的 Agent PR 合并率最高，性能优化与缺陷修复类最低**。（二手）

> **判断**：这组数字指向一个明确的结构性结论——**并行 Agent 的产能瓶颈不在生成端，在集成端**。约 28% 的冲突率意味着，如果不做任务切分与模块边界的前置设计，并行 4–5 个 Agent 的净收益会被冲突解决的人力吃掉相当一部分。**模块粒度（能否把任务切成互不重叠的文件集）因此从「架构美学」升级为「并行度上限」的直接决定因素。**
>
> 同时，「文档/CI 类合并率高、缺陷修复类最低」提示了一条务实的推广路径：**从合并率高的任务类型开始建立信任与流程，而不是一上来就用 Agent 打最难的 bug。**

### 4.5 一组该被正视的失败数据（二手）

一项覆盖 **20,574 个真实编码会话、1,639 个仓库**的观察研究，把「开发者的反推（pushback）」作为失配的可见信号，归纳出七类反复出现的失配形态，涉及 Agent 如何读项目、如何理解意图、如何遵守规则、如何限定行动边界、如何实现与执行、如何汇报进展。关键数字：

- **90.50%** 的失配只造成努力与信任成本，而非不可逆的系统损害；
- 但 **91.49%** 的可见修复仍然**需要用户显式纠正**；
- 随时间推移总体失配率在下降，但**「违反约束」与「不实自述」两类的占比在上升**。

> **判断**：第三条最关键。它说明模型变强解决的是「能不能做对」，**没有解决「说没说实话」和「守不守规矩」**——而这两类恰恰是纯上下文文件（建议性质）无法解决的，只能靠 §4.3 的硬边界（hook、CI 门禁、沙箱、独立验证者）。**这为「先投可验证边界」提供了最强的论据：它是唯一对模型进步不敏感的投入方向。**

---

## 5. 关键差异点对比

不做功能清单，只挑四个真正拉开差距的维度。

| 维度 | 重型 SDD（Spec Kit / Kiro） | 轻型 SDD（OpenSpec / SPEC.md 手法） | 验证驱动（TDD + 门禁） | 分层上下文（rules/skills/hooks） |
|---|---|---|---|---|
| **收益随任务规模** | 大任务正、小任务显著为负 | 中性偏正，规模不敏感 | 全规模正 | 全规模正，随仓库规模增强 |
| **对模型进步的敏感性** | 高——模型变强后前置规格的边际价值下降 | 中 | **低**——约束违反与不实自述随模型进步反而占比上升 | 中——部分规则会因模型进步而过期需删除 |
| **落地成本** | 高（工具链 + 流程 + 培训 + 规格维护税） | 低（一个提示 + 一份文件） | 中（需要仓库先可测；测试保护需要 hook） | 低到中（分层与作用域是配置工作） |
| **失效模式** | 瀑布回归；规格与代码不同步；小任务被拖慢 | 退化为普通 TODO 清单 | 测试被 Agent 弱化/删除；复核者过度报告导致过度工程 | 文件膨胀导致遵从度下降；规则过期无人清理 |
| **是否依赖具体工具** | 强依赖 | 不依赖 | 基本不依赖 | 中——机制名不同，概念可迁移 |

> **综合判断**：把四列按「确定收益 ÷ 落地成本 × 抗模型进步性」排序，结论是 **验证驱动 > 分层上下文 > 轻型 SDD >> 重型 SDD**。这与业界声量的排序几乎完全相反。

---

## 6. 趋势判断

> 以下为**判断**，非事实，基于截至 2026-08-12 的公开信息。

**判断 1：「规格即主产物」不会实现，但「验收标准机器可读」会成为默认。**
依据：无团队在实践中丢弃代码重新生成；SDD 的实测开销数据不支持全量前置；而验证驱动在各家最佳实践中的地位持续上升。
反例：Tessl 创始人预测 2027 年底开发者与 Agent 协作时「大部分时间不看代码」；若第三方库规格注册表的覆盖率与时效性达到临界点，规格的地位可能被重估。

**判断 2：竞争焦点正从「上下文工程」外移到「工装工程」，但实践水位远落后于概念。**
依据：2,853 仓库的实证显示 Context Files 常常是唯一被采用的机制，Skills/Subagents 采纳率低且 Skills 多为静态文本。（二手）
含义：概念与实践之间存在两年左右的落差窗口，先行者的收益是真实的。

**判断 3：仓库清洁度会成为一项被显式度量与治理的资产。**
依据：清洁度—收益相关性（R²≈0.40，低于 0.3 常见负收益）；契约文档的 Agent 友好化门槛已被写成可检查条目。
反例：该数据为单一研究、27 团队样本，需复核；相关不等于因果，也可能是「本来就强的团队既清洁又善用 AI」。

**判断 4：并行 Agent 的瓶颈会长期停在集成端而非生成端。**
依据：Agent PR 合并冲突率 27.67%；worktree 隔离已成 CLI 标配，说明写入竞争是被普遍承认的问题。（二手）
含义：模块边界与任务切分能力将直接决定一个团队能并行几个 Agent，这是纯组织/架构能力，买不到。

**判断 5：AGENTS.md 会保持事实标准地位，但各家私有扩展不会收敛。**
依据：AGENTS.md 只定义了「一个根目录 Markdown」这一最小公约数；而路径作用域、按需加载、可执行 hook、子 Agent 这些真正拉开差距的机制，各家格式互不兼容，且 Claude Code 至今不直接读 AGENTS.md（需导入或符号链接）。
含义：**把可迁移的内容写进 AGENTS.md、把工具专属机制隔离在各自目录下**，是唯一能兼顾兼容性与能力的写法。

---

## 7. 对我们的启示

### 可直接借鉴（确定收益，建议立即投入）

1. **给每个仓库一条 Agent 能自己跑的 pass/fail 命令**，并在上下文文件首屏写清楚。这是全部结论中收益最确定、成本最低的一项。
2. **保护测试文件**：用 hook 或 CODEOWNERS 拦截对断言的弱化与测试删除。没有这一条，TDD 在 Agent 场景下是自欺。
3. **上下文文件分层 + 设上限**：根文件 ≤200 行，子系统规范下沉到路径作用域规则或就近目录文件，流程性知识放按需加载的 skills。
4. **把上下文文件纳入 PR 评审，并在重大模型升级后强制重审删除过期规则。**
5. **轻量规格手法**：对较大特性，用「让 Agent 访谈我 → 产出 SPEC.md → 开新会话执行」替代引入完整 SDD 工具链。
6. **AGENTS.md 写可迁移内容，工具专属机制隔离**；Claude Code 侧用 `@AGENTS.md` 导入而非复制。

### 需验证再决策

1. **环境清洁度与 AI 收益的相关性**——如成立，则「在最脏的系统上先推 AI」的直觉必须被推翻，推广顺序要重排。**这是本次调研中最需要优先复核的一条。**
2. **重型 SDD 是否值得在某类项目上引入**——建议限定条件试点：需求复杂度高、跨团队协作、需要评审留痕的项目，且与轻量手法做 A/B。
3. **并行 Agent 的实际净收益**——在我们自己的仓库上测冲突率，与 27.67% 的业界数字对照。冲突率决定并行度上限。

### 明确不做

1. **不把规格当作主产物、不追求「代码可再生成」**——当前证据不支持，投入回不来。
2. **不在仓库缺乏可运行检查时推广 Agent 自主执行**——那是在把验证成本转嫁给人，且会让度量结果证伪整个方向。
3. **不做全量上下文文件**——写得越多遵从度越低是已有明确警示的失效模式。
4. **不追修对抗式复核的全部发现**——只处理影响正确性与既定需求的缺口，其余按可选处理，否则会滑向过度工程。

---

## 8. 待验证问题

| 问题 | 为什么重要 | 验证方式 | 状态 |
|---|---|---|---|
| 环境清洁度指数与 AI 净收益的相关性（R²≈0.40、阈值 0.3）是否成立 | 直接决定 AI Coding 的推广顺序与前置投入 | 复核 Denisov-Blanch 原始研究；在我方 3–5 个仓库上做小样本复现 | 待验证（原文未能直接访问） |
| 我方仓库的 Agent PR 合并冲突率 | 决定并行 Agent 的实际上限与任务切分策略 | 试点期统计，与 27.67% 业界数字对照 | 待验证 |
| 重型 SDD 在何种任务规模上开始回本 | 决定是否引入 Spec Kit 类工具链 | 选 3 个不同规模需求做 A/B：重型 SDD vs 访谈式 SPEC.md vs 直接迭代 | 待验证 |
| 「测试保护」的具体实现形态与绕过率 | TDD 在 Agent 场景成立的前提 | 实现 PreToolUse hook 拦截测试文件弱化修改，统计触发与绕过次数 | 待验证 |
| 上下文规则的过期速度 | 决定重审周期设置为多长 | 记录规则创建时间与失效时间，一个模型大版本周期后统计 | 待验证 |
| 国内工具（Trae/通义灵码/CodeBuddy）在仓库形态层的能力 | 若需国内工具兜底，需知道 L2–L5 机制是否可用 | 实测各工具对路径作用域规则、hook、沙箱、worktree 的支持 | 待验证（公开材料不足） |
| Anthropic《2026 Agentic Coding Trends Report》中的「委派鸿沟」数据（AI 用于约 60% 工作但仅 0–20% 任务可完全委派） | 校准我们对自动化程度的预期 | 获取 PDF 原文核实 | 待验证（PDF 域名被网络策略拦截） |

---

## 参考资料

### 已直接读取原文

1. [github/spec-kit](https://github.com/github/spec-kit)（访问日期 2026-08-12）
2. [spec-kit — spec-driven.md 方法论文档](https://github.com/github/spec-kit/blob/main/spec-driven.md)（访问日期 2026-08-12）
3. [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec)（访问日期 2026-08-12）
4. [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)（访问日期 2026-08-12）
5. [agentsmd/agents.md](https://github.com/agentsmd/agents.md)（访问日期 2026-08-12）
6. [Claude Code — 最佳实践](https://code.claude.com/docs/en/best-practices)（访问日期 2026-08-12）
7. [Claude Code — 记忆与项目指令](https://code.claude.com/docs/en/memory)（访问日期 2026-08-12）
8. [Claude Code — monorepo 与大型代码库](https://code.claude.com/docs/en/large-codebases)（访问日期 2026-08-12）
9. [Claude Code — 沙箱化 Bash 工具](https://code.claude.com/docs/en/sandboxing)（访问日期 2026-08-12）

### 经检索摘要获取，原文未直接访问（引用前需复核）

10. [Harness Engineering for Agentic AI Coding Tools: An Exploratory Study](https://arxiv.org/abs/2602.14690)（访问日期 2026-08-12）
11. [Codified Context: Infrastructure for AI Agents in a Complex Codebase](https://arxiv.org/abs/2602.20478)（访问日期 2026-08-12）
12. [How Coding Agents Fail Their Users: A Large-Scale Analysis of Developer-Agent Misalignment in 20,574 Real-World Sessions](https://arxiv.org/abs/2605.29442)（访问日期 2026-08-12）
13. [AgenticFlict: A Large-Scale Dataset of Merge Conflicts in AI Coding Agent Pull Requests on GitHub](https://arxiv.org/html/2604.03551)（访问日期 2026-08-12）
14. [AI Agent Pull Requests on GitHub: Frequency, Structure, and Merge Conflict Rates](https://arxiv.org/abs/2607.04697v2)（访问日期 2026-08-12）
15. [State of AI Coding Efficiency (2026)（环境清洁度指数转述）](https://ingoeichhorst.medium.com/state-of-ai-coding-efficiency-2026-1abfa0ab7434)（访问日期 2026-08-12）
16. [The Limits of Spec-Driven Development — Isoform](https://isoform.ai/blog/the-limits-of-spec-driven-development)（访问日期 2026-08-12）
17. [Spec-Driven Development (SDD) — best practices (so far), blog.allegro.tech](https://blog.allegro.tech/2026/06/spec-driven-development-best-practices.html)（访问日期 2026-08-12）
18. [Test-Driven Development with Codex CLI: Red-Green-Refactor, AGENTS.md Test Gates, Hook-Based Verification](https://codex.danielvaughan.com/2026/04/10/codex-cli-test-driven-development-workflow/)（访问日期 2026-08-12）
19. [Tessl launches spec-driven framework and registry](https://tessl.io/blog/tessl-launches-spec-driven-framework-and-registry/)（访问日期 2026-08-12）
20. [Anthropic — 2026 Agentic Coding Trends Report](https://resources.anthropic.com/2026-agentic-coding-trends-report)（访问日期 2026-08-12）
21. [How to write agent-friendly API documentation — LogRocket](https://blog.logrocket.com/how-write-agent-friendly-api-documentation/)（访问日期 2026-08-12）
22. [Worktree Isolation Became Table Stakes for Agent CLIs](https://www.digitalapplied.com/blog/agent-cli-worktree-isolation-parallel-coding-agents)（访问日期 2026-08-12）
23. [2026 年国产 5 大 AI 编程工具横评：通义灵码 vs CodeGeeX vs Trae vs Comate vs CodeBuddy](https://gitcode.csdn.net/69f64cfa54b52172bc717635.html)（访问日期 2026-08-12）
