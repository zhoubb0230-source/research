# 业务洞察专家团 · DeepSeek Harness 部署包

把 [`../expert-team/experts/`](../expert-team/experts/) 的 12 位专家装配到 dsh 上的
**可直接部署形态**。

| 读这个 | 干什么 |
|---|---|
| [`../expert-team/BOUNDARIES.md`](../expert-team/BOUNDARIES.md) | **先读。** 配置 / 人格 / 技能的三层边界 |
| [`DSH-NOTES.md`](DSH-NOTES.md) | **上线前必读。** 平台事实、**dsh 落不下去的三样东西**、四项待校验 |
| [`../expert-team/experts/README.md`](../expert-team/experts/README.md) | 12 位专家的名册 |

## 一句话：dsh 与 OpenClaw 的关键差异

**dsh 无法逐专家收窄工具面。** 队友共用 Lead 的 preset 组合与工作目录。

OpenClaw 版里"对比分析专家没有联网能力""报告生成专家写不到发布目录"是**机制**；
在 dsh 上它们退化成 `SOUL.md` 里的**承诺**。
验收方式必须跟着变——见 [`DSH-NOTES.md`](DSH-NOTES.md) §4。

## 目录

```
expert-team-dsh/
├── README.md                  本文件
├── DSH-NOTES.md               平台事实 / 能力缺口 / 待校验项 ← 上线前必读
├── orchestration/             【编排框架】
│   ├── cordis.patch.yml       宿主组合覆盖：provider 档位路由 + Lead + AGENTS.md 预算
│   │                          + 技能根 + agent-team 上限
│   └── preset/business-insight-team/
│       ├── agent.cordis.yml   preset 组合（全队共用）：护栏 persona + preset 自带技能根
│       └── preset.yml         展示元数据（只有 name 与 description）
├── experts/                   【12 位专家】每位一个独立目录
│   └── <agentId>/
│       ├── spawn.json         该专家的 spawnTeammate 实参（T1）
│       └── README.md          它的约束落在哪、哪些在 dsh 上落不下去
├── runtime/
│   ├── lead.md                dsh 运行约定（三个接口 / 名额 / 消息大小），拼进 Lead 人格
│   └── teammate.md            dsh 运行约定（fresh 上下文 / 共享 cwd），拼进队友人格
├── install.py                 ★ 装配逻辑（跨平台，已实测）
├── install.sh / install.ps1   薄封装：找 Python 然后转调
└── bin/
    ├── publish_report.py      ★ 发布闸逻辑（跨平台，已实测）
    └── publish-report.sh / .ps1
```

## 装配后的工作目录长什么样

```
<工作目录>/
├── AGENTS.md                     全队共用层：护栏 + 委托方模型 + 批次约定 + 三条编排铁律
│                                 （dsh 按目录加载，队友共享 cwd → 这是全队一份）
└── .dsh/
    ├── PROMPTS/<name>.md         12 位专家的人格正文 ← spawnTeammate(prompt) 的实参
    ├── skills/<skill>/SKILL.md   13 个技能（rank 100，优先级最高）
    └── roster.json               名册：name → 中文名 / provider 路由 / 人格文件 / 技能
```

**人格为什么是 `PROMPTS/*.md` 而不是配置**：`AgentOptions` 只有
`{ provider, model, maxTokens }` —— **没有 `prompt` 字段**。人格的唯一通道是
`spawnTeammate(prompt)`。这一点已从 `docs/subsystems/core.md` 确认。

**技能为什么是共用目录**：队友共用 Lead 的组合，无法逐队友给不同的技能表。
"谁该用哪个技能"写在各自的人格里。

## 12 位专家

| name | 角色 | 动作 | provider 路由 | context |
|---|---|---|---|---|
| `chief-coordinator` | 🧭 洞察总调度 | 全程（**Team Lead**） | `deepseek-high` | —（agent-loop 创建） |
| `insight-planner` | 🗺️ 洞察规划专家 | ① 界定（含分诊） | `deepseek-high` | `fresh` |
| `scope-definer` | 🔭 范围界定专家 | ② 枚举 | `deepseek-low` | `fresh` |
| `data-collector` | 🔍 数据采集专家 | ③ 取证 | `deepseek-low` | `fresh` |
| `fact-verifier` | ✅ 数据核证专家 | ④ 核证 | `deepseek-low` | `fresh` |
| `comparative-analyst` | 📊 对比分析专家 | ⑤ 刻画 ⑥ 聚合 | `deepseek-high` | `fresh` |
| `domain-analyst` | ⚙️ 领域分析专家（可选） | ⑤ 刻画（领域维度） | `deepseek-high` | `fresh` |
| `compliance-reviewer` | 🛡️ 合规审查专家（可选） | 闸门 + 合规维度 | `deepseek-high` | `fresh` |
| `red-team-challenger` | 🥊 质疑审查专家 | ⑦ 证伪 | **`deepseek-max`** | `fresh` |
| `arbiter` | ⚖️ 争议仲裁专家 | ⑧ 仲裁 | `deepseek-high` | `fresh` |
| `insight-director` | 🎯 首席洞察专家 | ⑨ 解读 | **`deepseek-max`** | `fresh` |
| `report-writer` | 📝 报告生成专家 | ⑩ 成文 | `deepseek-low` | `fresh` |

