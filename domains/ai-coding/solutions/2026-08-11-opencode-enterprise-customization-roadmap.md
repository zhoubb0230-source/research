---
id: ai-coding-solution-0001
title: 基于 opencode 的公司内 AI Coding 工具定制特性路线
domain: ai-coding
type: solution
status: draft
created: 2026-08-11
updated: 2026-08-11
tags: [cli-agent, coding-agent, architecture, selection, landing, enterprise-landing, guardrail, sandbox, observability, agent-skills, cost-optimization, audit]
vendors: [opencode, claude-code, codex, mimo-code]
related: [ai-coding-insight-0001, ai-coding-vendor-0001]
summary: 定制按四层分配，P0 补治理与接入、P1 补可观测与私有上下文，编排交给上游
---

# 基于 opencode 的公司内 AI Coding 工具定制特性路线

## TL;DR

- **目标**：让基于 opencode 的内部工具从"能用"走到"能在全公司合规铺开、并能度量收益"。
- **推荐方案**：按 **配置层 / 插件层 / 旁路服务层 / Fork 补丁层** 四层分配定制，硬性约束 **Fork 补丁面积 ≤ 10 个文件、≤ 2000 行**；目标 80% 以上的定制价值由前三层承载。
- **关键取舍**：不追 Agent 编排能力（上游在做，见 [ai-coding-insight-0001](../insights/2026-08-11-cli-coding-agent-landscape.md) §5），把资源压在**治理、可观测、私有上下文、流程闭环**四块——这四块上游要么不做，要么会做成付费 Enterprise 功能。
- **预估投入**：P0 约 2 人 × 2 个月；P1 约 3.5 人 × 3 个月；P2 视沙箱方案选型，4–6 人月起。
- **最容易被低估的两项**：`E1 版本与安装通道收敛`（不做它，后面所有强制策略都推不下去）和 `C2 组织级 AGENTS.md 强制注入`（不到 1 人周，价值极高）。

## 1. 背景与目标

### 1.1 问题陈述

公司已基于 opencode 封装内部 AI Coding 工具。opencode 本身在 Agent 内核、多 provider、MCP/LSP、权限模型、客户端/服务端分离上足够成熟，但在企业落地必需的几类能力上是空白（详见 [ai-coding-vendor-0001](../vendors/opencode.md) §5）：

- **无遥测导出**：不知道谁在用、用得怎么样、花了多少钱，无法做推广决策与成本管控。
- **无审计**：不满足合规对"AI 改了哪些代码、执行了哪些命令"的追溯要求。
- **强制策略薄弱**：远程配置优先级最低，用户可用 `--auto` 把权限放宽到"未显式拒绝即批准"；无 MCP / 插件 / hook 来源管控，无版本下限。
- **无 OS 级沙箱**：权限系统是策略层不是安全边界。
- **无技能分发机制**：公司的架构规范、脚手架、发布流程无法作为可执行知识下发。
- **私有上下文缺位**：内部文档、API 目录、历史缺陷、需求系统均未接入。

### 1.2 目标与非目标

| | 内容 |
|---|---|
| 目标 | ① 满足安全合规准入（数据不出网、可审计、可强制策略）；② 建立使用与效能度量；③ 把公司工程知识沉淀为 Agent 可执行的技能与规则；④ 打通研发流程闭环（评审、CI、工单）；⑤ 把 fork 维护成本控制在可持续区间 |
| 非目标 | ① 不追求超越 Claude Code / Codex 的通用编码能力；② 不自研 Agent 编排、TUI、桌面端、IDE 插件；③ 不自研模型路由与负载均衡（归 AI 网关团队）；④ 不自创技能 / 规则 / 工具格式 |

### 1.3 成功指标

