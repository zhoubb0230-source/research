# 🧭 洞察总调度 · OpenClaw 装配

| | |
|---|---|
| 人格与技能正本 | [`../../../expert-team/experts/chief-coordinator/`](../../../expert-team/experts/chief-coordinator/) |
| 本目录负责 | 这位专家在 OpenClaw 上的 **T1 配置片段** |
| 工作区 | `<WORKSPACE_ROOT>/chief-coordinator`（由 `install.sh` 生成） |

## 这位专家的 T1 约束落在哪

| 意图（`expert.yaml`） | OpenClaw 字段 |
|---|---|
| 算力档 high | `thinkingDefault: "high"` |
| 唯一能执行发布脚本 | `tools.profile: "coding"`（含 `exec`），其余角色 deny `exec` |
| 不许联网 | `tools.deny: ["browser","web_search","web_fetch"]` |
| 可派发全部 11 位 | `subagents.allowAgents`（11 项） |
| 禁止模糊派发 | `subagents.requireAgentId: true` |
| 保有完整上下文 | `sandbox.mode: "off"`、`contextInjection: "always"` |

## 它是唯一绑定到人类通道的 agent

`bindings` 里只有它一条。其余 11 位仅作为 `sessions_spawn` 的目标存在，
人不直接对它们说话。见主配置 `../../openclaw.config.json5` 的 `bindings`。

## 派发时必须显式传的两个参数

OpenClaw 文档明确：`sessions_spawn.model` 与 `sessions_spawn.thinking` 的
**显式取值优先级最高**。而"用 `agentId` 派发时是否自动套用目标 agent 的
`model`/`thinkingDefault`"，文档没有给出无歧义的表述。

**所以运行手册要求每次派发都显式带上 `model` 与 `thinking`。**
这不是冗余——它把一处不确定性变成了确定性。取值见各专家的 `entry.json5`。
