# OpenClaw 平台约束与适配决策

> 本文记录：为把专家团落到 OpenClaw，**原方案哪些地方必须改**、改成了什么、以及**哪些字段我无法从文档确认、必须你上线前校验**。
> 依据为 OpenClaw 官方文档（`docs.openclaw.ai`，源文件在 `github.com/openclaw/openclaw/docs/`，查阅日期 2026-08-19）。

---

## 1. 一句话结论

OpenClaw 能承载这套专家团，但**原方案的第三道闸必须换落点**——它原本设计成"渲染前的阻断式钩子"，而 OpenClaw 的钩子不能阻断任何动作。

---

## 2. 平台能力核对

| 原方案要求 | OpenClaw 能力 | 结论 |
|---|---|---|
| 多角色、各自模型与提示词 | `agents.entries.<id>` 支持 `model` / `thinkingDefault` / `workspace` / `identity` / `sandbox` / `tools` 逐 agent 覆盖 | ✅ 直接支持 |
| 角色间派发与汇总 | `sessions_spawn` + `sessions_yield`，完成后 push 式 announce 回父 | ✅ 直接支持 |
| 红队必须异源、看不到分析师推理 | spawn 参数 `context: "isolated"`（干净 transcript）+ 逐 agent 不同 `model` | ✅ **比原方案更强**：隔离由平台保证，不靠提示词自觉 |
| 证据库跨阶段持久化 | agent 工作区 + 批次目录（文件系统） | ✅ 支持，需自建目录约定 |
| 阶段间硬门 | 无原生阶段网关 | ⚠️ 由总调度 + playbook 承担，见 §4.1 |
| **渲染前确定性校验、非 0 即阻断** | **hooks 无 deny/cancel 语义，明确"cannot block actions"** | ❌ **不成立，已改设计，见 §3** |

---

## 3. 最重要的一处改动：第三道闸换落点

### 问题

原方案 `pipeline.yaml` 的 INV-3 写的是：

> 渲染前必须执行确定性数字校验钩子（`checks/verify_report.py`），退出码非 0 即阻断。
> **做不到这一条的平台不能选**——第三道闸是唯一不可被模型绕过的防线。

OpenClaw 的 internal hooks 收到事件后可以往 `event.messages` 里塞回复、可以写日志，
但**不能取消或拒绝正在发生的动作**。把校验挂在 hook 上，结果是"记录了违规但照样发布"——
这比没有闸更危险，因为它会制造"已经校验过"的错觉。

### 解法：把闸门放进「发布」这个动作本身

不再问"能不能拦住写文件"，而是让**唯一通往发布目录的路径**内含校验：

```
报告生成专家（sandbox: all）
   └─ 只能写自己的工作区 ──────────────→ 草稿
                                          │
洞察总调度 执行 bin/publish-report.sh ─────┤
   ├─ 内部跑 verify_report.py             │
   ├─ 退出码 0 → cp 草稿 → 发布目录  ✅   │
   └─ 退出码 1 → 不落盘，报违规      ❌ ──┘
```

三层权限约束共同保证它不可绕过：

| 约束 | 配置位置 | 挡住什么 |
|---|---|---|
| `sandbox: "all"` | `agents.entries.report-writer` | 报告生成专家写不到发布目录 |
| `tools.deny: ["exec"]` | 同上 | 它无法自己执行命令绕过脚本 |
| 只有总调度可执行发布脚本 | playbook + 工作区约定 | 发布动作集中在一个可审计的点 |

**这个版本其实比原设计更强**：原设计依赖"钩子会拦住"，新设计是"根本没有第二条路"。

### 连带修订

`../expert-team/orchestration/pipeline.yaml` 的 INV-3 表述应理解为：
**平台必须能提供一条"唯一的、内含确定性校验的发布通道"**，而不是"必须有可阻断的钩子"。
OpenClaw 用沙箱 + 工具权限 + 发布脚本满足了这条要求。

---

## 4. 其余适配决策

### 4.1 阶段硬门由总调度承担

OpenClaw 没有 BPMN 式的阶段网关。准入条件写在 `playbook.md` 里，由总调度执行。
**这是本方案最薄的一环**——它依赖总调度遵守自己的手册，属于模型自觉，不是机制保证。

缓解措施：
- `run-ledger` hook 把阶段事件写成 JSONL 台账，事后可审计"P5 是不是真的止于 2 轮"
- 关键的不可逆动作（P0 冻结、P9 归档）设人工签署
- 真正致命的那道闸（数字校验）已经落到机制上，不依赖总调度自觉

### 4.2 派发深度设为 2

| 事实 | 影响 |
|---|---|
| `maxSpawnDepth` 默认 1，depth-1 是叶子，**不被授予 `sessions_spawn`** | 默认配置下数据采集专家无法 fan-out |
| depth-1 只有在 `maxSpawnDepth >= 2` 时才拿到 `sessions_spawn` | 所以配置里设为 **2** |
| depth-2 是叶子，无 session 工具，不能再派子 | 采集工蜂只干活，不再分叉 |