| 指标 | 现状 | 目标 | 度量方式 |
|---|---|---|---|
| 版本收敛率（运行版本在批准范围内的比例） | 未知 | ≥ 95% | 遥测上报的 `app.version` |
| 覆盖到强制策略的开发机比例 | 未知 | ≥ 98% | 托管配置探针上报 |
| 会话级审计覆盖率 | 0 | 100% | 审计平台按 session 计数比对 |
| 周活跃使用人数 / 目标人群 | 未知 | ≥ 60% | 遥测 `session.count` 去重 |
| 单次任务平均 token 成本 | 未知 | 建立基线后季度下降 15% | 网关侧计费 + 遥测 |
| 公司技能库被调用次数 / 周 | 0 | 建立基线 | `skill` 工具调用事件 |

## 2. 约束与前提

- **上游节奏极快**：v1.18.7 → v1.18.16 集中在 2026-07-27 至 08-10（约两周十个版本）。任何内核改动都要按"每次 rebase 的冲突成本"折算。
- **上游无公开路线图**（issue #19206 被以 "not planned" 关闭），只能靠实验性开关与发布记录反推方向。
- **上游正在商业化**：仓库从 `sst/opencode` 迁到 `anomalyco/opencode`；Zen 网关与 Workspace 处于 beta 且定价待公布；Enterprise 版的卖点（集中配置 + SSO + 内部网关）与我们要自建的东西**直接重叠**。
- **许可证风险**：当前 MIT。需要保留版本冻结与 vendoring 能力以对冲许可证变更。
- **本方案成立的假设**：公司已有或将有统一 AI 网关（承担模型路由、鉴权、计费、限额）；公司已有日志/可观测平台（支持 OTLP 或可适配）；开发机可被 IT 统一管理（能落 `/etc/opencode/` 或等价机制）。

## 3. 方案选型

### 3.1 整体路线选型

| 候选方案 | 优势 | 劣势 | 成本 | 风险 | 结论 |
|---|---|---|---|---|---|
| A. 保持 opencode fork + 分层定制 | 复用成熟内核；服务端/OpenAPI 可直接承载自建接入面；MiMo Code 已验证 | 需持续 rebase；治理与可观测要自建 | 中 | 上游商业化 / 许可证变更 | **推荐** |
| B. 采购 Claude Code Enterprise | 治理与可观测开箱即用，能力上限最高 | 模型与账号体系绑定；部分能力需过厂商云；定制空间小 | 高（席位费） | 数据合规与供应商依赖 | 备选（可作为高价值团队的补充） |
| C. 自研 Agent 内核 | 完全可控 | 追不上 harness 与模型协同优化的迭代；重复造轮子 | 极高 | 大概率烂尾 | 否决 |
| D. 换到 Codex CLI 二次开发 | 管控原语更完整（`requirements.toml` 硬约束） | 绑定 OpenAI 生态；Rust 栈改造门槛更高 | 中高 | 与自研模型策略冲突 | 否决 |

**选型理由**：opencode 缺的能力全部是**可外挂的**（网关、审计、遥测、私有知识、流程闭环），缺的不是 Agent 内核本身；而它独有的**服务端 + OpenAPI + SDK + ACP** 接入面，恰好是自建企业形态最贵的那部分。
**切换条件**：若上游变更许可证为非商业友好协议、或 Enterprise 版把集中配置能力做成闭源专有，则冻结在最后一个 MIT 版本并评估方案 B。

### 3.2 定制分层原则（本方案的核心约束）

> **维护成本 ≈ 与上游的偏离面积。** 因此每个特性必须先问"能不能在更低的层做"。

| 层 | 手段 | 每次上游发版的维护成本 | 适用 |
|---|---|---|---|
| **L1 配置层** | `opencode.json` / managed 目录 / MDM / `instructions` / agent & command Markdown / `permission` / `experimental.policies` | ~0 | 策略、规范、模型接入、自定义 agent 与命令 |
| **L2 插件层** | `.opencode/plugins/` 或私有 npm 包；`tool.execute.before/after`、`shell.env`、`session.*`、`permission.*`、`file.edited`、`experimental.session.compacting`；`tool()` 注册自定义工具 | 低（仅在钩子签名变更时） | 审计、遥测、防泄漏、记忆注入、企业工具 |
| **L3 旁路服务层** | MCP server、基于 OpenAPI/SDK 的自建服务、配置下发 daemon、CI 任务 | 无（与 opencode 版本解耦） | 私有知识检索、Web/流水线入口、配置热更新 |
| **L4 Fork 补丁层** | 直接改 opencode 源码 | **高**，每次 rebase 都要处理 | 仅限前三层确实做不到的（如登录方式强制、启动期版本校验） |

