# AI Coding 工具（ai-coding）—— 领域索引

**范围**：编码助手与编码 Agent、代码生成/补全/重构、代码库理解与索引、研发流程集成（CI、Code Review、测试生成）、编码类评测与研发效能度量。
**不含**：通用 Agent 平台机制（见 [agent-platform](../agent-platform/INDEX.md)）。
详见 [docs/taxonomy.md](../../docs/taxonomy.md#ai-coding--ai-coding-工具)。

最后更新：2026-08-12 ｜ 条目数：4

## 专题

领域内围绕同一问题成组的条目。**先在这里定位专题，再进入具体条目**；未归入专题的条目只出现在下方按类型的表格中。

| 专题 | 问题 | 包含条目 | 状态 |
|---|---|---|---|
| **整体格局与企业落地** | CLI 形态编码 Agent 怎么选、怎么在公司内合规铺开 | [insight-0001](insights/2026-08-11-cli-coding-agent-landscape.md) · [solution-0001](solutions/2026-08-11-opencode-enterprise-customization-roadmap.md) · [vendor-0001](vendors/opencode.md) | 进行中 |
| **记忆与上下文管理** | opencode 在记忆/上下文上缺什么、按什么顺序补 | [insight-0002](insights/2026-08-12-memory-context-management-landscape.md) | 进行中（待补 solution） |

## 业界洞察 · insights/

| ID | 标题 | 摘要 | 标签 | 状态 | 更新 |
|---|---|---|---|---|---|
| [ai-coding-insight-0001](insights/2026-08-11-cli-coding-agent-landscape.md) | CLI 形态 AI Coding 工具的技术路线与企业化差距 | CLI Agent 分三条路线；中立内核在能力上必然滞后，企业价值在治理、私有上下文与流程闭环 | cli-agent, market-landscape, tech-route, guardrail, observability | review | 2026-08-11 |
| [ai-coding-insight-0002](insights/2026-08-12-memory-context-management-landscape.md) | AI Coding 工具的记忆与上下文管理：机制拆解与 opencode 差距分析 | opencode 有压缩无记忆；六层能力里它缺第四层，且第一、三、六层只做到及格线 | context-engineering, memory, agent-skills, repo-understanding | review | 2026-08-12 |

## 方案设计 · solutions/

| ID | 标题 | 摘要 | 标签 | 状态 | 更新 |
|---|---|---|---|---|---|
| [ai-coding-solution-0001](solutions/2026-08-11-opencode-enterprise-customization-roadmap.md) | 基于 opencode 的公司内 AI Coding 工具定制特性路线 | 定制按四层分配，P0 补治理与接入、P1 补可观测与私有上下文，编排交给上游 | cli-agent, architecture, landing, enterprise-landing, sandbox | draft | 2026-08-11 |

## 产品档案 · vendors/

| ID | 产品 | 定位 | 厂商 | 状态 | 核对日期 |
|---|---|---|---|---|---|
| [ai-coding-vendor-0001](vendors/opencode.md) | opencode | MIT 开源、模型中立的终端编码 Agent，客户端/服务端分离，是二次开发的主流内核 | anomalyco（原 SST） | stable | 2026-08-11 |

## 选题池

尚未开展、但已识别为值得调研的方向：

- 主流 AI Coding 工具能力横评（CLI Agent vs IDE 插件两条路线）
- 代码库理解与索引方案对比（向量检索 / AST / Agent 自主探索）
- AI 参与 Code Review 与测试生成的落地形态
- 编码 Agent 的评测基准与真实效能度量方式
- 企业内推广 AI Coding 的落地方案（权限、合规、度量、培训）
- Claude Code 产品档案（作为企业管控能力的对标基线）
- MiMo Code 产品档案（opencode 下游 fork 的定制做法拆解）
- 编码 Agent 的 OS 级沙箱方案对比（容器 / devcontainer / Seatbelt·Landlock）

## 维护

新增条目后同步更新：本文件对应表格 → [全局索引](../../INDEX.md) 的条目数与「最近更新」。
