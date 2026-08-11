# 全局索引

AI 先进技术调研知识库的一级入口。**先在这里定位领域，再进入领域索引，最后打开正文。**

最后更新：2026-08-11

## 领域一览

| 领域 ID | 名称 | 范围 | 索引 | 条目数 |
|---|---|---|---|---|
| `agent-platform` | 智能体平台 | Agent 框架/编排/运行时、多智能体协作、工具与记忆、平台化产品（Dify、Coze、Bedrock Agents 等） | [domains/agent-platform/INDEX.md](domains/agent-platform/INDEX.md) | 2 |
| `ai-coding` | AI Coding 工具 | 编码助手与 Agent（Claude Code、Cursor、Copilot 等）、代码生成/评测、研发流程集成 | [domains/ai-coding/INDEX.md](domains/ai-coding/INDEX.md) | 3 |

## 跨领域索引

- 分类体系与标签词表：[docs/taxonomy.md](docs/taxonomy.md)
- 写作与索引规范：[docs/conventions.md](docs/conventions.md)
- 模板：[insight](templates/insight.md) · [solution](templates/solution.md) · [vendor](templates/vendor.md)

## 最近更新

| 日期 | 领域 | 条目 | 变更 |
|---|---|---|---|
| 2026-08-11 | ai-coding | ai-coding-solution-0001 | 新增《基于 opencode 的公司内 AI Coding 工具定制特性路线》 |
| 2026-08-11 | ai-coding | ai-coding-insight-0001 | 新增《CLI 形态 AI Coding 工具的技术路线与企业化差距》 |
| 2026-08-11 | ai-coding | ai-coding-vendor-0001 | 新增 opencode 产品档案 |
| 2026-08-07 | agent-platform | agent-platform-solution-0001 | 新增《数字员工平台设计方案》 |
| 2026-08-07 | agent-platform | agent-platform-insight-0001 | 新增《企业级 Agent 的身份、授权与数据隔离：九个业界范式》 |
| 2026-08-07 | — | — | 初始化仓库骨架 |

## 维护说明

- 新增领域：建 `domains/<id>/{insights,solutions,vendors,assets}` + `INDEX.md`，在上表加一行，并登记到 `docs/taxonomy.md`。
- 每次条目变更：更新对应领域的条目数与「最近更新」表（保留最近 20 条）。