**硬性约束**：L4 补丁总面积 ≤ 10 个文件、≤ 2000 行；每个 L4 补丁必须登记"为什么不能在 L1–L3 做"，并同步向上游提 PR 争取内置。

## 4. 定制特性清单

> 价值：★★★ 高 / ★★ 中 / ★ 低。工作量为**含设计、开发、测试、文档的人周估算**，误差 ±40%。
> "上游风险"= 上游自己做掉、导致我们的实现变成负债的概率。

### 4.1 A 组 · 安全与合规（准入前提）

| # | 特性 | 层 | 价值 | 工作量 | 上游风险 | 说明 |
|---|---|---|---|---|---|---|
| A1 | **模型接入收敛到公司 AI 网关 + SSO 取凭据** | L1 + L2 | ★★★ | 2 人周 | 中（Enterprise 版卖点） | 自定义 provider 指向网关 `baseURL`；`{env:}`/`{file:}` 注入凭据；用 `experimental.policies` 先 `deny *` 再 `allow` 公司 provider，一并关掉 Zen 与外部 provider；插件在 `shell.env` 中注入短期 token。`NODE_EXTRA_CA_CERTS` + `HTTPS_PROXY` 处理内网证书与代理 |
| A2 | **强制配置下发（不可覆盖层）** | L1 + L3 | ★★★ | 3 人周 | 低 | Linux/Windows 落 `/etc/opencode/opencode.json`、`%ProgramData%\opencode`，macOS 走 MDM `ai.opencode.managed` plist。**注意 `.well-known/opencode` 远程配置优先级最低、会被用户配置覆盖，不能当强制手段**。因此需自建一个轻量 daemon 定期拉取策略并重写托管配置文件，补上 opencode 没有的"服务端热更新"通道 |
| A3 | **会话审计** | L2 + L3 | ★★★ | 3 人周 | 低 | 插件订阅 `session.created/updated/idle`、`tool.execute.after`、`permission.asked/replied`、`file.edited`、`command.executed`，落"人 / 仓库 / 分支 / 命令 / 变更文件 / 模型 / token"到审计平台。**离线缓冲 + 断点续传**，避免网络抖动丢审计 |
| A4 | **敏感信息与危险操作拦截** | L2 | ★★ | 4 人周 | 低 | `tool.execute.before` 拦 `bash`/`read`/`edit`/`webfetch`：密钥正则 + 熵值检测、危险命令黑名单、出网域名白名单。**必须在方案与对外口径中写明：这是策略层加固，不是安全边界**——模型可用解释器绕过路径级规则 |
| A5 | **OS 级沙箱执行** | L3（容器化） | ★★★ | 8–12 人周 + 持续运维 | 低 | opencode 无内置沙箱。优先走"受限开发容器 + `opencode serve` 服务端模式"，而非在内核里包 bubblewrap/landlock。需先做体验损伤评估（见 §8） |
| A6 | **关闭外发面** | L1 | ★★★ | 0.2 人周 | 低 | 托管配置强制 `share: "disabled"`；按需关闭依赖外部 Exa 的 `websearch`；`autoupdate` 指向内网源 |

### 4.2 B 组 · 可观测与度量

| # | 特性 | 层 | 价值 | 工作量 | 上游风险 | 说明 |
|---|---|---|---|---|---|---|
| B1 | **OpenTelemetry 遥测导出** | L2 | ★★★ | 4 人周 | 中 | 插件把事件总线转成 OTLP。**指标口径直接对齐 Claude Code**（session 数、token 与成本、工具决策接受/拒绝、代码行变更、提交与 PR 数、活跃时长），属性带 `session.id` / `user.id` / `organization.id` / `app.version` / 团队标签。这样未来若混用两种工具，看板可以复用 |
| B2 | **成本配额与提示** | L1 + 网关 | ★★★ | 1 人周（CLI 侧） | 低 | 额度与限流主体在网关侧；CLI 侧只需读取剩余额度并在 TUI toast 提示（`tui.toast.show`），以及用 agent 的 `steps` 上限约束失控循环 |
| B3 | **研发效能度量** | L3 | ★★ | 5 人周 | 低 | 旁路服务关联遥测与 git/评审数据，产出 AI 参与代码占比、采纳率、返工率。**依赖 B1 先落地**，否则无数据源 |

