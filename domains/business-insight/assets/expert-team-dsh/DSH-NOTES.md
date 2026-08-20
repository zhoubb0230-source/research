# DeepSeek Harness 平台事实与适配决策

> 依据 DeepSeek Harness 官方文档（`github.com/deepseek-ai/deepseek-harness`，查阅日期 2026-08-19）。
> 本文记录：**哪些是文档明确的**、**哪些是我推断的**、**上线前你必须校验什么**。

---

## 1. 一句话

dsh 能承载这套专家团，而且在一个关键点上**比 OpenClaw 更适合**：
它的 `agent/pre-step` 钩子决策是 authoritative 的——**可以拒绝**，
而 OpenClaw 的钩子明确没有 deny/cancel 语义。

但本方案仍然**不把闸门放在钩子上**，理由见 §3。

---

## 2. 文档明确的事实（可以照着用）

| 项 | 事实 | 出处 |
|---|---|---|
| 安装与启动 | `npx @deepseek-ai/dsh web`，默认 `http://127.0.0.1:3080` | README |
| 配置文件 | `cordis.yml`；用户侧覆盖走 **`cordis.patch.yml`**（profile 级与 home 级），再叠 `--patch` | architecture.md |
| 配置自查 | `dsh --profile web --dump-config` | architecture.md |
| **Skill 格式** | `<name>/SKILL.md` 或 `<name>.md`；名字 kebab-case `^[a-z0-9]+(?:-[a-z0-9]+)*$` | subsystems/skills.md |
| **Skill 发现优先级** | `.dsh/skills`(100) > `.agents/skills`(200) > 自定义(300) > `<dshHome>/skills`(400) > `<agentsHome>/skills`(500) > 内置(600)。**数字小者优先** | 同上 |
| Skill 项目根 | 最近的含 `.git` 的祖先目录；没有则用 cwd | 同上 |
| Skill frontmatter | `disable-model-invocation`、`user-invocable`，省略时默认 `true` | 同上 |
| LLM 提供方配置 | `apiKeyEnv` / `baseURL` / `thinking`(`enabled`\|`disabled`) / **`reasoningEffort`(`off`\|`low`\|`high`\|`max`)** / `maxTokens` / `defaultContextWindow` / `models` / `streamIdleTimeoutMs` / `retryPolicy` | config-catalog.md |
| Agent 循环配置 | `{ maxParallelToolCalls?, agents: (AgentOptions & { id, sessionId?, cwd?, resumeSessionId? })[] }` | 同上 |
| 外部子代理 | `dsh-subagent-acp`：`{ providerName, command, args[], cwd?, permission: 'allow'\|'reject', env, ... }` | 同上 |
| **多 Agent 协作** | `spawnTeammate()` 建队友、`sendMessage()` 派任务、`waitForChange()` 等结果（**有界等待，十秒到一小时**） | subsystems/agent-team.md |
| 消息可靠性 | 持久收件箱：先落库再投递；收据只在对方 pending inbox 或已记录消息落库后确认 | 同上 |
| pre-step 钩子 | **返回的 `agent/pre-step` 决策是 authoritative 的**，可用于校验/拒绝 | agent-lifecycle.md |
| Skill 的性质 | 「可扩展 agent 能力的**可选指令**」——是被发现、被调用的资源，**不是 agent 的人格绑定** | subsystems/skills.md |
| 人格绑定 | `SpawnTeammateRequest` 含 **`prompt`** 字段，人格在建队友时传入 | subsystems/agent-team.md |

---

## 3. 闸门为什么仍然放在脚本里

dsh 的 pre-step 钩子**能**拒绝，理论上可以把数字校验挂上去。本方案没有这么做：

1. **pre-step 拒绝的是一个 step，不是一次文件写入。** 报告落盘可能发生在工具执行内部，
   pre-step 未必能精确拦住那一刻。
