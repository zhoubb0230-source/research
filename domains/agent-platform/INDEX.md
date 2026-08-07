# 智能体平台（agent-platform）—— 领域索引

**范围**：Agent 编排与运行时、多智能体协作、工具调用与 MCP、记忆与上下文工程、Agent 可观测与评测、智能体平台类产品、企业级落地方案。
**不含**：仅面向编码场景的 Agent（见 [ai-coding](../ai-coding/INDEX.md)）。
详见 [docs/taxonomy.md](../../docs/taxonomy.md#agent-platform--智能体平台)。

最后更新：2026-08-07 ｜ 条目数：2

## 业界洞察 · insights/

| ID | 标题 | 摘要 | 标签 | 状态 | 更新 |
|---|---|---|---|---|---|
| [agent-platform-insight-0001](insights/2026-08-07-enterprise-agent-identity-authz-landscape.md) | 企业级 Agent 的身份、授权与数据隔离：九个业界范式 | 严肃的企业级 Agent 方案都把重心放在身份、授权、审计，而非编排能力 | identity, authz, data-isolation, audit, mcp, rag, guardrail, market-landscape | draft | 2026-08-07 |

## 方案设计 · solutions/

| ID | 标题 | 摘要 | 标签 | 状态 | 更新 |
|---|---|---|---|---|---|
| [agent-platform-solution-0001](solutions/2026-08-07-digital-employee-platform.md) | 数字员工平台设计方案 | 运行时不判权限，鉴权下沉网关与授权引擎，七道闸门叠加做数据隔离 | architecture, selection, enterprise-landing, identity, authz, data-isolation, audit, guardrail | draft | 2026-08-07 |

## 产品档案 · vendors/

| ID | 产品 | 定位 | 厂商 | 状态 | 核对日期 |
|---|---|---|---|---|---|
| _暂无_ | | | | | |

## 选题池

尚未开展、但已识别为值得调研的方向：

- **产品档案补齐**（由 solution-0001 选型表触发，被反复引用，宜独立成 vendor 卡片）：agentgateway、OpenFGA、Coze Studio、Flowable / Camunda 8（含许可证）、Milvus 多租户
- **来源核验**：insight-0001「待核清单」四项——Camunda 2026 报告数据、MCP 2026-07-28 修订内容、全部来源的 URL 与访问日期、Agentforce 风险分析出处
- 多智能体编排的主流技术路线对比（LangGraph / AutoGen / CrewAI / 平台型产品）
- MCP 生态现状与企业接入方式
- Agent 记忆与上下文工程的工程实践
- Agent 可观测性与效果评测体系
- 企业级智能体平台自建 vs 采购的选型框架

## 维护

新增条目后同步更新：本文件对应表格 → [全局索引](../../INDEX.md) 的条目数与「最近更新」。
