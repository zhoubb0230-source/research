# ⚖️ 争议仲裁专家 · OpenClaw 装配

| | |
|---|---|
| agentId | `arbiter` |
| 动作 | ⑧ 仲裁 |
| 模型 | opus-5 |
| thinking | high |
| 人格与技能正本 | [`../../../expert-team/experts/arbiter/`](../../../expert-team/experts/arbiter/) |
| 工作区 | `<WORKSPACE_ROOT>/arbiter`（由 `install.sh` 生成） |

## 本目录负责什么

只负责这位专家在 OpenClaw 上的 **T1 配置片段**（`entry.json5`）。
人格（`IDENTITY`/`SOUL`/`AGENTS`）与技能在正本目录里，本目录不复制它们。

## 这位专家的关键 T1 约束

| 意图 | OpenClaw 字段 |
|---|---|
| **完全剥夺联网** | 让「禁止自行补证」从纪律变成机制 |

## 怎么确认它装对了

产出侧的验收在正本的 `README.md` 里。配置侧只查两条：

```bash
# 1. 该 agent 的有效工具表是否与 entry.json5 一致
openclaw agents list
# 在它的会话里跑 /tools

# 2. 它是否只作为子 Agent 存在（bindings 里不该有它）
grep -c '"arbiter"' <生成的 openclaw.json 里的 bindings 段)   # 期望 0
```
