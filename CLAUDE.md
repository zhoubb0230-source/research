# CLAUDE.md

本仓库是 **AI 先进技术调研知识库**：沉淀业界洞察（Insight）与方案设计（Solution），供后续检索、复用、汇报。

本文件是给 Claude 的操作说明。**每次任务先读本文件 + `INDEX.md`，再按索引跳到具体文件，不要全库遍历或大范围 grep。**

## 1. 检索协议（最重要，直接影响 token 消耗）

按顺序执行，命中即停：

1. 读 `INDEX.md` —— 全局索引，列出所有领域及其条目摘要。
2. 读对应领域的 `domains/<domain-id>/INDEX.md` —— 领域内条目清单（一行一条，含摘要/标签/状态）。
3. 只打开索引里明确命中的 1–3 个正文文件。
4. 仍未命中，再用 `Grep` 检索 **frontmatter 字段**（如 `^tags:.*multi-agent`、`^vendors:.*dify`），而不是全文关键词。

禁止：为了找一个结论而 `Read` 整个 `domains/` 目录；对全库做无 glob 限制的正文 grep。

## 2. 目录结构

```
CLAUDE.md                     # 本文件：协作规范与检索协议
INDEX.md                      # 全局索引（一级入口）
docs/
  taxonomy.md                 # 分类体系、领域定义、标签词表
  conventions.md              # 命名、frontmatter、写作与索引维护规范
templates/
  insight.md                  # 业界洞察模板
  solution.md                 # 方案设计模板
  vendor.md                   # 产品/厂商档案模板
domains/
  agent-platform/             # 智能体平台
    INDEX.md
    insights/                 # 业界洞察：趋势、竞品格局、技术路线
    solutions/                # 方案设计：架构、选型、落地方案
    vendors/                  # 单个产品/厂商的事实性档案
    assets/                   # 图片、原始数据、导出文件
  ai-coding/                  # AI Coding 工具
    INDEX.md
    insights/
    solutions/
    vendors/
    assets/
```

新增领域时：在 `domains/` 下按同样结构建目录，登记到 `docs/taxonomy.md` 与 `INDEX.md`。

## 3. 三种内容类型

| 类型 | 目录 | 回答的问题 | 模板 |
|---|---|---|---|
| `insight` | `insights/` | 业界在做什么、怎么演进、谁领先 | `templates/insight.md` |
| `solution` | `solutions/` | 我们要做什么、怎么设计、如何落地 | `templates/solution.md` |
| `vendor` | `vendors/` | 某个产品/厂商的事实（能力、定价、架构） | `templates/vendor.md` |

判断规则：带主观判断与推荐 → `insight`；带自研设计与实施路径 → `solution`；纯事实卡片、被前两者反复引用 → `vendor`。

## 4. 写入规范（摘要，细则见 `docs/conventions.md`）

- 文件名：`YYYY-MM-DD-<slug>.md`，slug 用小写英文短横线。
- 每篇必须有 YAML frontmatter，字段见模板；`summary` 控制在 60 字内，索引直接复用。
- 一篇一主题，正文建议 ≤ 500 行；超长拆分并在 frontmatter 用 `related` 互链。
- 事实必须给来源（链接 + 访问日期）；推断与事实分段落写清楚。
- 图片、PDF、原始数据放 `assets/`，正文用相对路径引用。

## 5. 强制收尾动作

任何新增/修改/删除条目后，**必须同步更新两级索引**：

1. `domains/<domain-id>/INDEX.md` 的对应表格行；
2. `INDEX.md` 的领域条目数与"最近更新"。

未更新索引的改动视为未完成。

## 6. Git

- 开发分支：`claude/project-init-classification-tg7sfp`（除非另有指定）。
- 提交信息用中文祈使句，说明动了哪个领域/条目，例如：`docs(agent-platform): 新增 Dify 架构洞察`。