`context` 的合法取值是 **`fresh` | `fork`**，不是 `isolated`。

⚠️ **红队异源在 dsh 上默认不成立** —— `deepseek-max` 只换了 effort 档，模型家族没换。
要真正异源需要注册第二家 provider，见 `orchestration/cordis.patch.yml` 里 `redteam-alt` 那一段。

## 跑起来

### 前置

- dsh 可运行；`DEEPSEEK_API_KEY` 已设
- **Python 3.8+**（装配与校验脚本用，仅标准库）
- 一个工作目录（dsh 以最近的 `.git` 祖先为项目根）

### 步骤

```bash
cd domains/business-insight/assets/expert-team-dsh

# 1. 预演：看会生成哪些文件，不落盘
./install.sh /path/to/工作目录

# 2. 写入（可选 --preset 同时装 preset 目录）
./install.sh /path/to/工作目录 --write
./install.sh /path/to/工作目录 --write --preset ~/.dsh/.agent-presets

# 3. 复制配置覆盖，然后【务必】核对形状
cp orchestration/cordis.patch.yml <profile 目录>/
dsh --profile web --dump-config          # ← 形状错了不报错，只静默失效

# 4. 启动
npx @deepseek-ai/dsh web                 # http://127.0.0.1:3080
```

Windows：`.\install.ps1 <目录> -Write`，或直接 `python install.py <目录> --write`
（跨平台，行为完全一致；生成的文件统一 UTF-8 无 BOM、LF）。

若 PowerShell 拦执行策略，本会话临时放行即可：
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`。

### 第一次试跑用哪个需求

用 [`../insight-service/presets/landscape-survey.brief.json`](../insight-service/presets/landscape-survey.brief.json)（AI Coding 工具现状）。

理由是**可验证性**：你们自己就是这个领域的专家，报告出来五分钟就知道靠不靠谱——
哪家漏了、路线分错了、某个能力写错了，一眼可见。

```bash
python3 ../insight-service/checks/validate_brief.py \
        ../insight-service/presets/landscape-survey.brief.json
```

然后在 dsh UI 里对 `chief-coordinator` 发起需求。
**第一次对它说话时，把 `.dsh/PROMPTS/chief-coordinator.md` 的正文贴进去**——
Lead 不是 `spawnTeammate` 建的，它的人格要手动带入一次。

### 发布

```bash
./bin/publish-report.sh <草稿.md> <批次根>/evidence.jsonl <发布目录>
```

⚠️ **发布由人执行，不在 dsh 里跑。** preset 里刻意没装 bash/终端类工具，
所以没有任何一位专家能自己跑脚本绕过闸门。理由见 `DSH-NOTES.md` §5。

退出码非 0 = 没发布。正确处置是回边 R4 退回取证补证，**不是改措辞绕过**。

## 跑完怎么判断跑对了

照 [`../insight-service/acceptance.md`](../insight-service/acceptance.md) 走八项检验，一个下午做完。

八项里 V4（枚举召回，专家盲列 10 个再比对）与 V7（质疑有效性，至少 1 条"我没想到"）
最有信息量，也最容易被跳过。

**dsh 上要额外查的三项**（因为它们在这里是承诺不是机制）：

1. 对比分析专家的产出里，有没有不带 `evidence_id` 的数字 —— 它实际拿得到 web 工具
2. 报告生成专家有没有往批次目录以外的地方写文件
3. 质疑审查专家的模型是不是真的与刻画不同（默认**不是**）

## 与其他包的关系

| 包 | 用途 | 状态 |
|---|---|---|
| [`../insight-service/`](../insight-service/) | 骨架、任务包规范、算子、校验器 | 平台无关，正本 |
| [`../expert-team/`](../expert-team/) | **12 位专家的正本** + schema + 发布闸校验器 | 平台无关，正本 |
| [`../expert-team-openclaw/`](../expert-team-openclaw/) | OpenClaw 部署包 | 与本包**共用同一份专家正本**，名册已对齐 |
| 本包 | dsh 部署包 | 同上 |

## 关于本目录中的数字

不含任何真实产业数据或产品数据。出现的数字只有配置参数（并发、名额上限、
消息大小、effort 档位）。真实数据只能由专家团在运行时带来源产出，
经 `bin/publish-report.sh` 校验后入库。