2. **脚本是平台无关的。** 同一个 `verify_report.py` 在 OpenClaw 版、dsh 版、以及将来任何平台上
   都是同一份、同一套夹具、同一个退出码。校验逻辑不该随平台重写。
3. **脚本不会被说服。** 钩子里跑模型判断就又回到了"模型守门"，那正是要避免的。

所以：`bin/publish-report.sh` 是主闸，pre-step 钩子是**可选的加固**，不是替代。
若你想加，建议拦的是"写入发布目录"这个动作，而不是"渲染报告"这个步骤。

---

## 4. 适配决策

### 4.1 agent 与 skill 的边界

**判据是「常驻 vs 按需触发」，不是「复不复用」。**

先前用"被 ≥2 个 agent 用"当 skill 的标准——那是去重判据，与 skill 的定义无关。
官方文档说 skill 是「可扩展 agent 能力的**可选指令**」，本质属性是**可调用性**。

| | 性质 | 放哪 | 例 |
|---|---|---|---|
| **Persona** | 常驻。从建立到销毁一直遵守 | `agents/<id>/persona.md` | 认知姿态、禁令、输入输出契约 |
| **Skill** | 按需。遇到特定子任务才被调用 | `skills/<name>/SKILL.md` | "要记一条证据时，按这几步做" |

**两条推论：**

**① 护栏必须在 persona，不能做成 skill。**
skill 是 optional 的——模型可以不调用它。把「禁止编造数据」做成 skill，
等于把它变成可选项。防编造是本系统全部价值的地基，必须随 `spawnTeammate` 的 prompt 绑死。

**② 专属 skill 完全正当。** 本交付件 13 个 skill 里 10 个只被一个 agent 用。
`falsification-memo` 只有质疑审查专家会调，但它依然是 skill——
因为它是"开始质疑前先写备忘录"这样一个**有明确触发时机的作业程序**，不是"我是谁"。

### 4.1.1 agent 之间必须有互斥的认知姿态

多 agent 的价值来自姿态之间的**张力**。12 个都写成"严谨、有帮助的助手"，
就是一个 agent 跑了 12 遍，只剩成本没有收益。

每个 `persona.md` 的第一段是认知姿态，它们刻意互斥：
采集**不推理** / 核证**不信任** / 分析**只在证据上推理** / 质疑**敌意** /
仲裁**不站队** / 洞察**越界但标注** / 成文**不思考**。

**自检**：把任意两个 agent 的 persona 对调，产出应该明显变差。
对调了没影响，说明这两个没有核心差异，应该合并。

### 4.2 角色命名已泛化

骨架现在是通用的（十动作，不绑定产业机会场景），所以角色名也跟着泛化了：

| 原名（OpenClaw 包仍在用） | dsh 包 | 骨架动作 |
|---|---|---|
| 口径定义专家 | **洞察规划专家** `insight-planner` | ① 界定（含分诊） |
| 机会枚举专家 | **范围界定专家** `scope-definer` | ② 枚举 |
| 产业分析专家 | **对比分析专家** `comparative-analyst` | ⑤ 刻画 ⑥ 聚合 |
| 技术链分析专家 | **领域分析专家** `domain-analyst`（可插拔） | ⑤ 刻画（领域维度） |
| 合规管制专家 | **合规审查专家** `compliance-reviewer`（可选） | 闸门 + 合规维度 |
| 首席洞察专家 | 同名，但**职责扩大**：从只验收变为**产出解读 + 验收** | ⑨ 解读 |

⚠️ **`../expert-team-openclaw/` 仍在用旧名，尚未同步。** 两个包目前不一致，
以本包（dsh）的命名为准——它对齐了通用骨架。

### 4.3 reasoningEffort 没有 medium 档

dsh 只有 `off | low | high | max`。原设计中 medium 档的四个角色
（范围界定、数据采集、数据核证、报告生成）**一律落到 `low`**。

影响与补偿：

