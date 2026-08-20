# DeepSeek Harness 平台事实、适配决策与待校验项

> 依据：DeepSeek Harness 官方文档与包 README（`github.com/deepseek-ai/deepseek-harness`，
> 查阅日期 2026-08-20）。具体来源：
> `docs/config-catalog.md`（插件 config 字段，自动生成）、`docs/architecture.md`、
> `docs/agent-lifecycle.md`、`docs/subsystems/skills.md`、`docs/subsystems/agent-team.md`、
> `docs/subsystems/system-prompt.md`、`docs/subsystems/core.md`、
> `packages/preset/agent-presets/README.md`、`packages/preset/persona/README.md`、
> `packages/context/agent-instructions/README.md`、`packages/experimental/agent-team/README.md`。
>
> dsh 处于 developer preview 且迭代很快。**以当期文档与 `--dump-config` 为准。**

---

## 0. 对本仓库早先版本的四处更正

| # | 上一版说 | 实际 | 影响 |
|---|---|---|---|
| 1 | 建队友时传 `contextMode = isolated` | `TeamMemberSnapshot.context` 的取值是 **`'fresh' \| 'fork'`**，没有 `isolated` | 全部改为 `fresh`（无父历史种子）。写成 `isolated` 会被拒或被忽略 |
| 2 | 数据采集专家 `canDelegate: true`，可自我分派并行取证 | **名册是扁平的，只有 Lead 能建队友**，没有嵌套 Team | 并行取证必须由 Lead 拆成多个任务下发。这与 OpenClaw 侧不同 |
| 3 | `cordis.patch.yml` 的 `agent-loop.agents[]` 里列了 12 个 agent id | agent-loop 的 `agents[]` 是**进程启动时创建的顶层 agent**；agent-team 的队友是**运行时建的子会话**。两条路都走会得到 12 个互不相识的顶层 agent，外加 Lead 又建出 11 个队友 | 现在只声明 **1 个** —— Lead |
| 4 | `AgentOptions` 的完整字段"未确认"，也许支持 per-agent prompt | **已确认，只有三个字段**：`{ provider?, model?, maxTokens? }`。**没有 prompt，也没有 effort** | 人格的唯一通道确认是 `spawnTeammate(prompt)`；算力档只能靠"一档一条 provider 路由"，见 §3 |

还漏了一项**会直接跑失败**的配置：`agent-team` 的 `maxMembers` **默认是 8**，
而本方案要 11 位队友。不改这一项，会在建到第 8 位时失败。
而且它统计的是**曾经 provision 过的每一个名字，包括建失败的**，且**名字永不复用**。

---

## 1. dsh 的「专家配置」到底包含什么

你问 OpenClaw 那套 `AGENTS.md / SOUL.md / USER.md / IDENTITY.md / TOOLS.md / MEMORY.md`
在 dsh 上对应什么。答案是：**dsh 没有等价的一套文件，它把同样的职责拆到了四个完全不同的机制上。**

| OpenClaw 的东西 | dsh 的对应物 | 是不是逐专家的？ |
|---|---|---|
| `SOUL.md`（人格、语气、立场） | `spawnTeammate(prompt)` | ✅ **是。这是唯一的逐专家人格通道** |
| `IDENTITY.md`（名字、emoji） | `spawnTeammate` 的 `name` + `description` | ✅ 是（`name` 不可变） |
| `AGENTS.md`（操作指令） | ① `@deepseek-ai/dsh-agent-instructions` 加载的 `AGENTS.md` 链<br>② 或并进 `spawnTeammate(prompt)` | ①**否**（按目录，队友共享 cwd）<br>②是 |
| `USER.md`（用户模型） | 无对应物。并进 ① 的 `AGENTS.md` | 否 |
| `TOOLS.md` | **两边都没有这个文件。** OpenClaw 是 `AGENTS.md` 的 `## Tools` 小节，dsh 连这个约定都没有 | — |
| `MEMORY.md` | 无对应物（记忆走 Session 持久化，不走文件） | — |
| `skills/`（工作区技能） | `.dsh/skills/`（rank 100）等六档技能根 | **否**，见 §4 |
| `agents.entries.<id>`（逐 agent 配置） | ① `agent-loop.agents[]`（只对顶层 agent）<br>② preset 目录（**整队共用**） | ①是但字段极少<br>②否 |

