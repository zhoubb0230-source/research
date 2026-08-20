# 📝 报告生成专家 · OpenClaw 装配

| | |
|---|---|
| agentId | `report-writer` |
| 动作 | ⑩ 成文 |
| 模型 | haiku-4-5 |
| thinking | low |
| 人格与技能正本 | [`../../../expert-team/experts/report-writer/`](../../../expert-team/experts/report-writer/) |
| 工作区 | `<WORKSPACE_ROOT>/report-writer`（由 `install.sh` 生成） |

## 本目录负责什么

只负责这位专家在 OpenClaw 上的 **T1 配置片段**（`entry.json5`）。
人格（`IDENTITY`/`SOUL`/`AGENTS`）与技能在正本目录里，本目录不复制它们。

## 这位专家的关键 T1 约束

| 意图 | OpenClaw 字段 |
|---|---|
| **关进沙箱** | `sandbox: { mode: "all", scope: "agent", workspaceAccess: "rw" }` —— 写不到发布目录 |
| **拒绝命令执行** | `tools.deny` 含 `exec` / `process` —— 无法自己跑脚本绕过 |
| **完全剥夺联网** | 它只做措辞改写，一个新数字都不许引入 |

## ⚠️ 沙箱有部署前置

`sandbox.mode: "all"` 需要一个沙箱后端（`docker` / `podman` / `openshell` / `ssh`），
默认是 `docker`。**没有可用后端时这一条会失效。**

没有 Docker 的降级方案与它弱在哪，见 [`../../OPENCLAW-NOTES.md`](../../OPENCLAW-NOTES.md) 的
「报告生成专家的沙箱」一节。**不要默认降级方案等价**——它不等价。

## 怎么确认它装对了

产出侧的验收在正本的 `README.md` 里。配置侧只查两条：

```bash
# 1. 该 agent 的有效工具表是否与 entry.json5 一致
openclaw agents list
# 在它的会话里跑 /tools

# 2. 它是否只作为子 Agent 存在（bindings 里不该有它）
grep -c '"report-writer"' <生成的 openclaw.json 里的 bindings 段)   # 期望 0
```
