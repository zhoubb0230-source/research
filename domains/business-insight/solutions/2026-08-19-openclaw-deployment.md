---
id: business-insight-solution-0003
title: 业务洞察专家团的 OpenClaw 落地方案
domain: business-insight
type: solution
status: draft
created: 2026-08-19
updated: 2026-08-19
tags: [landing, multi-agent, orchestration, guardrail, anti-hallucination, architecture]
vendors: [openclaw, claude-opus-5, claude-sonnet-5, claude-fable-5, claude-haiku-4-5]
related: [business-insight-solution-0001, business-insight-solution-0002]
summary: 钩子不能阻断，闸门改放进唯一发布通道；派发深度必须设2，红队隔离由平台保证
---

# 业务洞察专家团的 OpenClaw 落地方案

> **面向**：把 `business-insight-solution-0001` 的平台中立设计部署到 OpenClaw
> **交付**：`../assets/expert-team-openclaw/`，含配置、12 角色装配元数据、安装脚本、发布闸、两个钩子与总调度运行手册
> **标记约定**：【设计】设计主张；【判断】推断；【待校验】依据文档推断但缺明确示例，上线前必须用 `openclaw config schema` 核对
> **状态说明**：`draft`。配置未在真实 OpenClaw gateway 上启动过；`install.sh`、`verify_report.py`、`publish-report.sh` 已在本仓库环境实测通过。待校验项清单见 `../assets/expert-team-openclaw/OPENCLAW-NOTES.md` §5。

## TL;DR

- **OpenClaw 能承载这套专家团，但原方案的第三道闸必须换落点。** OpenClaw 的 internal hooks 明确没有 deny/cancel 语义——把校验挂在钩子上，结果是"记录了违规但照样发布"，比没有闸更危险。
- **改法：闸门放进「发布」这个动作本身。** 报告生成专家 `sandbox: all` 写不到发布目录、`tools.deny: ["exec"]` 执行不了命令，唯一入口是总调度执行的 `publish-report.sh`，脚本内部跑数字校验，不过则不落盘。**这比原设计更强——不是"有人拦着"，是"根本没有第二条路"。**
- **`maxSpawnDepth` 必须设为 2。** 默认值 1 时 depth-1 是叶子、拿不到 `sessions_spawn`，数据采集专家无法 fan-out。
- **派发白名单必须显式配。** 默认只有请求方自己能被派发，不配 `allowAgents` 总调度谁也派不动。
- **红队的异源隔离由平台保证。** spawn 参数 `context: "isolated"` 给干净 transcript，不再依赖提示词自觉——这一项比原设计更可靠。

---

## 1. 角色命名与映射

12 个角色全部改为业务可读的中文名，agentId 用对应英文短名。

| agentId | 角色 | 原编号 | 模型 | thinking | 阶段 |
|---|---|---|---|---|---|
| `chief-coordinator` | 🧭 洞察总调度 | G1 | opus-5 | high | P0–P9 |
| `rubric-owner` | 📐 口径定义专家 | G2 | opus-5 | high | P0 |
| `opportunity-scanner` | 🔭 机会枚举专家 | S1 | opus-5 | medium | P1 |
| `data-collector` | 🔍 数据采集专家 | S2 | sonnet-5 | medium | P3 P7 |
| `industry-analyst` | 📊 产业分析专家 | S3 | opus-5 | high | P4 P7 |
| `techchain-analyst` | ⚙️ 技术链分析专家 | S4 | opus-5 | high | P4 P7 |
| `red-team-challenger` | 🥊 质疑审查专家 | C1 | fable-5 | high | P5 P7 |
| `fact-verifier` | ✅ 数据核证专家 | C2 | sonnet-5 | medium | P3 P7 |
| `compliance-officer` | 🛡️ 合规管制专家 | C3 | opus-5 | high | P2 P4 P7 |
| `arbiter` | ⚖️ 争议仲裁专家 | A1 | opus-5 | high | P6 P7 |
| `insight-director` | 🎯 首席洞察专家 | A2 | fable-5 | high | P8 |
| `report-writer` | 📝 报告生成专家 | A3 | haiku-4-5 | low | P8 |

只有洞察总调度绑定人类通道，其余 11 位仅作为子 Agent 被派发。

