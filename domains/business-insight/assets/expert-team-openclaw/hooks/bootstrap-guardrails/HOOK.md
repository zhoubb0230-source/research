---
name: bootstrap-guardrails
description: "agent:bootstrap 时把全角色共用护栏追加进引导上下文，保证 12 个专家的防编造条款始终在位"
metadata:
  { "openclaw": { "emoji": "🧱", "events": ["agent:bootstrap"], "requires": { "bins": ["node"] } } }
---

# bootstrap-guardrails

共用护栏（`assets/expert-team/experts/_shared/GUARDRAILS.md`）已经由 `install.py` 内联进每个
agent 工作区的 `SOUL.md`。本 hook 是**第二重保险**：万一某个 agent 的工作区被手工改动或
bootstrap 截断（`bootstrapMaxChars` 默认 20000 字符），护栏仍会被重新注入。

**本 hook 不承担闸门职责。** OpenClaw 的 internal hooks 没有 deny/cancel 语义，
无法阻断任何动作——它只能注入与记录。真正的阻断闸是 `bin/publish-report.sh`。

配置：

```json
{ "hooks": { "internal": { "entries": {
  "bootstrap-guardrails": { "enabled": true, "env": { "GUARDRAILS_PATH": "/abs/path/expert-team/experts/_shared/GUARDRAILS.md" } }
} } } }
```
