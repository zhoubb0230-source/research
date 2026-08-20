# OpenClaw 平台事实、适配决策与待校验项

> 依据：OpenClaw 官方文档（`github.com/openclaw/openclaw` 的 `docs/`，查阅日期 2026-08-20）。
> 具体页：`concepts/agent-workspace`、`start/bootstrapping`、`gateway/config-agents`、
> `tools/subagents`、`tools/skills`、`tools/multi-agent-sandbox-tools`、`automation/hooks`、
> `concepts/soul`、`concepts/user-model`、`concepts/memory`。
>
> 本仓库不缓存其内容。上线前请以当期文档与 `openclaw config schema` 为准。

---

## 0. 对本仓库早先版本的三处更正

上一版 `OPENCLAW-NOTES.md` 有三处结论经查文档后**不成立**，已改：

| # | 上一版说 | 实际 | 影响 |
|---|---|---|---|
| 1 | `thinkingDefault` **没有** `xhigh` / `max`，分析与质疑角色只能落到 `high` | **有。** 合法取值是 `off \| minimal \| low \| medium \| high \| xhigh \| adaptive \| max`（具体哪些可用由 provider/model profile 决定） | 质疑审查专家与首席洞察专家现在拿到 `max`，与原设计一致，**没有精度损失** |
| 2 | `entries.*.model` 的形态"不确定"，暂用对象 `{ primary }` | **两种都合法**：字符串形态 = 严格主模型、无 fallback；对象形态 `{ primary, fallbacks }` 才开 fallback | 12 位专家现在统一用**字符串形态**——批次中途悄悄换模型会让跨对象结论不可比 |
| 3 | `tools.deny` 的合法工具名"未穷举"，只敢写 `["exec"]` | 文档的访问档位示例里给出了实际工具名：`read` `write` `edit` `apply_patch` `exec` `process` `browser` `canvas` `nodes` `cron` `gateway` `image` `sessions_list` `sessions_history` `sessions_send` `sessions_spawn` `session_status`；另有 profile 自带的 `web_search` / `web_fetch` | 工具面收窄从"只敢 deny 一个"变成了逐角色可编排，见 §4 |

还有一处**度量单位错误**（在 `../expert-team/BOUNDARIES.md` 里已注明）：
上一版说总调度的 `AGENTS.md`「约 18 KB，逼近 20000 上限」——
那是拿 **UTF-8 字节数**比一个**字符数**上限。中文一字三字节，实测旧装配是 7824 字符，
离 20000 还有一半余量。截断风险当时被高估了。

---

## 1. OpenClaw 的「专家配置」到底包含什么

这是本次调研最核心的一张表。你提到的 `AGENTS.md / SOUL.md / USER.md / IDENTITY.md /
TOOLS.md / MEMORY.md` **基本正确，但有一处需要更正、两处需要补充**。

### 1.1 工作区文件（每轮注入系统提示词 = 本方案的 T2 人格层）

| 文件 | 官方定义 | 必需？ | 预算 | 本方案怎么用 |
|---|---|---|---|---|
| `AGENTS.md` | 操作指令、以及"如何使用记忆"。**每次会话开始加载** | 必需 | `bootstrapMaxChars` 20000 字符 | 输入输出契约、schema、交接规则、何时读技能 |
| `SOUL.md` | 人格、语气、边界 | 可选 | 同上 | 立场、KPI、不可说服的规则、绝不做的事；**护栏内联在最前面** |
| `IDENTITY.md` | agent 的名字、vibe、emoji | 可选 | 同上 | 名字 + emoji + 在骨架里的位置 |
| `USER.md` | 用户模型，**指令式条目**（`Always` / `Never` / `Prefer` + 观察日期 + `active`/`superseded`） | 可选 | **独立的 4000 字符预算** | 委托方模型（12 位共用一份） |
| `MEMORY.md` | 精选长期记忆。**只在主会话加载，共享/群组会话不加载** | 可选 | 计入合计 | **本方案不用**，理由见 §1.4 |
| `memory/YYYY-MM-DD.md` | 每日记忆日志 | 可选 | 走 `startupContext` 预算 | 不用 |
| `BOOT.md` | 网关重启时自动跑的启动检查单（需开 internal hooks） | 可选 | — | 不用 |
| `BOOTSTRAP.md` | 一次性首次运行仪式 | 自动生成 | — | **关掉**（`skipBootstrap: true`） |
| `skills/` | 工作区技能，**该工作区技能优先级最高** | 可选 | 只有 name+description 进提示词 | T3 技能层 |

