---
id: ai-coding-vendor-0001
title: opencode
domain: ai-coding
type: vendor
status: stable
created: 2026-08-11
updated: 2026-08-11
tags: [cli-agent, coding-agent, platform-product, architecture]
vendors: [opencode]
related: [ai-coding-insight-0001, ai-coding-solution-0001]
summary: MIT 开源、模型中立的终端编码 Agent，客户端/服务端分离，是二次开发的主流内核
---

# opencode

> 事实性档案，长期维护。**只记录可核实的事实**，主观判断写进 insight 并用 `related` 互链。
> 信息核对日期：2026-08-11（对应上游 `dev` 分支 commit `d041eee`，发行版 v1.18.16）

## 速览

| 项 | 内容 |
|---|---|
| 厂商 | 原 SST（sst/opencode），当前仓库归属 `anomalyco/opencode` |
| 定位 | 开源终端 AI 编码 Agent；模型中立，客户端/服务端分离 |
| 当前版本 | v1.18.16（2026-08-10） |
| 开源 / 闭源 | 开源 |
| License | MIT |
| 仓库 | https://github.com/anomalyco/opencode （`sst/opencode` 仍可访问） |
| 官网 / 文档 | https://opencode.ai/docs |
| 社区规模 | GitHub 196k+ stars、25k+ forks |
| 客户端形态 | TUI、CLI（headless）、Desktop（beta，v2 已迁移完成）、Web、ACP、IDE 插件、SDK |

## 1. 核心能力

| 能力 | 支持情况 | 说明 |
|---|---|---|
| 多模型 / 多 Provider | ✅ | 基于 models.dev 的 provider 列表；支持自定义 `baseURL`/`apiKey`、Bedrock（region/profile/VPC endpoint）、本地模型 |
| 项目规则 | ✅ | `AGENTS.md`（项目 / 全局 `~/.config/opencode/AGENTS.md`），兼容 `CLAUDE.md` 与 `~/.claude/CLAUDE.md`；`instructions` 支持 glob 与远程 URL |
| Agent Skills | ✅ | `SKILL.md` 按需加载，兼容 `.claude/skills/`、`.agents/skills/` 与 `~/.config/opencode/skills/`；`skill` 工具 + 按名通配的权限控制 |
| 子智能体 | ✅ | primary / subagent 两类；内置 build、plan（primary）与 general、explore、scout（subagent）；`subagent_depth` 控制嵌套层数 |
| 自定义 Agent | ✅ | JSON 配置或 Markdown frontmatter（`model`/`prompt`/`temperature`/`top_p`/`steps`/`permission`/`mode`/`hidden`/`color`），`opencode agent create` 可交互生成 |
| 权限系统 | ✅ | `allow`/`ask`/`deny` 三态；键包括 `read`/`edit`/`glob`/`grep`/`list`/`bash`/`task`/`skill`/`lsp`/`webfetch`/`websearch`/`question`/`todowrite`/`external_directory`/`doom_loop`；支持通配模式、按 agent 覆盖、`--auto` 自动批准 |
| OS 级沙箱 | ❌ | 无内置沙箱；隔离需外部容器/VM 方案 |
| MCP | ✅ | 本地与远程 MCP server；`POST /mcp` 可运行时动态添加；权限按 `mymcp_*` 通配 |
| LSP | ✅ | 内置 LSP 集成；实验性 `lsp` 工具提供 goToDefinition / findReferences / hover / documentSymbol / workspaceSymbol / callHierarchy（需 `OPENCODE_EXPERIMENTAL_LSP_TOOL`） |
| 插件系统 | ✅ | JS/TS 模块，本地目录或 npm 包加载；可注册自定义工具 |
| 上下文压缩 | ✅ | `compaction.auto` / `prune` / `reserved`；`experimental.session.compacting` 钩子可注入或整体替换压缩提示词 |
| 快照 / 回滚 | ✅ | 内部 git 仓库记录变更，支持 revert/unrevert；可用 `snapshot: false` 关闭 |
| 跨会话记忆 | ❌ | 无内置长期记忆机制 |
| Headless / 脚本化 | ✅ | `opencode run`、`opencode serve`、`prompt_async`、`/session/:id/command` |
| Web 搜索 | ⚠️ | `websearch` 依赖 Exa（需 OpenCode provider 或 `OPENCODE_ENABLE_EXA`） |
| 代码仓集成 | ✅ | `opencode github install`、GitLab 集成 |
| 会话分享 | ✅ | `/share`，数据上传至 opencode.ai CDN；可设 `share: "disabled"` |
| 可观测性 | ⚠️ | 仅 `POST /log` 结构化日志与事件总线；**无内置 OpenTelemetry 导出** |

## 2. 技术架构

**客户端 / 服务端分离**是其最显著的结构特征。运行 `opencode` 时同时拉起一个本地 HTTP 服务与一个 TUI 客户端，TUI 只是众多客户端之一。

