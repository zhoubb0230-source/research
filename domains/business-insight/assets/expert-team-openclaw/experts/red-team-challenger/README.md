# 🥊 质疑审查专家 · OpenClaw 装配

| | |
|---|---|
| agentId | `red-team-challenger` |
| 动作 | ⑦ 证伪 |
| 模型 | **fable-5** |
| thinking | **max** |
| 人格与技能正本 | [`../../../expert-team/experts/red-team-challenger/`](../../../expert-team/experts/red-team-challenger/) |
| 工作区 | `<WORKSPACE_ROOT>/red-team-challenger`（由 `install.sh` 生成） |

## 本目录负责什么

只负责这位专家在 OpenClaw 上的 **T1 配置片段**（`entry.json5`）。
人格（`IDENTITY`/`SOUL`/`AGENTS`）与技能在正本目录里，本目录不复制它们。

## 这位专家的关键 T1 约束

| 意图 | OpenClaw 字段 |
|---|---|
| **异源**：模型必须与 comparative-analyst / domain-analyst 不同 | `model: "anthropic/claude-fable-5"` vs 它们的 `opus-5` |
| **上下文隔离** | 派发时 `context: "isolated"`（OpenClaw 的默认值，运行手册仍显式传） |
| **看不到推理过程** | 总调度的派发实参里只放结论与证据 —— 这一条落在派发参数上，不在 entry 里 |

## 三条约束落在三个不同的地方

| 约束 | 落在哪 | 谁保证 |
|---|---|---|
| 异源模型 | 本目录的 `entry.json5` | 配置层 |
| 干净 transcript | 派发实参 `context: "isolated"` | 平台 |
| 看不到刻画的推理过程 | 总调度只传结论与证据 | **运行手册（T2/T3）** |

第三条**没有配置字段可落**——OpenClaw 无法表达"这个子会话不许读某个文件的某个字段"。
它是本方案里为数不多只能靠约定保证的约束，验收时要专门查。

## 怎么确认它装对了

产出侧的验收在正本的 `README.md` 里。配置侧只查两条：

```bash
# 1. 该 agent 的有效工具表是否与 entry.json5 一致
openclaw agents list
# 在它的会话里跑 /tools

# 2. 它是否只作为子 Agent 存在（bindings 里不该有它）
grep -c '"red-team-challenger"' <生成的 openclaw.json 里的 bindings 段)   # 期望 0
```
