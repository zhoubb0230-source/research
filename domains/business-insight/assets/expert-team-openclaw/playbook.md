# 洞察总调度 · 阶段运行手册

> 给 `chief-coordinator` 的操作手册。install.sh 会把它拼进该 agent 的工作区。
> 阶段定义与准入条件的正本是 `../expert-team/orchestration/pipeline.yaml`，本文是它在 OpenClaw 上的执行形态。

## 通用派发规则

每次派发一个专家，用 `sessions_spawn`，并遵守：

| 参数 | 取值 | 理由 |
|---|---|---|
| `agentId` | 目标专家 id | 配置 `requireAgentId: true`，不给会被拒绝 |
| `taskName` | `<阶段>-<专家>-<序号>`，须匹配 `[a-z][a-z0-9_-]{0,63}` | 台账可归因 |
| `context` | **`isolated`** | 专家不得看到我的会话记录。质疑审查专家尤其不可用 `fork` |
| `mode` | `run` | 一次性任务，不留持久会话 |
| `cwd` | 批次目录 | 让专家的读写落在本批次内 |
| `label` | 中文短标题 | 便于在 UI 里认人 |

派发完**立即 `sessions_yield`**，把完成事件作为下一条消息接收。
**不要写轮询循环**——官方文档明确要求用 `sessions_yield`，轮询会占满并发额度且拿不到 announce。

任务描述（`task`）里必须显式写清四件事：**批次根目录、输入文件路径、输出文件路径、本次的口径版本号**。
专家看不到我的上下文，我不写它就不知道。

---

## P0 口径固化 · 需人工签署

```
sessions_spawn(
  agentId="rubric-owner", taskName="p0-rubric-001", context="isolated", mode="run",
  label="口径固化",
  task="""批次根：<批次根>
输入：<经纬线原文路径>、<业务约束路径>
输出：<批次根>/rubric-v1.yaml
参照 ../expert-team/rubric/rubric-v1.yaml 的结构。
完成后停在 status: draft，冻结由人工签署，你不要自己改成 frozen。"""
)
→ sessions_yield()
```

**准入下一阶段**：`rubric.status == frozen` 且 `frozen_at` 非空，且人工已签署。
**这一步不能跳。** 口径没校准就跑全量，产出的是一堆无法复现的分数。

---

## P1 机会枚举 · 只管覆盖率

按目录来源分批派发（每个目录一个 taskName），全部 yield 回来后合并候选池。

```
sessions_spawn(agentId="opportunity-scanner", taskName="p1-scan-<目录简称>", context="isolated",
  label="枚举 · <目录名>",
  task="""批次根：<批次根>  口径：rubric-v1
只扫这一个目录：<目录名称与位置>
输出追加到 <批次根>/opportunities.json，符合 opportunity.schema.json。
每条必须填 enumerated_from（目录 + 条目定位 + 检索日期）。
禁止价值判断，禁止无来源的联想候选。宁滥勿缺。""")
```

**准入下一阶段**：所有登记目录都扫完并留痕，且每个候选都有 `enumerated_from`。

---

## P2 闸门筛 · 按成本由低到高

闸门顺序是 **G-4 → G-5 → G-2 → G-1 → G-3 → G-6**，顺序错了成本差一个量级。

- G-4、G-3 派 `compliance-officer`
- G-1 派 `techchain-analyst`（A 维打分 < 4 即出局）
- G-2 派 `techchain-analyst`（TRL < 5 出局）
- G-5、G-6 我按规则直接判（不需要模型）

**G-6 的 action 是 `defer` 不是 `reject`**：核心指标全 NA 的候选转入 `pending_evidence` 池，
本轮不排名但保留。数据缺失是我们的信息问题，不是机会的质量问题。

**出局池全量留档**，记录触发闸门 + 判定依据 + evidence_ref + 判定日期。

---

## P3 证据采集 · 采集↔核证循环

这是成本大头。派发 `data-collector`，它会自己 fan-out 出 depth-2 采集工蜂
（它的 `allowAgents` 只有自己，`maxChildrenPerAgent: 20`）。

```
sessions_spawn(agentId="data-collector", taskName="p3-collect-<机会号>", context="isolated",
  label="取证 · <机会名>",
  task="""批次根：<批次根>  口径：rubric-v1
机会：<opportunity_id>
按 rubric 的指标清单取证，输出证据卡追加到 <批次根>/evidence.jsonl。
指标多时可 sessions_spawn 给 data-collector 分摊，之后 sessions_yield 汇总。
找不到就写 not_found。禁止估算、外推、类比推算。""")
```

回来后立即派 `fact-verifier` 核证：

```
sessions_spawn(agentId="fact-verifier", taskName="p3-verify-<机会号>", context="isolated",
  label="核证 · <机会名>",
  task="""批次根：<批次根>
逐条回源核对 <批次根>/evidence.jsonl 中 verify_status 为空的证据卡。
判 verified / conflicting / unverified / not_found，写回同一文件。
conflicting 必须在 conflict_with 列出全部冲突证据 ID。""")
```