**合计上限 `bootstrapTotalMaxChars` 默认 60000 字符。**
超出即截断，运行时只提示"有文件被截断"，**不告诉你截了哪个**。

### 1.2 ⚠️ 更正：没有 `TOOLS.md`

文档明确：**环境相关的工具约定放在 `AGENTS.md` 的 `## Tools` 小节**，
不是一个独立文件。而且原文说得很清楚：

> The `## Tools` section holds local environment notes and conventions.
> **It does not control tool availability; it is only guidance.**

**工具可用性由配置层决定**，不是由这段散文决定：

```
agents.entries.<id>.tools.profile     基础档位（minimal | coding | messaging | full）
agents.entries.<id>.tools.alsoAllow   在 profile 之上加回工具
agents.entries.<id>.tools.allow       最终 allow-only 过滤（只能收窄，不能加回被 profile 移除的）
agents.entries.<id>.tools.deny        deny 永远胜出
```

本方案 12 位专家的 `AGENTS.md` 都保留了一个 `## Tools` 小节，但里面只写
"我为什么被给了/没被给这个能力"，真正的约束在 `experts/<id>/entry.json5` 里。
**这正是 `BOUNDARIES.md` 说的「能落 T1 的必须落 T1」。**

### 1.3 补充：一个工作区什么时候算"已配置"

> A workspace counts as configured once `SOUL.md`, `IDENTITY.md`, or `USER.md`
> has diverged from its starter template, or a `memory/` folder exists.

本方案的 `install.py` 生成的三个文件全都与模板不同，所以工作区一装好就是"已配置"，
`BOOTSTRAP.md` 仪式不会触发。同时我们显式设了 `skipBootstrap: true` 作双保险。

### 1.4 为什么本方案不用 `MEMORY.md`

洞察是**批次任务**，不是持续陪伴。跨批次沉淀的东西应该是
`baseline.json`（结构化、可被 `trend` 算子消费、可被校验），而不是自然语言记忆。

给专家配 `MEMORY.md` 的具体风险：上一批次"某某市场大约多少"的记忆，
会在下一批次变成一个**没有 `evidence_id` 的数字**——它绕过了取证与核证两道闸，
而且看不出来。这与全员护栏第一条直接冲突。

**跨批次的记忆载体是 `baseline.json`，不是 `MEMORY.md`。**

### 1.5 逐 agent 配置字段（= 本方案的 T1 配置层）

`agents.entries.<id>` 支持的、本方案用到的字段：

| 字段 | 本方案怎么用 |
|---|---|
| `workspace` | 每位专家一个独立工作区（`install.py` 生成） |
| `agentDir` | 每位专家独立的运行时状态目录 |
| `identity.{name,emoji,theme,avatar}` | 中文名 + emoji；`ackReaction` 与 `mentionPatterns` 由它派生 |
| `model` | **字符串形态**（严格，无 fallback） |
| `thinkingDefault` | `high` / `max` / `low` 三档 |
| `contextInjection` | 全员 `always`——长流水线中途不能丢护栏 |
| `tools.{profile,alsoAllow,allow,deny}` | 逐角色工具面，见 §4 |
| `skills` | 逐角色技能白名单；**非空列表会整体替换 defaults，不是合并** |
| `sandbox.{mode,scope,workspaceAccess}` | 只有报告生成专家开，见 §5 |
| `subagents.{allowAgents,requireAgentId,delegationMode}` | 派发白名单，见 §3 |
| `bootstrapMaxChars` / `bootstrapTotalMaxChars` | 保留默认，`install.py` 会自检并在超限时拒绝 |

---

## 2. 平台能力核对

