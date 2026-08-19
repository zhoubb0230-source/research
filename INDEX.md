# 全局索引

AI 先进技术调研知识库的一级入口。**先在这里定位领域，再进入领域索引，最后打开正文。**

最后更新：2026-08-19

## 领域一览

| 领域 ID | 名称 | 范围 | 索引 | 条目数 |
|---|---|---|---|---|
| `agent-platform` | 智能体平台 | Agent 框架/编排/运行时、多智能体协作、工具与记忆、平台化产品（Dify、Coze、Bedrock Agents 等） | [domains/agent-platform/INDEX.md](domains/agent-platform/INDEX.md) | 2 |
| `ai-coding` | AI Coding 工具 | 编码助手与 Agent（Claude Code、Cursor、Copilot 等）、代码生成/评测、研发流程集成 | [domains/ai-coding/INDEX.md](domains/ai-coding/INDEX.md) | 0 |
| `business-insight` | 业务洞察 | 新业务/新机会的产业洞察方法、机会筛选框架与评分口径、洞察类多智能体系统设计，以及其产出的机会榜单与深度报告 | [domains/business-insight/INDEX.md](domains/business-insight/INDEX.md) | 2 |

## 跨领域索引

- 分类体系与标签词表：[docs/taxonomy.md](docs/taxonomy.md)
- 写作与索引规范：[docs/conventions.md](docs/conventions.md)
- 模板：[insight](templates/insight.md) · [solution](templates/solution.md) · [vendor](templates/vendor.md)

## 最近更新

| 日期 | 领域 | 条目 | 变更 |
|---|---|---|---|
| 2026-08-19 | business-insight | business-insight-solution-0002 | 新增《产业机会经纬线：闸门规则与评分卡》 |
| 2026-08-19 | business-insight | business-insight-solution-0001 | 新增《业务洞察专家团：多智能体产业机会洞察系统设计方案》+ 全套可运行资产 |
| 2026-08-19 | — | — | 新增领域 business-insight |
| 2026-08-07 | agent-platform | agent-platform-solution-0001 | 新增《数字员工平台设计方案》 |
| 2026-08-07 | agent-platform | agent-platform-insight-0001 | 新增《企业级 Agent 的身份、授权与数据隔离：九个业界范式》 |
| 2026-08-07 | — | — | 初始化仓库骨架 |

## 维护说明

- 新增领域：建 `domains/<id>/{insights,solutions,vendors,assets}` + `INDEX.md`，在上表加一行，并登记到 `docs/taxonomy.md`。
- 每次条目变更：更新对应领域的条目数与「最近更新」表（保留最近 20 条）。
