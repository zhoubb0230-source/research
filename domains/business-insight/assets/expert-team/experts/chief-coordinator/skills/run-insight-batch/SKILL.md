---
name: run-insight-batch
description: 洞察批次的十动作准入条件、五条回边路由表与返工预算。推进任何一个阶段前先读本技能，不要凭记忆推进。
user-invocable: false
disable-model-invocation: false
---

# 洞察批次运行手册

> 骨架正本：`assets/insight-service/spine.md`｜算子契约：`assets/insight-service/aggregators.md`
> **本技能是平台中立的。** 具体用什么接口派发（`sessions_spawn` / `spawnTeammate`），
> 见你所在 harness 的运行约定片段，已由安装脚本拼进你的 `AGENTS.md`。

## 派发时必须写清的四件事

派发对象拿到的是**干净上下文**，它看不到你的会话。任务描述里没写的，它就是不知道。

1. 批次根的**绝对路径**
2. 本次动作编号与范围（哪些对象、哪些维度）
3. 输入文件的**具体路径**（不是"上一步的产出"）
4. 输出写到哪、必须符合哪个 schema、brief 版本号

---

## ① 界定（含分诊）→ `insight-planner`

**它可能返回"拒绝"，那是正常终局，不是失败。**

```
分诊三问：
  这是决策问题还是检索问题？     → 检索直接作答，不启动专家团
  decisionQuestion 答得上来吗？   → 连续两轮澄清仍答不上 → 判为非洞察需求
  知识库里有未过期的同题结论吗？   → 有则引用既有条目，不重跑
```

产出 `<批次根>/brief.json`，**必须跑校验**：

```
python3 assets/insight-service/checks/validate_brief.py <批次根>/brief.json
```

**准入 ②**：brief 已冻结（`frozenAt` 非空）**且**人工签署。冻结不是你能自行置位的。

## ② 枚举 → `scope-definer`

按 `brief.subject.source.type` 决定形态：

| source.type | 做法 |
|---|---|
| `catalog_enumeration` | 逐目录穷举，每目录一个任务 |
| `given` | 直接采纳清单（**枚举退化**，记入 `degradations`） |
| `baseline` | 从上一批次的 `baseline.json` 载入对象集合 |
| `hypothesis_generation` | 从已知机制清单或历史案例生成候选假说 |

**准入 ③**：每个对象都有 `enumerated_from`。

## ③④ 取证 ⇄ 核证 → `data-collector` / `fact-verifier`

取证回来**立即**核证，不要攒一批再核。

- `unverified` / `not_found` 的核心指标 → 打回补采，**最多 2 次**，之后记 `NA`
- 取证中报回"发现新对象" → **回边 R1**：新对象走一遍闸门再并入；若已过刻画，一并触发 R3
- `brief.evidencePolicy.directVerification.available` 为真 → 要求做直接验证
  （跑一下 / 读源码 / 调 API），它是最强的一手证据

**准入 ⑤**：核心指标 verified 率达标，或阶段预算耗尽。

## ⑤⑥ 刻画 → 聚合 → `comparative-analyst` / `domain-analyst` / `compliance-reviewer`

三者可并行：通用维度归 `comparative-analyst`，`ownerRole=domain-analyst` 的维度归领域分析专家，
合规维度归合规审查专家。刻画产出**必须带 `revision`**。

聚合按 `brief.aggregation` 的算子执行，**可组合**（如 cluster + matrix）。

## ⑦ 证伪 → `red-team-challenger`

**必须隔离上下文。** 只给结论与证据，**不给刻画的推理过程**：

```
给：   <批次根>/aggregation/*.json 的结论部分、<批次根>/evidence.jsonl
不给： <批次根>/characterization/*.json 里的 rationale 字段
```

做 **Top K + `rework.topKBuffer`（默认 3）** 个对象，不是恰好 Top K。

---

## 回边 R2：质疑类型决定返工回到哪一步

**这是全流程最容易做错的一步。不要把质疑一律扔给仲裁。**

| 质疑类型 | 派给谁 | 返工指令要点 |
|---|---|---|
| `evidence_missing` | `data-collector` | 定向补采指定指标 |
| `evidence_weak` | `data-collector` | 找**更高等级**来源，不是更多同级来源 |
| `source_grade_too_low` | `data-collector` | 追到一手来源 |
| `stale_data` | `data-collector` | 重新取当期数据 |
| `confirmation_bias` | `data-collector` | **明确要求补反向证据**——不写清楚它会去找更多同向材料，反而加剧偏误 |
| `scope_mismatch` | `fact-verifier` → `comparative-analyst` | 先修证据卡 `scope`，再重刻画 |
| `anchor_misapplied` | `comparative-analyst` | 证据够，档位判错，不需补证 |
| `counterexample` | `arbiter` | 判断问题，补证解决不了 |
| `causal_overreach` | `arbiter` | 同上 |
| `definition_drift` | **人工** | 口径异议，**唯一能改 brief 的路径**（回边 R5） |

### 三条硬约束

1. **只回不进。** 补来的证据必须重走 ④核证 → ⑤刻画 → ⑥聚合。**不许直接改分。**
2. **单调收敛。** 每次返工后检查证据库有无**新增 `evidence_id`**。
   没有 = 补证失败，该质疑按保守优先**直接成立**，不再重试。
3. **预算。** `rework.perSubject`（默认 2）、`rework.globalShare`（默认 0.2）。
   超预算 → 强制进 ⑧ 仲裁。

### 证伪轮次

**硬上限 2 轮。** 第 2 轮只能针对第 1 轮应答中的**新证据**；重复第 1 轮论点的质疑直接丢弃。
每轮次写进 `ledger.jsonl`，供事后审计。

## 回边 R3：任何刻画 revision 变了，聚合就作废

标记聚合为 `stale` → **全量重算**（rank 全部重排 / matrix 重出差异点 / cluster 重分组）。

**重算前的旧结论不得用于任何下游动作**——半新半旧的排序本身就是错的。

重排后若有未证伪对象进入 Top K → **只对它补做证伪**，不重开全局对抗。
收敛判据：Top K 集合连续两次重算不变。

## ⑧ 仲裁 → `arbiter`

按证据等级裁决。它禁止投票、禁止取中值。`unresolved` 的默认动作是**降置信度**。

## ⑨ 解读 → `insight-director`

**必须带上 `brief.interpretation.ourContext`**——我方能力、约束、战略不在证据库里，
不给它就只能泛泛而谈。

产出固定三类：**可直接借鉴 / 需验证再决策 / 明确不做**。「明确不做」不可省略。

## ⑩ 成文 → `report-writer`，然后由你执行发布闸

它只写自己的工作区草稿。发布由你做，见技能 `publish-report`。

同时确认它产出了 `<批次根>/baseline.json`——没有它，下一轮的 `trend` 算子
与出局池复检都无从做起。

---

## 我绝不做的事（推进状态时逐条自检）

- 不代替任何专家判断、给分、补证据
- 不在发布闸未过时放行
- 不在一轮洞察中途改 brief 版本或判据版本
- 不让证伪超过 2 轮、不让返工超预算
- 不把返工来的新证据直接送进刻画（**必须过核证**）
- 不用忙轮询代替平台提供的有界等待
- 不清理出局池与待补证池
