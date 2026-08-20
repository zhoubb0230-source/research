---
id: business-insight-solution-0005
title: 洞察服务的 DeepSeek Harness 试跑方案
domain: business-insight
type: solution
status: draft
created: 2026-08-19
updated: 2026-08-19
tags: [landing, multi-agent, orchestration, guardrail, anti-hallucination]
vendors: [deepseek-harness]
related: [business-insight-solution-0001, business-insight-solution-0003, business-insight-solution-0004]
summary: 角色定义走 skills 而非配置，把唯一形状未确认的部分隔离到一个可弃文件
---

# 洞察服务的 DeepSeek Harness 试跑方案

> **面向**：把 `business-insight-solution-0004` 的十动作骨架落到本地 dsh 上真实试跑
> **交付**：`../assets/expert-team-dsh/`
> **状态说明**：`draft`。`install.sh` 与发布闸已在本仓库环境实测；**配置覆盖的 YAML 形状未经实机验证**，
> 待校验项见 `../assets/expert-team-dsh/DSH-NOTES.md` §5。

## TL;DR

- **角色定义走 skills，不走配置。** dsh 的 skill 格式与发现规则是文档明确的，
  `cordis.patch.yml` 的 verbatim 形状不是。把 12 个角色放进 `.dsh/skills/`（项目级最高优先档），
  意味着**即使配置部分全要改，角色部分照常可用**。
- **不确定性被隔离到一个文件。** 整个交付包里只有 `cordis.patch.yml` 形状待校验，其余全部基于文档明确的事实。
- **dsh 的 pre-step 钩子可以拒绝**（与 OpenClaw 相反），但闸门仍放在脚本里——
  校验逻辑不该随平台重写，且脚本不会被说服。
- **角色命名已泛化**，对齐通用骨架。`expert-team-openclaw` 仍用旧名，尚未同步。
- **effort 无 medium 档**，原 medium 的四个角色落到 `low`；对抗与解读拿 `max`。

## 1. 十动作 ↔ 12 专家

| 动作 | 专家 | agentId | effort |
|---|---|---|---|
| 全程 | 洞察总调度 | `chief-coordinator` | high |
| ① 界定（含分诊） | 洞察规划专家 | `insight-planner` | high |
| ② 枚举 | 范围界定专家 | `scope-definer` | low |
| ③ 取证 | 数据采集专家 | `data-collector` | low |
| ④ 核证 | 数据核证专家 | `fact-verifier` | low |
| ⑤ 刻画 ⑥ 聚合 | 对比分析专家 | `comparative-analyst` | high |
| ⑤ 刻画（领域维度） | 领域分析专家（可选） | `domain-analyst` | high |
| 闸门 + 合规维度 | 合规审查专家（可选） | `compliance-reviewer` | high |
| ⑦ 证伪 | 质疑审查专家 | `red-team-challenger` | **max** |
| ⑧ 仲裁 | 争议仲裁专家 | `arbiter` | high |
| ⑨ 解读 | 首席洞察专家 | `insight-director` | **max** |
| ⑩ 成文 | 报告生成专家 | `report-writer` | low |

最难的两个判断——推翻结论、解读意味着什么——拿最高算力档【设计】。

## 2. 核心决策：把不确定性隔离

文档给了各插件的 config 字段（verbatim TypeScript 接口），但**没有给 `cordis.patch.yml` 本身的示例**。
面对这种局部不确定，两种做法：

| 做法 | 后果 |
|---|---|
| 猜一个形状，把所有东西都塞进配置 | 猜错则整包不可用，且**不报错只是静默失效** |
| **把能走确定通道的都走确定通道，不确定的隔离成一个可弃文件** | 猜错只影响那一个文件 |

选后者。具体：

```
角色提示词  →  .dsh/skills/<agentId>/SKILL.md    格式与发现规则文档明确 ✓
判据与口径  →  每批次的 brief.json               平台无关 ✓
发布闸      →  bin/publish-report.sh             脚本，平台无关 ✓
────────────────────────────────────────────────────────────
仅剩：provider 默认值 + agent id 名单  →  cordis.patch.yml  形状待校验 ⚠
```

**这是面对文档缺口时的通用做法**，不只适用于 dsh：先问"哪些部分不依赖这个缺口"，
把它们迁到确定通道上，让缺口的爆炸半径最小【设计】。