### 4.3 C 组 · 上下文与私有知识（差异化价值最高）

| # | 特性 | 层 | 价值 | 工作量 | 上游风险 | 说明 |
|---|---|---|---|---|---|---|
| C1 | **组织级 AGENTS.md 强制注入** | L1 | ★★★ | 0.5 人周 | 低 | 托管配置里用 `instructions` 指向内网 URL（opencode 原生支持远程指令文件，5 秒超时）与 `packages/*/AGENTS.md` 之类 glob。**全清单里性价比最高的一项** |
| C2 | **私有知识 MCP 服务** | L3 | ★★★ | 3–6 人周（取决于已有中台） | 低 | 内部文档、API 目录、历史缺陷、需求系统、代码检索各出一个 MCP server。**CLI 侧零改造**，托管配置直接下发 MCP 列表 |
| C3 | **公司技能库与分发机制** | L1 + L3 | ★★★ | 5 人周 | 中 | 用标准 `SKILL.md`（放 `.opencode/skills/`，同时兼容 `.claude/skills/`）承载架构规范、脚手架、发布流程、故障处理手册。opencode **没有插件市场概念**，需自建：私有 npm registry 或内网 git 分发 + 版本锁定 + 准入评审 + `permission.skill` 通配授权 |
| C4 | **跨会话记忆（轻量版）** | L2 | ★★ | 5 人周 | 中高 | 用 `experimental.session.compacting` 钩子注入 + 自定义 memory 工具 + 本地 SQLite，维护项目级 `MEMORY.md`（构建命令、架构决策、踩坑记录）。MiMo Code 的 `/dream` `/distill` 已验证路径可行。**建议先做只读注入 + 人工确认写入的轻量版**，再评估自动沉淀 |
| C5 | **大仓适配** | L1 | ★★ | 2 人周 | 低 | 子目录级 `AGENTS.md` + `instructions` glob；`watcher.ignore` 与 `.ignore` 裁剪；大仓评估关闭 `snapshot`（官方明确其在大仓/多子模块下会导致慢索引与高磁盘占用） |
| C6 | **打开实验性 LSP 工具** | L1 | ★★ | 1 人周（含灰度验证） | 低 | `OPENCODE_EXPERIMENTAL_LSP_TOOL=true` 让模型直接用 goToDefinition / findReferences / callHierarchy。强类型大仓上定位精度提升明显，**近乎零成本** |

### 4.4 D 组 · 研发流程闭环

| # | 特性 | 层 | 价值 | 工作量 | 上游风险 | 说明 |
|---|---|---|---|---|---|---|
| D1 | **CI / 代码评审集成** | L3 | ★★★ | 4 人周 | 低 | opencode 已有 `opencode github install` 与 GitLab 集成，但公司多为自建 GitLab/Gerrit + 自研流水线。用 headless `opencode run` 或 `opencode serve` + `prompt_async` 接入，产出评审意见与修复补丁 |
| D2 | **规格驱动工作流（需求 → 设计 → 实现 → 验证）** | L1 | ★★ | 3 人周 | 中 | 参照 MiMo Code 的 Compose：用**自定义 primary agent + slash command + skill** 实现，L1 就能覆盖大半。配合 `permission.task` 控制各阶段可调用的子智能体 |
| D3 | **工单 / 缺陷系统联动** | L3 | ★★ | 2 人周 | 低 | MCP + 自定义 command，从工单直接起会话、回写处理结论 |

### 4.5 E 组 · 交付与体验