- 取证与核证是机械性工作，`low` 影响不大
- 范围界定需要广度，`low` 可能导致枚举覆盖不足 → **首轮跑完要人工抽查出局池有无误杀**
- 若覆盖不足，把它提到 `high`，成本可接受（枚举只跑一次）

对抗与解读拿到最高档：质疑审查专家与首席洞察专家都是 `max`。
这是刻意的——**最难的判断给最多的算力**。

### 4.4 并发

`maxParallelToolCalls: 8` 是初始值，取证阶段是并发大头，**按你的速率限制实测回调**。
`waitForChange()` 有界等待上限一小时，取证类任务不会超时。

---

## 5. 上线前必须校验的四项

跑 `dsh --profile web --dump-config`，比对以下四处。**不要直接信我。**

| # | 待校验 | 我采用的写法 | 改错了会怎样 |
|---|---|---|---|
| 1 | **`cordis.patch.yml` 的顶层形状** | `plugins:` → 包名 → `config:` | 整个 patch 被忽略——**不报错，只是不生效** |
| 2 | `AgentOptions` 的完整字段 | 只填了文档明确的 `id`；persona 走运行时 `spawnTeammate(prompt=…)` | 若它支持 per-agent prompt，改到配置层更硬（配置约束 > 运行时约束） |
| 3 | 插件包名 | `@deepseek-ai/dsh-llm-deepseek` / `@deepseek-ai/dsh-agent-loop` | 同 1 |
| 4 | `retryPolicy` 的字段名 | `maxRetries` | 同 1 |

第 1 项风险最高：**配置错了不报错，只是静默失效**。所以先 `--dump-config` 确认，再跑。

---

## 6. 参考来源

- [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)（访问日期 2026-08-19）
- `docs/config-catalog.md`（插件 config 字段，自动生成）
- `docs/architecture.md`（patch 分层与 `--dump-config`）
- `docs/agent-lifecycle.md`（turn/step 生命周期、pre-step 决策）
- `docs/subsystems/agent-team.md`（`spawnTeammate` / `sendMessage` / `waitForChange`）
- `docs/subsystems/skills.md`（skill 格式、发现优先级、frontmatter）

本仓库不缓存其内容；dsh 处于 developer preview 且迭代很快，**以当期文档与 `--dump-config` 为准**。


---

## 7. 跨平台与脚本

### 7.1 逻辑只有一份

| 文件 | 角色 |
|---|---|
| `install.py` / `bin/publish_report.py` | **业务逻辑，跨平台，已在 Linux 上实测** |
| `install.ps1` / `bin/publish-report.ps1` | Windows 薄封装：找 Python → 转调 |
| `install.sh` / `bin/publish-report.sh` | Linux/macOS 薄封装：同上 |

封装里没有任何业务逻辑。三端跑同一份代码，不会出现
「Linux 上好好的、Windows 上行为不一样」这类问题。

⚠️ **`.ps1` 未经本地语法校验** —— 本环境没有 PowerShell。封装很薄（找 Python + 转调），
若它报错，直接跑 `python install.py <目录> --write` 即可，效果完全一致。

### 7.2 Windows 上处理掉的三个坑

| 坑 | 处理 |
|---|---|
| **BOM 破坏 frontmatter 解析** | 生成器显式 `encoding="utf-8"` 写入，Python 默认不加 BOM |
| **行尾** | 显式 `newline="\n"`，统一 LF，不受平台影响 |
| **控制台 GBK 编码炸掉 ✓/✗ 与制表符** | Python 侧 `sys.stdout.reconfigure(encoding="utf-8")`；PowerShell 侧设 `[Console]::OutputEncoding` 与 `PYTHONUTF8=1` |

第一条最要紧：`SKILL.md` 带 BOM 会让 frontmatter 解析失败，而这**不一定报错**——
可能只是该 skill 被静默忽略。

### 7.3 PowerShell 执行策略

若被拦，本会话临时放行即可，不必改全局设置：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
