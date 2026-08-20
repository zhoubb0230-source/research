# 业务洞察专家团 · DeepSeek Harness 交付件

**直接复制即可用，不需要跑任何安装脚本。**

- 骨架正本：[`../insight-service/spine.md`](../insight-service/spine.md)（十动作、五回边）
- 平台事实与待校验项：[`DSH-NOTES.md`](DSH-NOTES.md)
- 验收契约：[`../insight-service/acceptance.md`](../insight-service/acceptance.md)

---

## 一、agent 与 skill 的边界

这是本交付件最重要的设计约定。**弄错了，防编造机制会静默失效。**

### 判据一：常驻，还是按需触发？

| | 性质 | 放哪 |
|---|---|---|
| **Persona** | **常驻**。这个 agent 从建立到销毁一直遵守 | `agents/<id>/persona.md` |
| **Skill** | **按需**。遇到特定子任务才被调用 | `skills/<name>/SKILL.md` |

### 判据二：身份禁令，还是作业程序？

| | 内容 | 放哪 |
|---|---|---|
| 我是谁、我的**认知姿态** | 不可协商 | persona |
| 我**绝不做**什么（护栏） | 不可协商 | persona |
| 我的输入输出契约 | 不可协商 | persona |
| "遇到 X 时，按这几步做 Y" | 情境化的方法 | skill |

### ⚠️ 护栏必须在 persona，不能做成 skill

官方文档对 skill 的定义是「可扩展 agent 能力的**可选指令**」——**可选**意味着模型可以不调用它。

**把「禁止编造数据」做成一个 skill，等于把它变成可选项。** 防编造是本系统全部价值的地基，
它必须常驻在每个 persona 里，随 `spawnTeammate` 的 prompt 一起绑死。

### 复用不是判据

skill **可以是专属的**。`falsification-memo` 只有质疑审查专家会用，但它依然是 skill——
因为它是「开始质疑前先写备忘录」这样一个**有明确触发时机的作业程序**，不是"我是谁"。

本交付件 13 个 skill 里 10 个是专属的。这是正常的，不是设计缺陷。

---

## 二、12 个专家的核心差异

多 agent 的价值来自**互斥的认知姿态**之间的张力。如果 12 个都是"严谨、有帮助的助手"，
那就是一个 agent 跑了 12 遍，只剩成本没有收益。

| 专家 | 动作 | **核心认知姿态**（persona 的第一段） |
|---|---|---|
| 🧭 洞察总调度 | 全程 | **不判断内容**。只管状态推进与回退路由，任何内容判断都是越权 |
| 🗺️ 洞察规划专家 | ① 界定 | **先劝退**。默认这个需求不该进专家团，直到它证明自己是决策问题 |
| 🔭 范围界定专家 | ② 枚举 | **不筛选**。宁滥勿缺，任何"我觉得这个不行"都是越权 |
| 🔍 数据采集专家 | ③ 取证 | **不推理**。看到什么记什么，找不到就是找不到 |
| ✅ 数据核证专家 | ④ 核证 | **不信任**。默认送来的每条证据都是错的，直到回源命中 |
| 📊 对比分析专家 | ⑤⑥ 刻画聚合 | **只在证据上推理**。不取数、不质疑、不解读 |
| ⚙️ 领域分析专家 | ⑤ 领域维度 | **只谈自己懂的**。领域包没覆盖的，一律交回 |
| 🛡️ 合规审查专家 | 闸门 | **不凭记忆**。任何判定没有原文条目定位就是 undetermined |
| 🥊 质疑审查专家 | ⑦ 证伪 | **敌意**。目标是推翻，不是完善。没推翻任何东西就是失职 |
| ⚖️ 争议仲裁专家 | ⑧ 仲裁 | **不站队**。只看证据等级，不看谁说得多、谁先说 |
| 🎯 首席洞察专家 | ⑨ 解读 | **越界但标注**。唯一被允许超出证据说"所以我们该……"的角色 |
| 📝 报告生成专家 | ⑩ 成文 | **不思考**。只改措辞，语义强度一个字都不能动 |

**自检**：把任意两个 agent 的 persona 对调，产出应该明显变差。
如果对调了没影响，说明这两个没有核心差异，应该合并。

---

## 三、目录

```
expert-team-dsh/
├── README.md              本文件（边界判据 + 核心差异）
├── DSH-NOTES.md           平台事实、适配决策、待校验项
├── INSTALL.md             手工安装步骤（复制，不跑脚本）
├── cordis.patch.yml       agent 声明与 provider 配置
│
├── agents/                ← 每个专家一个目录
│   └── <agentId>/
│       ├── agent.json     身份与运行参数（模型、effort、动作、要挂的 skill）
│       └── persona.md     认知姿态 + 禁令 + 契约 ← 传给 spawnTeammate 的 prompt
│
├── skills/                ← 按需调用的作业程序
│   └── <skill-name>/
│       └── SKILL.md
│
├── verify_package.py      交付件自检（检查这套文件是否自洽，不安装任何东西）
└── bin/                   发布闸（唯一的报告落盘通道）
    ├── publish_report.py
    ├── publish-report.ps1
    └── publish-report.sh
```

## 四、13 个 skill 与触发时机

| skill | 什么时候被调用 | 谁会用 |
|---|---|---|
| `insight-brief-authoring` | 要把需求写成任务包时 | 洞察规划专家 |
| `catalog-enumeration` | 要从目录穷举对象时 | 范围界定专家 |
| `evidence-card-writing` | 要记录一条证据时 | 数据采集专家 |
| `source-back-verification` | 要核对一条证据时 | 数据核证专家 |
| `dimension-scoring` | 要给一个维度赋值时 | 对比分析、领域分析 |
| `aggregation-operators` | 要把刻画折叠成结论时 | 对比分析专家 |
| `export-control-lookup` | 要判定管制状态时 | 合规审查专家 |
| `falsification-memo` | 开始质疑前 | 质疑审查专家 |
| `challenge-typing` | 给质疑归类（决定回退路由）时 | 质疑审查、总调度 |
| `arbitration-ruling` | 要裁决一条分歧时 | 争议仲裁专家 |
| `implication-drafting` | 要产出启示时 | 首席洞察专家 |
| `report-rendering` | 要渲染报告时 | 报告生成专家 |
| `rework-dispatch` | 收到质疑要派返工时 | 洞察总调度 |

## 五、拿到手先跑一次自检

```
python verify_package.py
```

它不安装任何东西，只检查这套文件本身：agent.json 合法性、persona 存在且含
「认知姿态」与「绝不做的事」、skill 引用完整、frontmatter 合规、kebab-case、
**SKILL.md 无 BOM**（BOM 会让 dsh 静默忽略这个 skill）。

安装步骤见 [`INSTALL.md`](INSTALL.md) —— 全是复制文件与改配置，不跑脚本。

## 六、关于本目录中的数字

不含任何真实产业数据或产品数据。出现的数字只有配置参数（并发、返工预算、effort 档位）
与判据阈值。真实数据只能由专家团在运行时带来源产出，经 `bin/` 下的发布闸校验后入库。
