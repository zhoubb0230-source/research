# AI Coding 工具（ai-coding）—— 领域索引

**范围**：编码助手与编码 Agent、代码生成/补全/重构、代码库理解与索引、研发流程集成（CI、Code Review、测试生成）、编码类评测与研发效能度量。
**不含**：通用 Agent 平台机制（见 [agent-platform](../agent-platform/INDEX.md)）。
详见 [docs/taxonomy.md](../../docs/taxonomy.md#ai-coding--ai-coding-工具)。

最后更新：2026-08-12 ｜ 条目数：4

## 业界洞察 · insights/

| ID | 标题 | 摘要 | 标签 | 状态 | 更新 |
|---|---|---|---|---|---|
| [ai-coding-insight-0001](insights/2026-08-12-coding-agent-memory-mechanisms.md) | AI Coding Agent 的记忆机制：五家实现原理拆解与 OpenCode 差距 | 记忆已从静态指令文件演进为「离线抽取＋索引常驻＋按需检索」的四层结构，OpenCode 只做到第一层 | memory, context-engineering, cli-agent, tech-route | draft | 2026-08-12 |
| [ai-coding-insight-0002](insights/2026-08-12-ai-coding-paradigm-methodology-and-repo-shape.md) | AI Coding 编程范式：方法论与仓库形态的双重重构 | 范式重心已从写提示转向配置 Agent 周边设施；可验证边界比规格文档更能决定成败 | spec-driven, verification, harness-engineering, repo-shape, tech-route | draft | 2026-08-12 |

## 方案设计 · solutions/

| ID | 标题 | 摘要 | 标签 | 状态 | 更新 |
|---|---|---|---|---|---|
| [ai-coding-solution-0001](solutions/2026-08-12-opencode-memory-plugin-design.md) | OpenCode 记忆能力设计方案：零上游补丁的插件式实现 | 全部能力经 plugin hook 实现，主干零补丁，rebase 成本恒定为零 | memory, context-engineering, architecture, landing | draft | 2026-08-12 |
| [ai-coding-solution-0002](solutions/2026-08-12-agent-ready-repo-and-workflow.md) | Agent-Ready 仓库与工作流落地方案：从可验证边界到分层上下文 | 按「可验证边界→分层上下文→选择性规格驱动」三级投入，不先引入 SDD 工具链 | verification, repo-shape, harness-engineering, architecture, landing | draft | 2026-08-12 |

## 产品档案 · vendors/

| ID | 产品 | 定位 | 厂商 | 状态 | 核对日期 |
|---|---|---|---|---|---|
| _暂无_ | | | | | |

## 选题池

尚未开展、但已识别为值得调研的方向：

- 主流 AI Coding 工具能力横评（CLI Agent vs IDE 插件两条路线）
- 代码库理解与索引方案对比（向量检索 / AST / Agent 自主探索）
- L3 知识资产：skills / 流程沉淀的业界形态对比（Codex skills、Gemini SkillExtractionAgent、Claude Skills）
- AI 参与 Code Review 与测试生成的落地形态
- 编码 Agent 的评测基准与真实效能度量方式
- 企业内推广 AI Coding 的落地方案（权限、合规、度量、培训）
- 人机协作形态演进史（补全 → Chat → IDE Agent → CLI Agent → 异步委派 / 并行多 Agent）——`ai-coding-insight-0002` 明确划在边界外
- 多 Agent 并行的集成瓶颈：模块粒度、任务切分与合并冲突治理
- 规格驱动工具链实测对比（Spec Kit / Kiro / OpenSpec / BMAD 的真实开销与收益 A/B）

## 维护

新增条目后同步更新：本文件对应表格 → [全局索引](../../INDEX.md) 的条目数与「最近更新」。
