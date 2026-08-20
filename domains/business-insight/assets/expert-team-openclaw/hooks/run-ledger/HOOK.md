---
name: run-ledger
description: "把专家团的阶段消息与命令事件写入 JSONL 台账，供批次复盘与成本归因"
metadata:
  { "openclaw": { "emoji": "📒", "events": ["message:sent", "command", "session:compact:before"], "requires": { "bins": ["node"] } } }
---

# run-ledger

把每次运行的关键事件落到 `~/.openclaw/logs/business-insight-ledger.jsonl`，用于：

- **批次复盘**：哪个阶段跑了几轮、哪个专家被派发了多少次
- **成本归因**：定位 `data-collector` 的 fan-out 是否失控
- **对抗轮次审计**：确认 P5 确实止于 2 轮（编排层的硬上限是否真的生效）
- **压缩前留痕**：`session:compact:before` 时记录一笔，避免长批次被压缩后无法回溯

**本 hook 不承担闸门职责**，只记录。台账是事后审计材料，不是准入控制。
