# 写作与索引维护规范

## 1. 文件命名

```
domains/<domain-id>/<type-dir>/YYYY-MM-DD-<slug>.md
```

- 日期为**首次创建日期**，后续修订不改文件名，只改 frontmatter 的 `updated`。
- `slug`：小写英文短横线，3–6 个词，能独立表意。
  - 好：`2026-08-05-multi-agent-orchestration-landscape.md`
  - 差：`2026-08-05-notes.md`、`2026-08-05-调研1.md`
- `vendors/` 下的档案不带日期：`dify.md`、`cursor.md`，一个产品一个文件，长期维护。

## 2. Frontmatter（必填）

所有正文文件顶部必须是 YAML frontmatter。字段固定顺序，便于 `Grep` 精确匹配（如 `^status: stable`）。

```yaml
---
id: agent-platform-insight-0001      # <domain>-<type>-<四位序号>，全局唯一，不复用
title: 多智能体编排的业界技术路线
domain: agent-platform               # 见 docs/taxonomy.md §1
type: insight                        # insight | solution | vendor
status: draft                        # draft | review | stable | archived
created: 2026-08-05
updated: 2026-08-05
tags: [multi-agent, orchestration, tech-route]
vendors: [langgraph, dify, autogen]
related: [agent-platform-solution-0001]
summary: 一句话结论，≤60 字，索引直接复用，不要写"本文介绍…"
---
```

字段说明：

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | 序号在同一 domain+type 内递增，删除条目后序号不回收 |
| `summary` | 是 | 写**结论**而非主题，索引可读性全靠它 |
| `tags` / `vendors` | 是 | 只用 `docs/taxonomy.md` 已登记的词；新词先登记 |
| `related` | 否 | 填其他条目的 `id`，用于跨领域串联 |
| `owner` | 否 | 多人协作时填负责人 |

## 3. 正文结构

统一从 `templates/` 复制，不要自创骨架。共同要求：

- 首屏必须是 **TL;DR / 核心结论**，3–5 条要点，让人不读全文也能用。
- **事实与判断分离**：事实段落给来源链接与访问日期；判断段落显式标注「判断」「假设」。
- 一篇一主题，正文建议 ≤ 500 行。超长按子主题拆分，用 `related` 互链。
- 引用来源格式：`[标题](URL)（访问日期 2026-08-05）`。
- 图片/PDF/数据放同领域 `assets/`，命名 `<slug>-<序号>.<ext>`，正文用相对路径。

## 4. 索引维护（每次改动必做）

### 4.1 领域索引 `domains/<domain-id>/INDEX.md`

按类型分表，一条一行：

```markdown
| ID | 标题 | 摘要 | 标签 | 状态 | 更新 |
|---|---|---|---|---|---|
| [agent-platform-insight-0001](insights/2026-08-05-xxx.md) | 多智能体编排技术路线 | 一句话结论 | multi-agent, tech-route | stable | 2026-08-05 |
```

摘要列直接复制 frontmatter 的 `summary`，两处必须一致。

### 4.2 全局索引 `INDEX.md`

- 更新对应领域的「条目数」。
- 在「最近更新」表顶部插入一行，保留最近 20 条。

### 4.3 归档

条目过时：`status` 改 `archived`，正文顶部加一行 `> 已归档（2026-08-05）：<失效原因>`，索引行状态同步改为 `archived`，**不删除文件**。

## 5. 检索约定（写给未来的自己）

优先用 frontmatter 字段检索，命中率高且 token 省：

| 目的 | 检索方式 |
|---|---|
| 找某领域全部条目 | 读 `domains/<id>/INDEX.md` |
| 找某个产品的所有材料 | `Grep` 模式 `^vendors:.*\bdify\b`，限定 `domains/**/*.md` |
| 找某主题 | `Grep` 模式 `^tags:.*multi-agent` |
| 找可对外引用的结论 | `Grep` 模式 `^status: stable` |
| 找最近更新 | 读 `INDEX.md` 的「最近更新」表 |

不要为了找结论而通读整个目录；不要对全库做无 glob 限制的正文关键词搜索。

## 6. 提交规范

```
<type>(<domain>): <做了什么>
```

`type` 取 `docs`（新增/修改调研内容）、`chore`（骨架、模板、索引维护）、`refactor`（结构调整）。

示例：
- `docs(agent-platform): 新增多智能体编排技术路线洞察`
- `docs(ai-coding): 更新 cursor 产品档案至 2026-08 版本`
- `chore: 重建两级索引`