### 1.1 dsh 真正的「per-agent 目录」是 preset —— 但它不是逐专家的

dsh 确实有一个"一个目录 = 一份 agent 组合"的机制，叫 **agent preset**：

```
<preset-root>/<preset-id>/
├── agent.cordis.yml     组合：plugin row 的顶层列表（tools / prompt 段 / 技能提供方…）
├── preset.yml           展示元数据：只有 name 与 description（id 来自目录名，trust 来自 root）
└── skills/  等          相对路径从 preset 自己的目录解析 —— 随 preset 一起搬家
```

- preset id = 目录名，必须匹配 `[a-z0-9][a-z0-9-]*`
- root 有 `trust`（`system` 出厂 / `user` 本地），先配置的 root 赢重名
- `includeUserRoot: true`（默认）会把 `<dshHome>/.agent-presets` 追加为 user root
- 选用：`agent-presets: { default: <id> }`

**看起来这就是你要的"每个专家一个独立目录"。它不是。** 因为：

> A subagent's child joins its parent's standing composition through `composeFrom()`,
> **never through `mount()`**.

队友是 Lead 的可续跑子代理，**加入 Lead 的常驻组合，不各自 mount 自己的 preset**。
所以一个专家团 = **一个 preset**，不是 12 个。

理由文档也写了：重新 mount 会让孩子拿到与父不同的组合世代，
而且组合文件被删了孩子会直接失败。

### 1.2 结论：dsh 上逐专家能配的，只有四样

```
spawnTeammate({
  name,          ← 不可变标签，kebab-case，最长 64 字符，永不复用
  description,   ← 名册里的一行
  prompt,        ← 【全部人格】：IDENTITY + SOUL + AGENTS + 运行约定，一整段
  context,       ← 'fresh'（无父历史种子）| 'fork'（复制 Lead 的已完成轮次前缀）
  provider,      ← 已注册的 provider 路由，间接决定 model / effort / maxTokens
})
```

**工具面、技能表、沙箱、cwd —— 一个都不能逐专家配。**

---

## 2. 本方案在 dsh 上怎么摆这三层

| 层 | 载体 | 逐专家？ |
|---|---|---|
| **T1 配置** | `spawnTeammate` 的 `provider` + `context` | ✅ 只有这两项 |
| **T1 团队级** | preset 的 `agent.cordis.yml`（工具、技能根、persona 段）+ `cordis.patch.yml`（provider 路由、agent-team 上限、AGENTS.md 预算） | ❌ 整队一份 |
| **T2 人格** | `spawnTeammate(prompt)` = `IDENTITY.md` + `SOUL.md` + `AGENTS.md` + `runtime/teammate.md` | ✅ |
| **T2 团队级** | 项目 `AGENTS.md`（护栏 + 委托方模型 + 批次约定 + 三条编排铁律） | ❌ 整队一份 |
| **T3 技能** | `.dsh/skills/<name>/SKILL.md`（rank 100）+ preset 自带的一份 | ❌ 目录共用，"谁该用哪个"写在 T2 里 |

### 为什么护栏放在项目 `AGENTS.md` 而不是每份 prompt 里复制一遍

`spawnTeammate(prompt)` 是**会话开头的一次性注入**，长会话经过压缩后可能淡出。
而 `agent-instructions` 加载的 `AGENTS.md` 是**每个会话都会重建的 baseline**：
文档说得很明确——压缩把 baseline 事件挡住之后，下一次进入 pre-step 会重新组装当前 baseline。

所以：**会淡出的东西放 prompt，不能淡出的东西放 `AGENTS.md`。**
三条编排铁律（判据版本、证伪 2 轮、发布闸无旁路）因此写在 `AGENTS.md` 里。

