# 🧭 洞察总调度 · dsh 装配

| | |
|---|---|
| name / agentId | `chief-coordinator` |
| 动作 | 全程 |
| provider 路由 | `deepseek-high` |
| 人格与技能正本 | [`../../../expert-team/experts/chief-coordinator/`](../../../expert-team/experts/chief-coordinator/) |

## 本目录负责什么

只负责这位专家在 dsh 上的 **T1 装配实参**（`spawn.json`）。
人格（`IDENTITY`/`SOUL`/`AGENTS`）与技能在正本目录里，本目录不复制它们。

## 它不是 spawnTeammate 建出来的

Lead 由 `agent-loop.agents[]` 在**进程启动时**创建。
它的人格通过项目 `AGENTS.md`（全队共用层）+ 它自己的会话首条消息注入
—— `install.py --write` 会把它的人格写成 `.dsh/PROMPTS/chief-coordinator.md`，
第一次对它说话时把这份正文贴进去，或用 `--seed` 让脚本替你拼好。

**⚠️ 这是 dsh 与 OpenClaw 的一处实质差异**：OpenClaw 的 Lead 有自己的工作区文件，
每轮自动注入；dsh 的 Lead 人格只在会话开头出现一次，长会话经过压缩后可能淡出。
所以它的不可违反规则（证伪 2 轮上限、判据版本不变、发布闸无旁路）
**同时**写进了全队共用的 `AGENTS.md` —— 那一层每轮都在。

## 装配理由

Team Lead。由 agent-loop 在启动时创建，**不通过 spawnTeammate**。本目录的 spawn.json 只记录它的路由选择。

## 在 dsh 上落不下去的约束

`../../../expert-team/experts/chief-coordinator/expert.yaml` 里的 `tools.need` / `tools.deny`
**在 dsh 上无法逐队友生效**——队友共用 Lead 的 preset 组合与 cwd。
它们退化成 `SOUL.md` / `AGENTS.md` 里的承诺。

验收时请如实按"承诺"检验（抽查产出里有没有越界痕迹），
不要按"机制"检验（"配置里禁了所以不可能发生"在这里不成立）。
详见 [`../../DSH-NOTES.md`](../../DSH-NOTES.md) §4。