| 原方案要求 | OpenClaw 能力 | 结论 |
|---|---|---|
| 多角色、各自模型与提示词 | `agents.entries.<id>` 逐项覆盖 | ✅ |
| 角色间派发与汇总 | `sessions_spawn` + push 式 announce | ✅ |
| **用 `agentId` 派发时，子会话用目标角色的人格** | 文档明确：*"Native sub-agents still load bootstrap files from the target agent workspace"* | ✅ **这是本方案能成立的关键事实** |
| 红队必须异源、看不到分析师推理 | 逐 agent 不同 `model` + `context: "isolated"` | ✅ 比原方案更强：隔离由平台保证 |
| 逐角色工具面收窄 | `tools.{profile,alsoAllow,allow,deny}` | ✅ |
| 逐角色文件系统隔离 | `sandbox.{mode,scope,workspaceAccess}` | ⚠️ 需要沙箱后端，见 §5 |
| 阶段间硬门 | 无原生阶段网关 | ⚠️ 由总调度 + 技能承担，见 §6 |
| **渲染前确定性校验、非 0 即阻断** | **hooks 无 deny/cancel 语义** | ❌ **不成立，已换落点，见 §7** |

---

## 3. 派发拓扑

```
洞察总调度 (depth 0)  ← 唯一绑定人类通道
   └─ 11 位专家 (depth 1)
         └─ 采集工蜂 (depth 2，仅数据采集专家可派，且只能派它自己)
```

三个必须一起设的字段：

| 字段 | 取值 | 理由 |
|---|---|---|
| `maxSpawnDepth` | **2** | 默认 1 时 depth-1 是叶子，**不被授予 `sessions_spawn`**，数据采集专家就无法 fan-out |
| `subagents.allowAgents` | 总调度列 11 位；数据采集专家列 `["data-collector"]` 自己 | **默认只有请求方自己能被派发**。不设这个，总调度谁也派不动 |
| `requireAgentId` | `true` | 禁止不指名的模糊派发 |

**注意**：`allowAgents` 要包含自己才能自派——文档原话是
*"Include the requester id when self-targeted `agentId` calls should be allowed."*

并发额度（全部需按你的速率限制实测回调）：

| 参数 | 默认 | 本方案 |
|---|---|---|
| `maxChildrenPerAgent` | 5 | 20 |
| `maxConcurrent` | 8 | 12 |
| `announceTimeoutMs` | 120000 | 600000（取证类任务远超 2 分钟） |
| `archiveAfterMinutes` | 60 | 240 |
| `runTimeoutSeconds` | 0 | 0（不设超时） |

---

## 4. 逐角色工具面：一个容易踩的坑

`tools.profile: "coding"` **包含 `web_search` / `web_fetch`，但不包含 `browser`**。

所以"剥夺某位专家的联网能力"必须同时 deny 三个：

```json5
"deny": ["browser", "web_search", "web_fetch"]
```

只 deny `browser` 是不够的——那位专家仍然能检索，只是不能开浏览器。
本方案里有 6 位专家（对比分析、领域分析、质疑审查、争议仲裁、首席洞察、报告生成）
被完全剥夺联网，全部三个都 deny 了。

另一条：`tools.allow` 是**只能收窄的最终过滤**，
它**不能加回被 profile 移除的工具**。要加回得用 `alsoAllow`（在 profile 阶段生效）。

---

## 5. 报告生成专家的沙箱

**推荐配置**（本方案默认）：

```json5
"sandbox": { "mode": "all", "scope": "agent", "workspaceAccess": "rw" }
```

⚠️ **有部署前置**：`sandbox` 需要一个后端（`docker`（默认）/ `podman` / `openshell` / `ssh`）。
没有可用后端时这一条**不生效**，而且不一定报错。

### 没有 Docker 时的降级方案，以及它弱在哪

降级：`sandbox.mode: "off"`，靠 `tools.deny: ["exec", "process"]` 拦住它自己跑脚本。

**这不等价。** 文档明确：

> The workspace is the **default cwd, not a hard sandbox**. Tools resolve relative
> paths against the workspace, but **absolute paths can still reach elsewhere** on
> the host unless sandboxing is enabled.

也就是说，降级之后报告生成专家**仍然可以用绝对路径写到发布目录**。

**唯一的缓解**：让它根本不知道发布目录在哪——
发布目录路径不出现在它的 `AGENTS.md`、不出现在派发给它的任务描述里。
本方案的装配已经满足这一点（发布路径只在总调度的 `publish-report` 技能里）。

这是**信息隐藏，不是访问控制**。用降级方案时请如实知道自己拿到的是哪一种。

---

