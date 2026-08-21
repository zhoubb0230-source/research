# 业务洞察（business-insight）—— 领域索引

**范围**：面向新业务/新机会的产业洞察方法与洞察类多智能体系统——机会筛选框架与评分口径、洞察专家团的角色与编排设计、防编造机制，以及该系统产出的机会榜单与深度洞察报告。
**不含**：Agent 平台本身的机制与产品（见 [agent-platform](../agent-platform/INDEX.md)）。本领域关注的是"用多 Agent 做洞察这件事怎么做对"，不是"Agent 平台怎么建"。
详见 [docs/taxonomy.md](../../docs/taxonomy.md#business-insight--业务洞察)。

最后更新：2026-08-20 ｜ 条目数：6

## 业界洞察 · insights/

| ID | 标题 | 摘要 | 标签 | 状态 | 更新 |
|---|---|---|---|---|---|
| _暂无_ | | | | | |

> 专家团每轮筛选产出的**机会榜单**与**单机会深度洞察报告**归档到本目录，模板见
> [templates/longlist.md](assets/expert-team/templates/longlist.md) 与
> [templates/opportunity-report.md](assets/expert-team/templates/opportunity-report.md)。

## 方案设计 · solutions/

| ID | 标题 | 摘要 | 标签 | 状态 | 更新 |
|---|---|---|---|---|---|
| [business-insight-solution-0001](solutions/2026-08-19-business-insight-expert-team.md) | 业务洞察专家团：多智能体产业机会洞察系统设计方案 | 洞察质量由证据架构决定而非角色数量；先过闸后打分、证伪优先、数字必须绑定证据ID | architecture, multi-agent, orchestration, guardrail, anti-hallucination | draft | 2026-08-19 |
| [business-insight-solution-0002](solutions/2026-08-19-opportunity-screening-rubric.md) | 产业机会经纬线：闸门规则与评分卡 | 经纬线拆成先过闸后加权两段；毛利看在位者、两强看是否受管制、缺数据不淘汰 | selection, rubric, opportunity-scouting, export-control | draft | 2026-08-19 |
| [business-insight-solution-0003](solutions/2026-08-19-openclaw-deployment.md) | 业务洞察专家团的 OpenClaw 落地方案 | 钩子不能阻断，闸门改放进唯一发布通道；派发深度必须设2，红队隔离由平台保证 | landing, multi-agent, orchestration, guardrail, anti-hallucination | draft | 2026-08-20 |
| [business-insight-solution-0004](solutions/2026-08-19-insight-service-spine.md) | 洞察服务的统一骨架与任务包规范 | 洞察需求的差异是退化不是缺失；一条骨架加参数化，范式降级为预设而非类型 | architecture, selection, rubric, guardrail, anti-hallucination | draft | 2026-08-19 |
| [business-insight-solution-0005](solutions/2026-08-19-dsh-deployment.md) | 洞察服务的 DeepSeek Harness 试跑方案 | 角色定义走 skills 而非配置，把唯一形状未确认的部分隔离到一个可弃文件 | landing, multi-agent, orchestration, guardrail | draft | 2026-08-20 |
| [business-insight-solution-0006](solutions/2026-08-20-expert-config-boundaries.md) | 数字专家的配置、人格与技能边界 | 三层不是两层：能配置的必须配置，但每轮注入的散文和按需加载的技能要分开 | architecture, multi-agent, orchestration, landing | draft | 2026-08-20 |

## 产品档案 · vendors/

| ID | 产品 | 定位 | 厂商 | 状态 | 核对日期 |
|---|---|---|---|---|---|
| _暂无_ | | | | | |

## 可运行资产 · assets/expert-team/

专家团的全套可执行资产（平台中立）。装配说明见 [assets/expert-team/README.md](assets/expert-team/README.md)。

| 资产 | 说明 |
|---|---|
| [rubric/rubric-v1.yaml](assets/expert-team/rubric/rubric-v1.yaml) | 机器可读的闸门、权重与六档锚点。**执行以此为准**，solution-0002 是它的说明 |
| [schemas/](assets/expert-team/schemas/) | 证据卡、候选机会、评分卡、裁决的 JSON Schema（防编造第一道闸） |
| [BOUNDARIES.md](assets/expert-team/BOUNDARIES.md) | **配置(T1)/人格(T2)/技能(T3) 三层边界规范**。装配任何 harness 前先读 |
| [experts/](assets/expert-team/experts/) | **12 位专家的独立目录**（专家定义的唯一真相源）：每位含 `expert.yaml` 装配意图 + `IDENTITY/SOUL/AGENTS` 人格 + `skills/` 技能 + 验收清单 |
| [orchestration/](assets/expert-team/orchestration/) | 阶段编排、模型路由、四类平台落地映射 |
| [templates/](assets/expert-team/templates/) | 榜单、深度报告、证据卡的输出模板 |
| [checks/verify_report.py](assets/expert-team/checks/verify_report.py) | 渲染前确定性数字校验（防编造第三道闸，含自测夹具） |
| [data-sources/](assets/expert-team/data-sources/) | 数据源类型、证据等级判定与口径陷阱清单 |
| [expert-team-openclaw/](assets/expert-team-openclaw/) | **OpenClaw 部署包**：编排框架 + 12 份 `entry.json5` 逐专家配置、工作区装配脚本、发布闸、钩子 |
| [insight-service/](assets/insight-service/) | **洞察服务骨架**：十动作骨架与回环模型、任务包 Schema、五个聚合算子、**试跑验收契约**、两份预设与校验器 |
| [expert-team-dsh/](assets/expert-team-dsh/) | **DeepSeek Harness 部署包**：宿主组合覆盖 + preset 组合 + 12 份 `spawn.json` 逐专家实参、装配脚本与发布闸 |

> **本领域的资产与方案中不含任何真实产业数据。** 产业数据只能由专家团在运行时带来源产出，
> 存入 `assets/evidence/<batch>/`，并经 `verify_report.py` 校验后方可写入报告。

## 选题池

- **首轮跑通后回灌**：P0 口径校准的人机分差记录 → 沉淀为领域知识包
- 半导体装备技术链的子能力项图谱（A 维度判定的底座，目前只有清单没有图谱）
- 洞察类多智能体系统的失效模式与业界做法对比（需先积累自有运行数据，避免无来源写作）
- 出口管制清单的结构化跟踪机制（清单更新频繁，一次性检索无法长期有效）
- 付费产业数据源的选型与性价比评估

## 维护

新增条目后同步更新：本文件对应表格 → [全局索引](../../INDEX.md) 的条目数与「最近更新」。