---

## 3. 算力档：一档一条 provider 路由（本包第 1 号风险）

`reasoningEffort` 是 **provider 级**配置（`off | low | high | max`，**没有 medium**），
而 `AgentOptions` 只有 `{ provider, model, maxTokens }`。

所以要给不同专家不同算力，只能一档注册一条路由，再用 `spawnTeammate(provider)` 选：

```yaml
deepseek-low:   { name: '@deepseek-ai/dsh-llm-deepseek', config: { reasoningEffort: low  } }
deepseek-high:  { name: '@deepseek-ai/dsh-llm-deepseek', config: { reasoningEffort: high } }
deepseek-max:   { name: '@deepseek-ai/dsh-llm-deepseek', config: { reasoningEffort: max  } }
```

⚠️ **待校验**：`AgentOptions.provider` 的取值是不是这里的 row id。文档只说它是
"Registered provider route (must have a registered adapter at call time)"，没说路由名怎么来。
`--dump-config` 或建会话时的 provider 选择器里看实际取值。

**如果一个 deployment 只能注册一条 deepseek 路由**：全队共用一个 effort 档，
逐专家算力差异无法实现。折中是设成 `high`，并接受质疑与解读拿不到 `max`。
**不要把"建议 effort"写进提示词就当数**——那是自述，不是配置。

### 3.1 medium 档的损失

原设计中 medium 档的四个角色（枚举、取证、核证、成文）一律落到 `low`。

- 取证与核证是机械性工作，`low` 影响不大
- **枚举需要广度，`low` 可能导致覆盖不足** → 首轮跑完必须人工抽查出局池有无误杀
- 若覆盖不足，把它提到 `high`，成本可接受（枚举只跑一次）

---

## 4. dsh 落不下去的东西（本包第 2、3 号风险）

**这一节是本包与 OpenClaw 包最重要的差异，不要跳过。**

### 4.1 逐专家工具面：做不到

OpenClaw 侧那张表——对比分析专家、领域分析专家、质疑审查专家、争议仲裁专家、
首席洞察专家、报告生成专家**完全剥夺联网**；总调度**唯一持有 exec**——
在 dsh 上**整张表都落不下去**。队友共用 Lead 的 preset 组合，工具注册在 preset 层，
对每一位加入的队友都生效。

**后果要说清楚**：这些约束在 dsh 上退化成 `SOUL.md` 里的**承诺**。
"对比分析专家不取数"在 OpenClaw 上是"它的工具表里没有 browser"，
在 dsh 上是"它答应了不去查"。

**验收方式必须跟着变**：按承诺检验（抽查产出里有没有越界痕迹），
不要按机制检验（"配置里禁了所以不可能发生"在这里不成立）。

**唯一能做的收窄是整队级的**：preset 里**刻意不装 bash / 终端类工具**
（`dsh-tool-bash`、`dsh-terminal-bash`、`dsh-tool-pwsh` 等一个都不装）。
代价是 Lead 也跑不了发布脚本 —— 见 §5。

### 4.2 红队异源：默认不成立

质疑审查专家的异源要求是**不同模型**，不是不同 effort。
只注册 DeepSeek 一家的话，红队与刻画**同源**，同源盲区依然存在。

可选的第二家（都在官方 config-catalog 里）：

- `@deepseek-ai/dsh-llm-pi-ai` —— 另一个直连 LLM 提供方
- `@deepseek-ai/dsh-subagent-claude-code` / `-codex` / `-acp` —— 把外部 harness 接成子代理

`orchestration/cordis.patch.yml` 里留了一段注释掉的 `redteam-alt`。
**不打开就跑，请在验收时如实记下"红队与刻画同源"这一项退化**，
不要当成"和 OpenClaw 版一样"。

### 4.3 逐专家技能表：做不到

技能注册表是 host + per-scope 分层的，但队友都挂在同一个 preset 层下。
所以 12 位专家看到的是**同一张技能目录**。

