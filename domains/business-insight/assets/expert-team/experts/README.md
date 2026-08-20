# 12 位数字专家 · 平台中立正本

**这里是专家定义的唯一真相源。** 两个 harness 包只做装配，不复制内容——
改专家改这里，然后重跑对应 harness 的安装脚本。

- 层次划分为什么是这样：[`../BOUNDARIES.md`](../BOUNDARIES.md) ← **先读这个**
- 骨架（十动作 + 五回边）：[`../../insight-service/spine.md`](../../insight-service/spine.md)
- OpenClaw 装配：[`../../expert-team-openclaw/`](../../expert-team-openclaw/)
- dsh 装配：[`../../expert-team-dsh/`](../../expert-team-dsh/)

## 名册

| agentId | 角色 | 动作 | 算力档 | 可派发 | 可选 |
|---|---|---|---|---|---|
| `chief-coordinator` | 🧭 洞察总调度 | 全程 | high | 全部 11 位 | 否 |
| `insight-planner` | 🗺️ 洞察规划专家 | ① 界定（含分诊） | high | — | 否 |
| `scope-definer` | 🔭 范围界定专家 | ② 枚举 | low | — | 否 |
| `data-collector` | 🔍 数据采集专家 | ③ 取证 | low | 随平台变 | 否 |
| `fact-verifier` | ✅ 数据核证专家 | ④ 核证 | low | — | 否 |
| `comparative-analyst` | 📊 对比分析专家 | ⑤ 刻画 ⑥ 聚合 | high | — | 否 |
| `domain-analyst` | ⚙️ 领域分析专家 | ⑤ 刻画（领域维度） | high | — | **是** |
| `compliance-reviewer` | 🛡️ 合规审查专家 | 闸门 + 合规维度 | high | — | **是** |
| `red-team-challenger` | 🥊 质疑审查专家 | ⑦ 证伪 | **max** | — | 否 |
| `arbiter` | ⚖️ 争议仲裁专家 | ⑧ 仲裁 | high | — | 否 |
| `insight-director` | 🎯 首席洞察专家 | ⑨ 解读 | **max** | — | 否 |
| `report-writer` | 📝 报告生成专家 | ⑩ 成文 | low | — | 否 |

**最难的两个判断——推翻结论、解读意味着什么——拿到最高算力档。** 这是刻意的。

## 每位专家的目录长什么样

```
<agentId>/
├── expert.yaml     T1 装配意图：算力档 / 隔离要求 / 工具面 / 派发白名单 / 闸门 / 禁令
│                       —— 平台中立。它说"应该被强制成什么"，不说字段名。
├── IDENTITY.md     T2 我是谁（名字、emoji、在骨架里的位置）
├── SOUL.md         T2 我的立场、KPI、不可说服的规则、绝不做的事
├── AGENTS.md       T2 我的输入输出、schema、交接契约、何时去读技能
├── skills/
│   └── <skill>/SKILL.md   T3 操作流程：清单、判定表、正反例（按需加载）
└── README.md       一页纸：边界一句话 + 怎么验收它装对了
```

`_shared/` 三份是全员共用的：

| 文件 | 用途 | 落到哪 |
|---|---|---|
| `GUARDRAILS.md` | 全员护栏（数字纪律、事实/判断分离、角色边界） | 内联进每位专家的人格层最前面 |
| `USER.md` | 委托方模型（稳定偏好，指令式条目） | OpenClaw 直接作 `USER.md`；dsh 拼进 prompt |
| `BATCH-LAYOUT.md` | 批次目录约定 | 由总调度在派发时给出路径 |

## 工具面一览（这是 T1 里最容易被忽略的一列）

| 专家 | browser | exec | 为什么 |
|---|---|---|---|
| `chief-coordinator` | ❌ | ✅ | 唯一能执行发布脚本的角色；反过来不许联网，避免它顺手做内容 |
| `insight-planner` | ✅ | ❌ | 只用于分诊第三问（有没有未过期的同题结论） |
| `scope-definer` | ✅ | ❌ | 打开目录、查条目 |
| `data-collector` | ✅ | ❌ | 取证的主要工具 |
| `fact-verifier` | ✅ | ❌ | 只用于打开证据卡已给出的 URL 回源 |
| `comparative-analyst` | ❌ | ❌ | **刻意剥夺**——能检索就会"顺手查一下"，同时绕过取证与核证两道闸 |
| `domain-analyst` | ❌ | ❌ | 同上 |
| `compliance-reviewer` | ✅ | ❌ | **唯一被授予联网的分析类角色**——管制清单凭记忆作答是最高风险动作 |
| `red-team-challenger` | ❌ | ❌ | 能自己补证的红队会变成"自己补证再自己认可" |
| `arbiter` | ❌ | ❌ | "禁止自行补证"从纪律变成机制 |
| `insight-director` | ❌ | ❌ | "禁止引入新的事实性数字"从纪律变成机制 |
| `report-writer` | ❌ | ❌ + 沙箱 | 权限最紧：写不到发布目录，也无法自己跑脚本绕过 |

> ⚠️ **这张表在 dsh 上落不下去。** dsh 的队友共用 Lead 的组合，无法逐队友收窄工具面。
> 详见 `../BOUNDARIES.md` 第五节与 `../../expert-team-dsh/DSH-NOTES.md`。

## 改东西改哪儿

| 想改什么 | 改哪个文件 | 之后要做什么 |
|---|---|---|
| 某位专家的立场、禁令 | `<id>/SOUL.md` | 重跑对应 harness 的安装脚本 |
| 某位专家的输入输出契约 | `<id>/AGENTS.md` | 同上 |
| 某个操作流程、判定表 | `<id>/skills/<skill>/SKILL.md` | 同上 |
| 算力档、工具面、派发白名单 | `<id>/expert.yaml` **和**对应 harness 的 `entry.json5` / `spawn.json` | **两处都要改**——yaml 是意图，harness 文件是真实字段 |
| 全员护栏 | `_shared/GUARDRAILS.md` | 同上 |
| 增删一位专家 | 新建目录 + 改两个 harness 包的 `experts/` + 改本表 | 同上 |

`expert.yaml` 与 harness 侧的实际配置**故意分成两份**：
前者是可读的意图（"这个角色不该能联网"），后者是各平台的真实字段（`tools.deny: ["browser"]`）。
合并成一份就意味着要么丢掉可读性，要么在平台字段变化时全体返工。
