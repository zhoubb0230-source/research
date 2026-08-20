# 🎯 首席洞察专家 · OpenClaw 装配

| | |
|---|---|
| agentId | `insight-director` |
| 动作 | ⑨ 解读 |
| 模型 | **fable-5** |
| thinking | **max** |
| 人格与技能正本 | [`../../../expert-team/experts/insight-director/`](../../../expert-team/experts/insight-director/) |
| 工作区 | `<WORKSPACE_ROOT>/insight-director`（由 `install.sh` 生成） |

## 本目录负责什么

只负责这位专家在 OpenClaw 上的 **T1 配置片段**（`entry.json5`）。
人格（`IDENTITY`/`SOUL`/`AGENTS`）与技能在正本目录里，本目录不复制它们。

## 这位专家的关键 T1 约束

| 意图 | OpenClaw 字段 |
|---|---|
| **完全剥夺联网** | 让「禁止引入新的事实性数字」从纪律变成机制 |
| max 档 | 解读是全流程唯一被允许越过证据边界的动作 |

## 怎么确认它装对了

产出侧的验收在正本的 `README.md` 里。配置侧只查两条：

```bash
# 1. 该 agent 的有效工具表是否与 entry.json5 一致
openclaw agents list
# 在它的会话里跑 /tools

# 2. 它是否只作为子 Agent 存在（bindings 里不该有它）
grep -c '"insight-director"' <生成的 openclaw.json 里的 bindings 段)   # 期望 0
```
