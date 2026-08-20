# 🛡️ 合规审查专家 · dsh 装配

| | |
|---|---|
| name / agentId | `compliance-reviewer` |
| 动作 | 闸门 + 合规维度 |
| provider 路由 | `deepseek-high` |
| 人格与技能正本 | [`../../../expert-team/experts/compliance-reviewer/`](../../../expert-team/experts/compliance-reviewer/) |
| 可选 | **是** —— 不满足条件时不要建它 |

## 本目录负责什么

只负责这位专家在 dsh 上的 **T1 装配实参**（`spawn.json`）。
人格（`IDENTITY`/`SOUL`/`AGENTS`）与技能在正本目录里，本目录不复制它们。

## spawnTeammate 实参

```jsonc
{
  "name":        "compliance-reviewer",          // 不可变，且名字永不复用（含建失败的）
  "description": "🛡️ 合规审查专家 —— 负责骨架的 闸门 + 合规维度",
  "prompt":      <.dsh/PROMPTS/compliance-reviewer.md 正文>,   // ← 人格在这里绑上去
  "context":     "fresh",             // fresh = 无父历史种子（不是 "isolated"）
  "provider":    "deepseek-high"
}
```

**`context` 的合法取值是 `fresh` | `fork`，不是 `isolated`。**
`fresh` 表示这个队友没有父会话的历史种子；`fork` 会把 Lead 的已完成轮次前缀复制过来。
本方案全部用 `fresh`。

## 装配理由

可选。它是唯一【应该】联网的分析角色 —— 在 dsh 上这一点是自动满足的，因为全队都能联网。

## 在 dsh 上落不下去的约束

`../../../expert-team/experts/compliance-reviewer/expert.yaml` 里的 `tools.need` / `tools.deny`
**在 dsh 上无法逐队友生效**——队友共用 Lead 的 preset 组合与 cwd。
它们退化成 `SOUL.md` / `AGENTS.md` 里的承诺。

验收时请如实按"承诺"检验（抽查产出里有没有越界痕迹），
不要按"机制"检验（"配置里禁了所以不可能发生"在这里不成立）。
详见 [`../../DSH-NOTES.md`](../../DSH-NOTES.md) §4。