## 6. 阶段硬门由总调度承担 —— 本方案最薄的一环

OpenClaw 没有 BPMN 式的阶段网关。准入条件写在技能 `run-insight-batch` 里，由总调度执行。
**这依赖总调度遵守自己的手册，属于模型自觉，不是机制保证。**

缓解措施：

- `run-ledger` hook 把阶段事件写成 JSONL 台账，事后可审计"证伪是不是真的止于 2 轮"
- 关键的不可逆动作（brief 冻结、批次归档）设人工签署
- **真正致命的那道闸（数字校验）已经落到机制上**，不依赖总调度自觉

---

## 7. 第三道闸为什么不在 hook 上

OpenClaw 的 internal hooks 收到事件后可以往 `event.messages` 里塞回复、可以写日志，
但**不能取消或拒绝正在发生的动作**。

把校验挂在 hook 上，结果是"记录了违规但照样发布"——
**这比没有闸更危险**，因为它会制造"已经校验过"的错觉。

### 解法：让唯一通往发布的路径内含校验

```
报告生成专家（沙箱 + deny exec）
   └─ 只能写自己的工作区 ──────────────→ 草稿
                                          │
洞察总调度 执行 bin/publish-report.sh ─────┤
   ├─ 内部跑 verify_report.py             │
   ├─ 退出码 0 → 落盘发布目录       ✅   │
   └─ 退出码 1 → 不落盘，报违规     ❌ ──┘
```

三层权限共同保证不可绕过：沙箱（写不到）+ deny exec（跑不了脚本）+
只有总调度有 exec（发布集中在一个可审计的点）。

**这比原设计更强**：原设计依赖"钩子会拦住"，现在是"根本没有第二条路"。

`../expert-team/orchestration/pipeline.yaml` 的 INV-3 应理解为：
**平台必须能提供一条"唯一的、内含确定性校验的发布通道"**，
而不是"必须有可阻断的钩子"。

---

## 8. 上线前必须校验的四项

跑 `openclaw config schema`，比对以下四处。**不要直接信我。**

| # | 待校验 | 我采用的写法 | 改错了会怎样 |
|---|---|---|---|
| 1 | 模型 ID 是否已在你的 provider 注册 | `anthropic/claude-opus-5` 等 | 文档说裸 ID 需要 provider 匹配或显式 `provider/model`。**你的 provider 命名可能不是 `anthropic`** |
| 2 | `bindings.match.channel` 的合法取值 | 占位 `<CHANNEL>` | 填你实际启用的通道；`install.py` 会拒绝残留占位符 |
| 3 | `session.reset.mode: "off"` 是否合法 | `"off"` | 文档只举了 `daily` 与 idle，`off` 是推断。**不合法就整段删掉**，改用长 idle 阈值 |
| 4 | hook handler 的模块导出形态 | 同时 `module.exports` 与 `.default` | 文档示例用 `export default`（TS）；为兼容 CJS 两种都导出 |

第 3 项风险最高：**配置不合法时的失败方式可能是静默忽略**，不是报错。

`agents.entries.*.skills: []` 的语义（空数组 = 无技能）在本次已从文档确认：
> Set `agents.entries.*.skills: []` for no skills. A non-empty list is the final
> set for that agent; **it does not merge with defaults**.

所以本方案给每位专家显式列出它自己的技能名，不依赖继承。

---

## 9. 参考来源

- [Agent workspace](https://docs.openclaw.ai/concepts/agent-workspace)
- [Agent bootstrapping](https://docs.openclaw.ai/start/bootstrapping)
- [Configuration — agents](https://docs.openclaw.ai/gateway/config-agents)
- [Sub-agents](https://docs.openclaw.ai/tools/subagents)
- [Skills](https://docs.openclaw.ai/tools/skills)
- [Multi-agent sandbox & tools](https://docs.openclaw.ai/tools/multi-agent-sandbox-tools)
- [Hooks](https://docs.openclaw.ai/automation/hooks)
- [SOUL.md personality guide](https://docs.openclaw.ai/concepts/soul)
- [User model](https://docs.openclaw.ai/concepts/user-model)
- [Memory](https://docs.openclaw.ai/concepts/memory)

（文档源文件在 `github.com/openclaw/openclaw` 的 `docs/` 目录，查阅日期 2026-08-20。）