| # | 特性 | 层 | 价值 | 工作量 | 上游风险 | 说明 |
|---|---|---|---|---|---|---|
| E1 | **版本与安装通道收敛** | L1 + L3 + L4 | ★★★ | 3 人周 | 低 | 内网 npm registry（opencode 原生支持 `.npmrc`）+ 内部发布渠道 + 自动升级指向内部源。**opencode 没有版本下限机制**（Claude Code 有 `requiredMinimumVersion`），若要强制，需一个极小的 L4 补丁在启动期校验。**这是所有强制策略的前置条件——版本散了，策略就下发不到位** |
| E2 | **IDE 接入** | L1 | ★★ | 0.5 人周 | 低 | 直接用 `opencode acp`，覆盖 Zed / JetBrains / Neovim 系。**明确不自研 IDE 插件** |
| E3 | **中文化与术语一致** | 上游 PR | ★ | 1 人周 | — | 上游已在做 i18n（含 RTL、复数规则）。**优先提 PR 回上游，不进 fork** |
| E4 | **Web / 移动端入口** | L3 | ★ | 8–12 人周 | **高** | 上游 Desktop v2 已 GA、Web 端在推进。**建议观望，先不做** |

### 4.6 明确不做

| 不做项 | 理由 |
|---|---|
| 计划模式、后台子智能体、工作区 | 上游实验开关已存在（`PLAN_MODE` / `BACKGROUND_SUBAGENTS` / `WORKSPACES`），自研即负债 |
| 自研 TUI / 桌面端 | 上游重心已转向多端，投入产出比极低 |
| 自研 IDE 插件 | ACP 已解决 |
| 自创技能 / 规则 / 工具格式 | `AGENTS.md` / `SKILL.md` / MCP 已是事实标准，自创会切断与上游及其他工具的互通 |
| 自研模型路由与负载均衡 | 归 AI 网关团队，CLI 侧只做 provider 配置 |
| 把 L2 插件拦截宣传为"安全隔离" | 技术上不成立，会造成虚假安全感 |

## 5. 落地路径

| 阶段 | 目标 | 交付物 | 周期 | 验收标准 |
|---|---|---|---|---|
| **P0 合规准入** | 能在受控范围内合法铺开 | A1 网关+SSO、A2 强制配置下发、A3 审计、A6 关外发面、C1 组织 AGENTS.md、E1 版本通道、E2 ACP 接入 | 2 个月 / 约 2 人 | 全部流量经公司网关；100% 会话可审计；试点机器策略覆盖率 ≥ 98%；`share` 与外部 provider 确认关闭 |
| **P1 度量与知识** | 能看清收益，能沉淀知识 | B1 OTel、B2 成本提示、A4 防泄漏、C2 私有知识 MCP、C3 技能库与分发、C6 LSP 工具、D1 CI/评审集成、D2 规格工作流 | 3 个月 / 约 3.5 人 | 度量看板上线并有周活/成本/工具决策三类基线；≥ 5 个内部 MCP 上线；≥ 15 个公司技能可分发；至少 1 条流水线接入 |
| **P2 深化** | 补齐隔离与长期记忆 | A5 沙箱容器化、C4 跨会话记忆、B3 效能度量、C5 大仓适配、D3 工单联动 | 3–4 个月 / 约 3 人 | 高敏仓库全部在沙箱内执行；记忆能力灰度对比出正收益方可推广 |

**贯穿全程的上游对齐机制（不是可选项）**

1. 每两周跟一次上游 `dev` 分支，跑一遍回归；
2. 通用改动（i18n、provider 适配、bug fix、LSP 工具稳定性）**提 PR 回上游**，只在私有仓保留公司专属（网关认证、审计、内部 MCP、版本校验）；
3. 维护一张"上游在做 vs 我们在做"的对照表，每月复核一次，发现撞车立即停掉自研；
4. 每季度审计 L4 补丁面积，超阈值则重构下沉到 L1–L3。