好消息是代价不高：模型侧目录只用 `name` 与 `description`，**从不用正文**，
所以多几个技能只多几十个 token。"谁该用哪个技能"写在各自的 `AGENTS.md` 段里。

⚠️ **一个会静默失效的坑**：本地技能提供方读的两个 frontmatter 键
`disable-model-invocation` 与 `user-invocable`，**省略时默认为 `true`**。
也就是说省略 `disable-model-invocation` 等于**模型看不到这个技能**。
所有 `SKILL.md` 必须显式写 `disable-model-invocation: false`，
`install.py` 会检查并在缺失时拒绝写入。

### 4.4 共享 checkout

一个进程、一份 checkout，**成员共享 cwd，改动彼此立刻可见**。
任务板上的 `writeScopes` 是**协调提示，不是锁**——它不阻止任何写入，也不授权任何写入。

所以"只写自己那一格"在 dsh 上同样是承诺。写别人的格子不会报错，
但会静默毁掉他们的产出。

---

## 5. 发布闸放在哪

dsh 的 `agent/pre-step` 钩子决策**是 authoritative 的、可以拒绝**——
这一点比 OpenClaw 强（OpenClaw 的钩子明确没有 deny/cancel 语义）。

**但本方案仍然不把闸门放在钩子上**，三个理由：

1. **pre-step 拒绝的是一个 step，不是一次文件写入。** 报告落盘可能发生在工具执行内部。
2. **脚本是平台无关的。** 同一个 `verify_report.py` 在 OpenClaw 版、dsh 版、
   将来任何平台上都是同一份、同一套夹具、同一个退出码。校验逻辑不该随平台重写。
3. **脚本不会被说服。** 钩子里跑模型判断就又回到了"模型守门"。

### dsh 上闸门实际怎么成立

| OpenClaw | dsh |
|---|---|
| 报告生成专家被沙箱关在自己工作区 | ❌ 无逐专家沙箱 |
| 报告生成专家 deny exec | ❌ 无逐专家工具面 |
| 总调度是唯一有 exec 的角色，由它跑发布脚本 | ❌ 无法只给一个人 |
| — | ✅ **preset 里整队都不装 bash/终端工具**，所以没有任何一位专家能跑脚本 |
| — | ✅ **发布由人在 dsh 外面执行** |

代价是发布不再是流水线的一环，需要人介入一次。
**收益是这道闸在 dsh 上仍然是机制而不是承诺** —— 值得。

若你确实需要全自动，可以加一个 `agent/pre-step` 钩子拦"写入发布目录"这个动作
（不是"渲染报告"这个步骤），作为**加固**，不是替代。

---

## 6. 消息与并发

| 事实 | 影响 |
|---|---|
| 消息走**持久收件箱**：先落库再投递，收据只在对方 pending inbox 或已记录消息落库后确认 | 派发可靠，**Lead 不需要自己做重试**。`queued` 不是"要你重发" |
| `maxMessageBytes` 默认 65536，覆盖完整封装 | 派任务传**文件路径**，不要把证据库贴进消息体 |
| `waitForChange()` 有界等待，**十秒到一小时** | 取证类任务不会超时。**不要写忙轮询** |
| 保证是"进程内重试 + 目标会话去重"，**不是跨进程恰好一次** | 不要同时跑两个 harness 进程操作同一个 Team |
| `maxParallelToolCalls: 8` | 取证阶段是并发大头，按速率限制实测回调。撞限流的表现是大面积超时，不是报错 |
| `interrupt()` 只有 Lead 能用，且只取消当前轮次、不清收件箱、不释放任务归属 | 中断后要手动 release 任务 |

---

## 7. 技能发现优先级（文档明确）

| Rank | 来源 | 根 |
|---|---|---|
| 100 | `project-dsh` | `<projectRoot>/.dsh/skills` |
| 200 | `project-agents` | `<projectRoot>/.agents/skills` |
| 300 | `custom` | `Config.customSkillDirs` |
| 400 | `user-dsh` | `<dshHome>/skills` |
| 500 | `user-agents` | `<agentsHome>/skills` |
| 600 | `bundled` | `Config.bundledSkillDir` |