- **服务端**：负责 LLM 调用、工具执行、会话持久化、MCP 与 LSP 管理。暴露 OpenAPI 3.1 规范（`GET /doc`），并据此用 Stainless 生成 SDK。
- **通信**：HTTP REST + Server-Sent Events（`GET /event`，首个事件为 `server.connected`）。
- **接入面**：
  - `opencode serve` / `opencode web` 起独立服务端，`opencode attach <url>` 让 TUI 连接远程服务端；
  - `OPENCODE_SERVER_PASSWORD` 提供 HTTP Basic Auth；
  - `server.port` / `hostname` / `cors` / `mdns` 可配置，支持 mDNS 局域网发现；
  - `opencode acp` 以 JSON-RPC over stdio 提供 [Agent Client Protocol](https://agentclientprotocol.com) 接入（Zed、JetBrains、Avante.nvim、CodeCompanion.nvim）。
- **关键 API 面**：`/session`（创建/fork/abort/revert/diff/summarize/permissions）、`/session/:id/message`、`/session/:id/shell`、`/agent`、`/command`、`/config`（含 `PATCH`）、`/provider`、`/find`、`/mcp`、`/tui/*`（可远程驱动 TUI，IDE 插件即基于此）。

### 配置体系

配置为**合并**而非覆盖，优先级由低到高：

1. Remote config（`.well-known/opencode`，认证时拉取，作为组织默认值的**基线层**）
2. Global（`~/.config/opencode/opencode.json`）
3. `OPENCODE_CONFIG` 指定的自定义路径
4. Project（项目根 `opencode.json`）
5. `.opencode/` 目录（agents / commands / plugins / skills / tools / themes）
6. `OPENCODE_CONFIG_CONTENT`（内联）
7. **Managed 配置文件**：macOS `/Library/Application Support/opencode/`、Linux `/etc/opencode/`、Windows `%ProgramData%\opencode`
8. **macOS 托管偏好**（MDM 下发 `.mobileconfig`，`ai.opencode.managed` 域）— 最高优先级，用户不可覆盖

支持 `{env:VAR}` 与 `{file:path}` 变量替换。TUI 配置独立在 `tui.json`。`opencode debug config` 可查看解析后的最终配置。

### 插件机制

插件为导出插件函数的 JS/TS 模块，接收 `{ project, directory, worktree, client, $ }`，返回钩子对象。加载来源：`~/.config/opencode/plugins/`、`.opencode/plugins/`，以及 `plugin` 配置项声明的 npm 包（启动时用 Bun 安装并缓存到 `~/.cache/opencode/node_modules/`，因此可走企业私有 npm registry 的 `.npmrc`）。

可订阅事件：`command.executed`、`file.edited`、`file.watcher.updated`、`installation.updated`、`lsp.client.diagnostics`、`lsp.updated`、`message.*`、`permission.asked`、`permission.replied`、`server.connected`、`session.created/compacted/deleted/diff/error/idle/status/updated`、`todo.updated`、`shell.env`、`tool.execute.before`、`tool.execute.after`、`tui.prompt.append`、`tui.command.execute`、`tui.toast.show`，以及 `experimental.session.compacting`。

插件还可通过 `tool()` 注册自定义工具（同名时覆盖内置工具）。

### 策略（Policies，实验性）

`experimental.policies` 以 `{ effect, action, resource }` 三元组控制资源使用，当前仅支持 `provider.use`。支持通配符匹配、**后匹配优先**、全局配置优先于项目配置（防止仓库重新启用被全局禁用的 provider）。官方建议以其替代旧的 `disabled_providers` / `enabled_providers`。

### 企业相关能力

- 不存储用户代码与上下文数据；唯一外发点是可选的 `/share`。
- 官方 Enterprise 方案（付费、按席位）提供集中式配置、SSO 集成、强制走内部 AI 网关并禁用其他 provider。share 页面自托管**仍在其路线图上**，尚未提供。
- 网络：遵循 `HTTPS_PROXY` / `HTTP_PROXY` / `NO_PROXY`（TUI 与本地服务端通信必须绕过代理），自定义 CA 通过 `NODE_EXTRA_CA_CERTS`。

## 3. 生态与集成

- **模型**：由 models.dev 驱动的全量 provider；官方自营网关 **OpenCode Zen**（可选）提供经过基准测试的模型清单，含 Workspace（团队角色、成员月度额度、模型开关、BYO Key），当前 beta 免费。
- **协议**：MCP（client）、ACP（agent server）、LSP。
- **SDK**：由 OpenAPI 规范经 Stainless 生成的 JS SDK（`@opencode-ai/sdk`），插件类型包 `@opencode-ai/plugin`。
- **知名下游 fork**：小米 **MiMo Code**（`@mimo-ai/cli`，MIT，在 opencode 之上增加 SQLite FTS5 跨会话记忆、`/dream` `/distill` 自进化、Compose 规格驱动模式、内置工作流与 50+ 技能、语音输入）。

## 4. 定价与商业模式

| 档位 | 价格 | 包含 | 限制 |
|---|---|---|---|
| opencode 本体 | 免费（MIT） | 全部功能 | 模型费用自付 |
| OpenCode Zen | 按请求计费（宣称按成本价，仅加收支付手续费） | 官方精选模型网关、余额自动充值、月度限额 | 模型托管于美国 |
| Zen Workspace | beta 期间团队免费 | 角色（Admin/Member）、成员额度、模型开关、BYO Key | 定价待公布 |
| opencode Enterprise | 按席位报价 | 集中配置、SSO、内部网关接入 | 自有网关不额外收 token 费 |

## 5. 已知局限

1. **无 OS 级沙箱**。权限系统在应用层拦截工具调用，模型可通过 `bash` 内的间接手段（如脚本、解释器）绕过路径与命令级规则。隔离必须依赖外部容器/VM。
2. **无内置遥测导出**。仅有 `/log` 与 SSE 事件总线，企业需自建插件把事件转为 OTel/日志平台格式。
3. **无跨会话长期记忆**。上下文仅靠 compaction 与快照维持，会话结束即丢失（下游 fork MiMo Code 正是补这一块）。
4. **无插件市场与分发治理**。插件靠 npm 包名或本地目录加载，缺少来源白名单、版本锁定、准入审核等管控项。
5. **Policies 能力面窄**。当前仅能管控 provider，无法管控 MCP 来源、插件来源、hook 来源。
6. **快照对大仓不友好**。内部 git 快照在大型仓库或多子模块场景下会导致索引慢与磁盘占用高，官方给出的解法是直接关闭。
7. **Remote config 优先级最低**。`.well-known/opencode` 只是基线，会被用户的全局/项目配置覆盖；真正的强制策略只能靠 managed 目录或 macOS MDM，Linux/Windows 没有服务端热更新通道。
8. **`websearch` 依赖外部 Exa 服务**，内网环境不可用。
9. 发布节奏极快（v1.18.7 → v1.18.16 集中在 2026-07-27 至 08-10），fork 方需承担持续 rebase 成本。

## 6. 关键动态

| 日期 | 事件 | 来源 |
|---|---|---|
| 2026-08-10 | v1.18.16 发布（Home 右键项目菜单、目录列举兜底、中文 token 术语修订） | [Releases](https://github.com/anomalyco/opencode/releases) |
| 2026-08-07 | v1.18.15 支持会话完整 JSON 导出 | 同上 |
| 2026-08-04 | v1.18.13 起支持 RTL 布局、复数规则、GitHub PR 评审上下文带 PR 编号与链接 | 同上 |
| 2026-07-28 | v1.18.9 引入可选的 V2 桌面 sidecar（由内置 CLI 服务驱动） | 同上 |
| — | v1.18.0 完成 Desktop v2 迁移，保留新旧布局切换开关 | [v1.18.0](https://github.com/anomalyco/opencode/releases/tag/v1.18.0) |
| 2026-03-26 | 社区 issue #19206 询问官方路线图，被以 "not planned" 关闭——项目**不提供公开路线图** | [issue #19206](https://github.com/anomalyco/opencode/issues/19206) |
| — | 仓库归属由 `sst/opencode` 变更为 `anomalyco/opencode`（文档内 PR 链接与 Releases 页均已指向新组织） | 仓库与官方文档 |

### 实验性开关（反映在研方向）

`OPENCODE_EXPERIMENTAL_*` 系列环境变量：`PLAN_MODE`（计划模式）、`BACKGROUND_SUBAGENTS`（后台子智能体）、`WORKSPACES`（工作区）、`SCOUT`（Scout 子智能体）、`NATIVE_LLM`（原生 LLM 请求路径）、`PARALLEL`（并行搜索）、`EVENT_SYSTEM`（新事件系统）、`LSP_TOOL`、`LSP_TY`、`FILEWATCHER`、`OXFMT`、`ICON_DISCOVERY`、`BASH_DEFAULT_TIMEOUT_MS`、`OUTPUT_TOKEN_MAX`。

## 参考资料

1. [opencode 官方文档仓库源码](https://github.com/anomalyco/opencode/tree/dev/packages/web/src/content/docs)（访问日期 2026-08-11，对应 commit `d041eee`；`opencode.ai` 站点本身在本次调研网络环境下不可达，故直接核对文档源文件）
2. [opencode Releases](https://github.com/anomalyco/opencode/releases)（访问日期 2026-08-11）
3. [sst/opencode README](https://github.com/sst/opencode)（访问日期 2026-08-11）
4. [XiaomiMiMo/MiMo-Code](https://github.com/XiaomiMiMo/MiMo-Code)（访问日期 2026-08-11）
5. [issue #19206：is there any Roadmap on opencode develop](https://github.com/anomalyco/opencode/issues/19206)（访问日期 2026-08-11）