## 2. 派发拓扑

```
                    人类通道
                       │  bindings: chief-coordinator
                       ▼
       depth 0   🧭 洞察总调度（main agent）
                       │  sessions_spawn(agentId=..., context="isolated")
                       │  ↓ 派发后立即 sessions_yield 等待 announce
       ┌───────────────┼────────────────────────────────────┐
       ▼               ▼                                    ▼
depth 1  📐 口径  🔭 枚举  🔍 采集  📊 产业  ⚙️ 技术链  🥊 质疑
         ✅ 核证  🛡️ 合规  ⚖️ 仲裁  🎯 洞察   📝 报告
                       │
                       │  仅数据采集专家可再派（allowAgents 只含自己）
                       ▼
       depth 2   🔍 采集工蜂 ×N（叶子，无 session 工具）
```

**关键约束【设计】**：
- `maxSpawnDepth: 2` —— depth-1 只有在该值 ≥2 时才被授予 `sessions_spawn`
- `requireAgentId: true` —— 禁止不指名的模糊派发
- `context: "isolated"` —— 所有派发一律隔离，质疑审查专家尤其不可用 `fork`
- 用 `sessions_yield` 等结果，**禁止轮询循环**（官方明确要求）

## 3. 三道防编造闸在 OpenClaw 上的落点

| 闸 | 原设计 | OpenClaw 落点 | 是否降级 |
|---|---|---|---|
| 一 · 产出侧 | schema 强制数值绑定 `evidence_ref` | 工作区 `AGENTS.md` 内联 schema 契约 + 总调度做 schema 校验 | ⚠️ 由平台强制降为流程强制 |
| 二 · 核证侧 | 核证专家回源比对 | 数据核证专家（角色不变） | ✅ 不变 |
| 三 · 渲染侧 | **可阻断的钩子** | **唯一发布通道内含校验** | ✅ **增强** |

### 第三道闸的重构【设计】

```
📝 报告生成专家  sandbox: all      →  只能写自己的工作区
                tools.deny: exec  →  无法自行执行命令绕过
                       │
                       ▼  草稿路径回报给总调度
🧭 洞察总调度   bin/publish-report.sh <草稿> <证据库> <发布目录>
                       │
                       ├─ python3 verify_report.py  →  exit 0  →  cp 到发布目录 ✅
                       └─                              exit 1  →  不落盘，报违规 ❌
```

脚本已实测：合规草稿落盘、违规草稿被拦且发布目录保持干净。

**这道闸没有旁路。** 违规的正确处置是回 P3 补证，不是改报告措辞绕过，不是手工复制文件。

## 4. 与原方案的差异汇总

| # | 原方案 | OpenClaw 版 | 原因 |
|---|---|---|---|
| 1 | 渲染前阻断式钩子 | 唯一发布通道内含校验 | hooks 无 deny/cancel 语义 |
| 2 | 阶段硬门由编排引擎强制 | 由总调度按 playbook 执行 | 无原生阶段网关，**本方案最薄的一环**，见 §5 |
| 3 | effort `xhigh` / `max` | `thinkingDefault: xhigh` / `max` | ~~OpenClaw 无 xhigh/max 档~~ **已更正：有。** 见下方修订记录 |
| 4 | 红队"应当"异源 | `context: "isolated"` 平台保证 | 平台能力更强，升级 |
| 5 | 角色编号 S1/C1/A1 | 中文角色名 + 英文 agentId | 业务可读性 |
| 6 | 提示词各自维护 | `install.py` 从 `expert-team/experts/` 装配工作区 | 消除正副本漂移 |

## 5. 已知风险

| 风险 | 影响 | 缓解 |
|---|---|---|
| **阶段硬门依赖总调度自觉** | 可能跳阶段、超轮次 | `run-ledger` 台账事后审计；P0/P9 人工签署；最致命的数字校验已落到机制上 |
| thinking 降档 | 分析与对抗深度低于原设计 | 改 `adaptive`；任务描述里要求逐项作答；质疑审查专家已用 fable-5 |
| 配置字段形态未经实机验证 | 启动失败或字段被忽略 | `OPENCLAW-NOTES.md` §5 列了 7 项待校验，`install.sh` 预演模式不改动线上配置 |
| 总调度引导文件接近单文件上限 | 超 20000 字符会被静默截断，先掉的是文件末尾 | 已实测约 18 KB；`bootstrap-guardrails` hook 作第二重保险 |
| `maxConcurrent: 12` 可能撞模型速率限制 | 批量取证阶段大面积失败 | 首轮按实测回调 |