**数字小者优先。** 项目根是最近的含 `.git` 的祖先目录；没有则用 cwd。
技能名 kebab-case，接受 `<name>/SKILL.md` 与扁平的 `<name>.md`，
**不支持嵌套递归发现**。

本方案装到 rank 100（`.dsh/skills`），preset 自带的那一份落在 rank 300。

---

## 8. 上线前必须校验的四项

跑 `dsh --profile web --dump-config`，比对以下四处。**不要直接信我。**

| # | 待校验 | 我采用的写法 | 改错了会怎样 |
|---|---|---|---|
| 1 | **`cordis.patch.yml` 的顶层形状** | `plugins:` → row id → `{ name, config }` | 整个 patch 被忽略 —— **不报错，只是不生效** |
| 2 | **provider 路由名是不是 row id** | `deepseek-low` / `-high` / `-max` | 逐专家算力档失效，全队落到同一档 |
| 3 | 插件包名 | `@deepseek-ai/dsh-llm-deepseek` / `-agent-loop` / `-agent-instructions` / `-skill-filesystem` / `-experimental-agent-team` / `-persona` | 同 1 |
| 4 | `retryPolicy` 的字段名 | `maxRetries` | 同 1 |

第 1 项风险最高：**配置错了不报错，只是静默失效。** 所以先 `--dump-config` 确认，再跑批次。

preset 侧另有两项：`agent.cordis.yml` 是**顶层列表**（不是映射）；
`preset.yml` **只承载 `name` 与 `description`**，写 `id` 或 `trust` 无效。

---

## 9. 跨平台与脚本

| 文件 | 角色 |
|---|---|
| `install.py` / `bin/publish_report.py` | **业务逻辑，跨平台，已在 Linux 上实测** |
| `install.ps1` / `bin/publish-report.ps1` | Windows 薄封装：找 Python → 转调 |
| `install.sh` / `bin/publish-report.sh` | Linux/macOS 薄封装：同上 |

封装里没有任何业务逻辑，三端跑同一份代码。

Windows 上处理掉的三个坑：

| 坑 | 处理 |
|---|---|
| **BOM 破坏 frontmatter 解析** | 生成器显式 `encoding="utf-8"` 写入，Python 默认不加 BOM |
| 行尾 | 显式 `newline="\n"`，统一 LF |
| 控制台 GBK 编码炸掉 ✓/✗ | Python 侧 `reconfigure(encoding="utf-8")`；PowerShell 侧设 `[Console]::OutputEncoding` 与 `PYTHONUTF8=1` |

第一条最要紧：`SKILL.md` 带 BOM 会让 frontmatter 解析失败，而这**不一定报错**——
可能只是该技能被静默忽略。

⚠️ `.ps1` 未经本地语法校验（本环境没有 PowerShell）。封装很薄，
若报错直接跑 `python install.py <目录> --write`，效果完全一致。

---

## 10. 参考来源

- [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)（访问日期 2026-08-20）
- `docs/config-catalog.md` — 插件 config 字段（自动生成）
- `docs/architecture.md` — patch 分层与 `--dump-config`
- `docs/agent-lifecycle.md` — turn/step 生命周期、pre-step 决策
- `docs/subsystems/agent-team.md` + `packages/experimental/agent-team/README.md` — Team 名册、邮箱、任务板
- `docs/subsystems/skills.md` — 技能格式、发现优先级、frontmatter
- `docs/subsystems/system-prompt.md` — 提示词段落的 order 约定（-100 harness 身份 / 0 部署人格 / 100–199 工具指引）
- `packages/preset/agent-presets/README.md` — preset 目录形态、mount/composeFrom、trust
- `packages/preset/persona/README.md` — `deployment:persona` 段
- `packages/context/agent-instructions/README.md` — `AGENTS.md` 链的加载与预算
- `docs/subsystems/core.md` — `AgentOptions` 的完整字段