## 3. 闸门为什么仍在脚本里

dsh 的 `agent/pre-step` 决策是 authoritative 的——**能拒绝**，这点与 OpenClaw 明确相反
（后者的钩子无 deny/cancel 语义）。理论上可以把数字校验挂上去。没有这么做，三个理由：

1. pre-step 拒绝的是一个 **step**，不是一次文件写入；报告落盘可能发生在工具执行内部
2. **脚本平台无关**：同一份 `verify_report.py`、同一套夹具、同一个退出码，在任何平台上都一样
3. 钩子里跑模型判断就又回到了"模型守门"，那正是要避免的

pre-step 是**可选加固**，不是替代。要加就拦"写入发布目录"，不拦"渲染报告"。

## 4. 试跑该看什么

有五个参数是**猜的**，只有跑起来才知道：

| 观察点 | 取值 | 判定猜错的信号 |
|---|---|---|
| `rework.perSubject` | 2 | 大量对象耗尽预算仍未解决 → 调高 |
| `rework.topKBuffer` | 3 | 重排后仍频繁有未证伪对象进 Top K → 调高 |
| 单调收敛判据 | 每次返工须产新证据 | 出现"补证失败但其实只是慢了一步"的误判 |
| 枚举 effort | `low` | 人工抽查出局池，看有无误杀 |
| `maxParallelToolCalls` | 8 | 撞速率限制 |

两个**结构性**问题也要看：

- **⑨ 解读是否真的产出了可用的启示**，还是又退化成套话——这是新加的动作，最需要验证
- **五条回边会不会震荡**，特别是 R2（证伪→取证）与 R3（刻画→聚合）连锁触发时

## 5. 建议的首个试跑需求

用 `landscape-survey` 预设（AI Coding 工具现状），不用 `opportunity-screening`。

**理由不是"另一个验证不了"**——两类洞察的**系统质量都当场可测**（八项检验见 `../assets/insight-service/acceptance.md`）。
要等几个月的是「这个机会最终赚不赚钱」，那是结论验证，不是系统验收，两者不能混。

真实依据是这四条：

| 依据 | 说明 |
|---|---|
| **证据可得性** | `opportunity-screening` 的 C 维标了 `na_hotspot`——设备级细分市场规模公开渠道常查不到。首轮撞上大面积 NA，测出来的是"数据拿不到"而不是"系统好不好" |
| **成本** | 候选 250 个 vs 40 个，取证量差一个数量级 |
| **有无一手证据可对照** | `landscape-survey` 的 `directVerification.available=true`，能装上跑一下，判断有没有编造最容易 |
| **判错代价** | 工具现状报告错了改一版；产业机会榜单若有编造数据流到战略汇报，代价高得多 |

这是成本与风险的权衡。产业机会筛选反而多一个验收优势：若内部已有人工机会评估，
可直接比对 Top N 重合度（`solution-0001` 落地路径 P3），同样当场可做。

## 6. 已知不一致

**`expert-team-openclaw` 与本包角色命名不一致。** 本包已泛化对齐通用骨架
（口径定义→洞察规划、机会枚举→范围界定、产业分析→对比分析、技术链→领域分析、合规降为可选，
首席洞察专家职责从"只验收"扩为"产出解读 + 验收"），OpenClaw 包仍是旧名。

以本包命名为准。OpenClaw 包的同步待办。

## 7. 开放问题

| 问题 | 阻塞什么 | 决策人 |
|---|---|---|
| `cordis.patch.yml` 形状 | 配置层生效与否 | 试跑前 `--dump-config` 自查 |
| `AgentOptions` 完整字段 | 能否在配置层硬约束 per-agent model/effort | 同上 |
| 枚举用 `low` 是否够 | 覆盖率 | 首轮人工抽查出局池 |
| OpenClaw 包何时同步 | 两包一致性 | 待本包试跑结论确定后再同步，避免同步两次 |

## 参考资料

1. [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)（访问日期 2026-08-19）
2. `docs/config-catalog.md`、`docs/architecture.md`、`docs/agent-lifecycle.md`、
   `docs/subsystems/agent-team.md`、`docs/subsystems/skills.md`（同上访问日期）

完整事实清单与四项待校验见 `../assets/expert-team-dsh/DSH-NOTES.md`。