## 6. 落地路径

| 阶段 | 目标 | 验收 |
|---|---|---|
| D0 校验 | 配置字段形态核对 | `openclaw config schema` 逐项比对 `OPENCLAW-NOTES.md` §5 的 7 项 |
| D1 空跑 | 12 个 agent 能被正确派发 | 总调度收到 P0 后派发口径定义专家，而不是自己写 rubric |
| D2 单机会 | 1 个已知机会端到端 | 报告通过发布闸；台账显示 P5 确实止于 2 轮 |
| D3 小批 | 30–50 候选跑完 P1–P6 | 抽查 10 个出局机会无误杀；抽查 10 个数字全部可回源 |
| D4 全量 | 150–300 候选 | 见 solution-0001 §7 |

**D0 不能跳。** 字段形态错了会静默失效——被忽略的字段不报错，只是不生效，而 `allowAgents` 或 `maxSpawnDepth` 失效会让整个派发拓扑塌成单 agent。

## 7. 开放问题

| 问题 | 阻塞什么 | 决策人 |
|---|---|---|
| 通道与账号（`<CHANNEL>` / `<ACCOUNT_ID>`） | 配置无法上线 | 平台侧 |
| provider 命名是否为 `anthropic` | 模型解析 | 平台侧 |
| `maxConcurrent` 实际可用值 | 取证阶段吞吐 | 首轮实测 |
| 阶段硬门是否需要外部编排器兜底 | §5 第一条风险 | 架构侧；若不可接受，考虑 solution-0001 §6.3 的 BPMN 或 LangGraph 方案 |

## 参考资料

OpenClaw 官方文档（源文件位于 `github.com/openclaw/openclaw` 的 `docs/` 目录），查阅日期 2026-08-19：

1. [Configuration — agents](https://docs.openclaw.ai/gateway/config-agents)（访问日期 2026-08-19）
2. [Sub-agents](https://docs.openclaw.ai/tools/subagents)（访问日期 2026-08-19）
3. [Multi-agent routing](https://docs.openclaw.ai/concepts/multi-agent)（访问日期 2026-08-19）
4. [Configuration reference](https://docs.openclaw.ai/gateway/configuration-reference)（访问日期 2026-08-19）
5. [Hooks](https://docs.openclaw.ai/automation/hooks)（访问日期 2026-08-19）

模型档位与价目口径来自 Claude API 官方模型表（口径日期 2026-06-24）。

---

## 修订记录（2026-08-20）

本方案的交付件已按 `business-insight-solution-0006` 重建，三处结论经查官方文档后**不成立**：

| 原文 | 实际 | 影响 |
|---|---|---|
| `thinkingDefault` 无 `xhigh` / `max` 档 | **有。** 合法取值 `off \| minimal \| low \| medium \| high \| xhigh \| adaptive \| max` | 质疑审查专家与首席洞察专家恢复 `max`，**无精度损失** |
| `entries.*.model` 形态不确定 | 字符串形态与 `{ primary, fallbacks }` 均合法；字符串 = 严格无 fallback | 12 位统一用字符串形态 |
| `tools.deny` 的合法工具名未穷举 | 文档的访问档位示例给出了实际工具名 | 工具面从"只敢 deny 一个"变成逐角色可编排 |

另有一处度量错误：原文说总调度的 `AGENTS.md`「约 18 KB，逼近 20000 上限」——
那是拿 UTF-8 **字节数**比一个**字符数**上限。实测旧装配 7824 字符，余量充足。

**结论未变的部分**：钩子无 deny/cancel 语义、闸门必须放进唯一发布通道、
派发深度必须设 2、红队隔离由 `context: "isolated"` 保证——这四条经复核仍然成立。

交付件现状见 `../assets/expert-team-openclaw/README.md` 与 `OPENCLAW-NOTES.md`。