## 6. 风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|---|---|---|---|
| 上游变更许可证或把集中配置做成闭源 Enterprise 功能 | 中 | 高 | 锁定最后一个 MIT 版本并保留 vendoring；所有定制保持"可迁移"（贴合 `effect/action/resource` 的 policy 语义）；同时评估方案 B |
| 上游发版过快导致 rebase 失控 | 高 | 中 | L4 补丁面积硬约束；双周对齐；补丁必须带回归用例 |
| 把 L2 插件当安全边界，造成虚假安全感 | 中 | **高** | 对外口径统一为"策略层加固"；高敏场景必须落 A5 沙箱；在准入评审清单中明确标注 |
| 沙箱化损伤开发体验导致弃用 | 中 | 高 | P2 前先做 10 人 / 2 周试点，度量任务时长与放弃率，不达标则改用远程开发容器 |
| 遥测触碰隐私红线（提示词、代码内容） | 中 | 高 | 默认只上报元数据与指标，**不上报提示词与工具内容**；如需内容级采样，走单独审批并做脱敏 |
| 技能库无人维护变成陈旧噪音 | 高 | 中 | 技能带 owner 与复核日期；遥测统计调用次数，连续两季度零调用即归档 |
| 自研能力与上游撞车 | 中 | 中 | 上游对照表 + 月度复核；C4 记忆先做轻量版控制沉没成本 |
| 网关成为单点 | 低 | 高 | 网关侧多活；CLI 侧配置备用 provider 并由托管配置控制启用开关 |

## 7. 成本估算

| 项 | 量级 | 口径 |
|---|---|---|
| P0 人力 | ~4 人月 | 2 人 × 2 个月，含 1 名有 TS/Bun 经验的工程师 |
| P1 人力 | ~10.5 人月 | 3.5 人 × 3 个月，其中 MCP 与技能库需业务侧配合投入 |
| P2 人力 | ~10 人月 + 持续运维 | 沙箱容器化是主要变量；若走远程开发容器，需叠加计算资源成本 |
| 模型调用 | 走公司 AI 网关统一结算 | 建议先按人均 token 建立基线，再设团队月度额度 |
| 基础设施 | 内网 npm registry、OTLP 采集与存储、审计存储、MCP 服务托管 | 多数可复用现有平台 |
| 上游对齐 | ~0.5 人 常态投入 | 双周跟进 + 回归 + 提 PR |

## 8. 开放问题

| 问题 | 阻塞什么 | 决策人 | 期限 |
|---|---|---|---|
| 沙箱走本地容器 / 远程开发容器 / 进程级隔离？ | A5 全部设计与 P2 排期 | 安全 + 研发效能 | P1 中期前 |
| 遥测是否允许采集提示词与工具内容（哪怕采样脱敏）？ | B1 的数据模型与 B3 的可行性 | 安全合规 | P0 结束前 |
| 是否同时保留 Claude Code Enterprise 作为高价值团队补充？ | 预算与 B1 指标口径设计 | 研发效能负责人 | P1 启动前 |
| 技能库的准入与评审归谁（架构组 / 各业务线）？ | C3 的运营机制 | 架构委员会 | P1 启动前 |
| 是否接受一个 L4 补丁用于启动期版本强制校验？ | E1 的强制力 | 技术负责人 | P0 中期 |
| 主力代码仓是否为单体大仓？ | C5 优先级与 `snapshot` 策略 | 研发效能 | P0 结束前 |

## 参考资料

1. [ai-coding-insight-0001《CLI 形态 AI Coding 工具的技术路线与企业化差距》](../insights/2026-08-11-cli-coding-agent-landscape.md)
2. [ai-coding-vendor-0001《opencode 产品档案》](../vendors/opencode.md)
3. [opencode 文档源码（`anomalyco/opencode`，commit `d041eee`）](https://github.com/anomalyco/opencode/tree/dev/packages/web/src/content/docs)（访问日期 2026-08-11）
4. [Set up Claude Code for your organization](https://code.claude.com/docs/en/admin-setup)（访问日期 2026-08-11）
5. [Claude Code Monitoring（OpenTelemetry）](https://code.claude.com/docs/en/monitoring-usage)（访问日期 2026-08-11）
6. [XiaomiMiMo/MiMo-Code README](https://github.com/XiaomiMiMo/MiMo-Code)（访问日期 2026-08-11）