拓扑：`洞察总调度(0) → 11 位专家(1) → 采集工蜂(2，仅数据采集专家可派)`。

### 4.3 派发白名单必须显式配置

文档：**默认只有请求方自己能被派发**。不设 `allowAgents`，总调度谁也派不动。
所以配置里给总调度列了全部 11 个专家，给数据采集专家只列了它自己。
同时 `requireAgentId: true`，禁止不指名的模糊派发。

### 4.4 并发额度上调

| 参数 | 默认 | 本方案 | 理由 |
|---|---|---|---|
| `maxChildrenPerAgent` | 5 | 20（上限） | Top K=6 的深度阶段 + 采集 fan-out |
| `maxConcurrent` | 8 | 12 | 全局车道；**受你的模型速率限制约束，需实测回调** |
| `announceTimeoutMs` | 120000 | 600000 | 取证类任务远超 2 分钟 |
| `archiveAfterMinutes` | 60 | 240 | 长批次中途不要把子会话归档掉 |

### 4.5 thinking 档位有精度损失

OpenClaw 的 `thinkingDefault` 是 `off / low / medium / high / adaptive`，**没有 `xhigh` / `max`**。
原方案给分析专家、质疑审查专家、仲裁专家配的是 `xhigh` / `max`，在这里只能落到 `high`。

影响：这几个角色的推理深度低于原设计。若质量不达标，可考虑的补偿手段（按优先级）：
1. 把 `thinkingDefault` 改为 `adaptive`，让模型自己决定深度
2. 在任务描述里显式要求"先列出你要检查的每一项，再逐项作答"
3. 换更强的模型（质疑审查专家已用 `claude-fable-5`）

### 4.6 会话与消息策略

- `session.reset.mode: "off"`——洞察流水线是长任务，按日重置会切断批次上下文
- `messages.queue.mode: "followup"`——默认的 `steer` 会把新消息注入正在跑的 run，可能污染阶段产出
- `contextInjection: "always"`——保证长流水线中途不丢角色约束与护栏

### 4.7 引导文件体积

`bootstrapMaxChars` 默认 20000（单文件）、`bootstrapTotalMaxChars` 60000（合计）。
生成后的实际体积：多数专家 `SOUL.md` + `AGENTS.md` 合计约 9 KB，**洞察总调度约 18 KB**（含运行手册）。

⚠️ **总调度是唯一接近单文件上限的**。若后续往 playbook 里加内容，注意别把 `AGENTS.md` 顶过 20000 字符——
超了会被静默截断，而被截掉的通常是文件末尾的"我绝不做的事"。
`bootstrap-guardrails` hook 是针对这种情况的第二重保险。

---

## 5. 我无法从文档确认的点 —— 上线前必须校验

以下字段形态我**没有找到明确的官方示例**，是按同类字段的写法推断的。
上线前请执行 `openclaw config schema` 取当期 JSON Schema 逐项比对，**不要直接信我**。

| # | 待校验项 | 我采用的写法 | 风险 |
|---|---|---|---|
| 1 | `agents.entries.*.model` 的形态 | 对象 `{ "primary": "..." }`（与 `agents.defaults.model` 一致） | 若 entries 层实际接受裸字符串，需改为 `"model": "anthropic/claude-opus-5"` |
| 2 | 模型 ID 是否已在你的 provider 注册 | `anthropic/claude-opus-5` 等 | 文档说"裸 ID 需要 provider 匹配或显式 `provider/model`"。你的 provider 命名可能不是 `anthropic` |
| 3 | `tools.deny` 的合法工具名 | `["exec"]` | 工具名清单未在文档中穷举，`exec` 来自社区配置示例 |
| 4 | `bindings.match.channel` 的合法取值 | 占位 `<CHANNEL>` | 需填你实际启用的通道 |
| 5 | `session.reset.mode: "off"` 是否合法 | `"off"` | 文档只举了 `daily` 与 idle，`off` 是推断 |
| 6 | hook handler 的模块导出形态 | 同时 `module.exports` 与 `.default` | 文档示例用 `export default`（TS）；为兼容 CJS 两种都导出 |
| 7 | `agents.defaults.skills: []` 的语义 | 空数组 = 不启用任何 skill | 可能空数组与"未设置"语义不同 |

**校验方法**：先 `./install.sh`（预演，不改你的配置），拿到 `openclaw.config.generated.json`，
逐项对照 `openclaw config schema` 的输出，改完 `openclaw.config.json5` 再 `./install.sh --merge`。

---

## 6. 参考来源

- [Configuration — agents](https://docs.openclaw.ai/gateway/config-agents)
- [Sub-agents](https://docs.openclaw.ai/tools/subagents)
- [Multi-agent routing](https://docs.openclaw.ai/concepts/multi-agent)
- [Configuration reference](https://docs.openclaw.ai/gateway/configuration-reference)
- [Hooks](https://docs.openclaw.ai/automation/hooks)

（文档源文件位于 `github.com/openclaw/openclaw` 的 `docs/` 目录，查阅日期 2026-08-19。
本仓库不缓存其内容，上线前请以当期文档与 `openclaw config schema` 为准。）
