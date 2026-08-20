# ✅ 数据核证专家 · OpenClaw 装配

| | |
|---|---|
| agentId | `fact-verifier` |
| 动作 | ④ 核证 |
| 模型 | sonnet-5 |
| thinking | low |
| 人格与技能正本 | [`../../../expert-team/experts/fact-verifier/`](../../../expert-team/experts/fact-verifier/) |
| 工作区 | `<WORKSPACE_ROOT>/fact-verifier`（由 `install.sh` 生成） |

## 本目录负责什么

只负责这位专家在 OpenClaw 上的 **T1 配置片段**（`entry.json5`）。
人格（`IDENTITY`/`SOUL`/`AGENTS`）与技能在正本目录里，本目录不复制它们。

## 这位专家的关键 T1 约束

| 意图 | OpenClaw 字段 |
|---|---|
| 只回源，不另找来源 | `tools.deny: ["browser"]` —— 另找来源是取证，不是核证 |

## 怎么确认它装对了

产出侧的验收在正本的 `README.md` 里。配置侧只查两条：

```bash
# 1. 该 agent 的有效工具表是否与 entry.json5 一致
openclaw agents list
# 在它的会话里跑 /tools

# 2. 它是否只作为子 Agent 存在（bindings 里不该有它）
grep -c '"fact-verifier"' <生成的 openclaw.json 里的 bindings 段)   # 期望 0
```