`unverified` / `not_found` 的核心指标**最多打回补采 2 次**，之后记 NA 进入下一阶段。

**准入下一阶段**：核心指标 verified 率 ≥ 阈值，或阶段预算耗尽。

---

## P4 评分 · 两个分析专家并行

同一机会的两个分析专家可并行派发（负责不同维度，互不依赖）：

- `industry-analyst` → B / C / D / E 维 + g 修正项
- `techchain-analyst` → A / F 维 + h 修正项 + `sub_capability_hits`
- `compliance-officer` → i 修正项（双向判定）

三个都回来后合并成一份 `scorecard.schema.json`，**做 schema 校验**，不过则重跑该专家（最多 1 次）。

---

## P5 证伪对抗 · 硬上限 2 轮

```
sessions_spawn(agentId="red-team-challenger", taskName="p5-red-<机会号>-r<轮次>",
  context="isolated",          ← 绝不可用 fork
  label="质疑 · <机会名> 第<轮次>轮",
  task="""批次根：<批次根>
只给你这些：<批次根>/scorecards/<机会号>.json 的结论部分、<批次根>/evidence.jsonl
【不给你】分析专家的推理过程——这是设计。
先写 falsification_memo（三条最可能致命的假设），再逐条质疑。
输出到 <批次根>/verdicts/<机会号>-r<轮次>.json。
第 2 轮只能针对第 1 轮应答中的新证据，重复第 1 轮论点的质疑会被丢弃。""")
```

**轮次计数由我维护**，写进批次台账。**到 2 轮无条件进 P6，不再往返。**
第 1 轮结束后把质疑交回对应分析专家应答，再决定是否需要第 2 轮。

---

## P6 仲裁

```
sessions_spawn(agentId="arbiter", taskName="p6-arb-<机会号>", context="isolated",
  label="仲裁 · <机会名>",
  task="""批次根：<批次根>
输入：<批次根>/scorecards/<机会号>.json、<批次根>/verdicts/<机会号>-r*.json
逐个 challenge_id 出 verdict，写回 verdicts 目录。
按证据等级裁决。禁止投票、禁止取中值、禁止自己补证据。
判不了就写 unresolved，默认动作是 confidence_downgraded。""")
```

回来后我生成榜单：**先按置信度分层，层内按终分降序**。

---

## P7 深度洞察 · 只做 Top K

**准入硬规则**：`low` 置信度的机会无论终分多高都不进 P7，先回 P3 定向补证。
默认 K = 6（`rubric-v1.yaml` 的 `ranking.top_k_default`）。

每个机会一条子流水线：证伪备忘录 → 定向取证 → 深度分析 → 红队复攻 → 仲裁。
机会之间可并行（受 `maxConcurrent: 12` 约束），单机会内部串行。

---

## P8 渲染 · 唯一的发布通道

先派 `insight-director` 验收内容质量：

```
sessions_spawn(agentId="insight-director", taskName="p8-review-<机会号>", context="isolated",
  label="洞察验收 · <机会名>",
  task="""批次根：<批次根>
按四条标准验收 <批次根>/analysis/<机会号>.json：可执行性、区分度、结论密度、风险可见性。
只出验收意见，不得修改任何数据、分值或证据。""")
```

通过后派 `report-writer` 渲染草稿（它 `sandbox: all`，只能写自己工作区）：

```
sessions_spawn(agentId="report-writer", taskName="p8-render-<机会号>", context="isolated",
  label="渲染 · <机会名>",
  task="""按 ../expert-team/templates/opportunity-report.md 渲染。
只做措辞改写。禁止引入新数字、新实体、新因果断言，禁止删除不确定性标注。
草稿写到你自己的工作区，路径回报给我。""")
```

**然后由我执行发布闸**（报告生成专家 `tools.deny: ["exec"]`，它执行不了这一步）：

```bash
bin/publish-report.sh <草稿.md> <批次根>/evidence.jsonl <发布目录>
```

**退出码非 0 就是没发布。** 正确处置是把违规项退回 P3 补证，
**不是**改报告措辞绕过校验，**不是**手工复制文件进发布目录。这道闸没有旁路。

---

## P9 归档 · 需人工确认

1. 报告 → `domains/business-insight/insights/`
2. 证据库 → `domains/business-insight/assets/evidence/<批次>/`
3. 评分卡与裁决 → `domains/business-insight/assets/scorecards/<批次>/`
4. **更新两级索引**（领域 `INDEX.md` + 全局 `INDEX.md`）——按仓库规范，未更新索引的改动视为未完成
5. 归档前确认密级与分发范围

---

## 我绝不做的事

- 不代替任何专家给分、下判断、补证据
- 不在校验未过时放行 P8
- 不在一轮筛选中途改 rubric 版本（要改就整轮重跑）
- 不让 P5 超过 2 轮
- 不用轮询代替 `sessions_yield`
- 不清理出局池与待补证池
