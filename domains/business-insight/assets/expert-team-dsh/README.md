# 业务洞察专家团 · DeepSeek Harness 试跑包

把 `../insight-service/` 的十动作骨架落到本地 dsh 上，用于**真实试跑**。

- 骨架正本：[`../insight-service/spine.md`](../insight-service/spine.md)
- 任务包规范：[`../insight-service/schemas/brief.schema.json`](../insight-service/schemas/brief.schema.json)
- **平台事实与待校验项：[`DSH-NOTES.md`](DSH-NOTES.md) ← 跑之前读这个**

## 12 位专家 ↔ 十个动作

| 动作 | 专家 | agentId | effort |
|---|---|---|---|
| 全程 | 🧭 洞察总调度 | `chief-coordinator` | high |
| ① 界定（含分诊） | 🗺️ 洞察规划专家 | `insight-planner` | high |
| ② 枚举 | 🔭 范围界定专家 | `scope-definer` | low |
| ③ 取证 | 🔍 数据采集专家 | `data-collector` | low |
| ④ 核证 | ✅ 数据核证专家 | `fact-verifier` | low |
| ⑤ 刻画 ⑥ 聚合 | 📊 对比分析专家 | `comparative-analyst` | high |
| ⑤ 刻画（领域维度） | ⚙️ 领域分析专家（可选） | `domain-analyst` | high |
| 闸门 + 合规维度 | 🛡️ 合规审查专家（可选） | `compliance-reviewer` | high |
| ⑦ 证伪 | 🥊 质疑审查专家 | `red-team-challenger` | **max** |
| ⑧ 仲裁 | ⚖️ 争议仲裁专家 | `arbiter` | high |
| ⑨ 解读 | 🎯 首席洞察专家 | `insight-director` | **max** |
| ⑩ 成文 | 📝 报告生成专家 | `report-writer` | low |

最难的两个判断——**推翻结论**和**解读意味着什么**——拿到最高算力档。

## 目录

```
expert-team-dsh/
├── README.md              本文件
├── DSH-NOTES.md           平台事实、适配决策、4 项待校验 ← 必读
├── roles.json             12 角色的装配元数据与附加契约
├── playbook.md            总调度的十动作 + 五回边运行手册
├── cordis.patch.yml       配置覆盖（**唯一形状待校验的文件**）
├── install.sh             从 ../expert-team/prompts/ 生成 skills 到 <项目>/.dsh/skills/
└── bin/publish-report.sh  唯一发布通道，内含数字校验
```

## 跑起来

### 前置

- dsh 可运行；`DEEPSEEK_API_KEY` 已设
- `python3`（校验脚本用，仅标准库）
- 一个工作目录（dsh 以最近的 `.git` 祖先为项目根）

### 步骤

```bash
cd domains/business-insight/assets/expert-team-dsh

# 1. 预演：看看会生成哪 12 个 skill，不落盘
./install.sh /path/to/你的工作目录

# 2. 写入 <工作目录>/.dsh/skills/
./install.sh /path/to/你的工作目录 --write

# 3. 合并配置覆盖，然后**务必**核对形状（见 DSH-NOTES.md §5）
cp cordis.patch.yml /path/to/你的工作目录/
dsh --profile web --dump-config

# 4. 启动
npx @deepseek-ai/dsh web        # http://127.0.0.1:3080
```

### 第一次试跑建议用哪个需求

用 `../insight-service/presets/landscape-survey.brief.json`（AI Coding 工具现状）。

理由是**可验证性**：你们自己就是这个领域的专家，报告出来五分钟就知道靠不靠谱——
哪家漏了、路线分错了、某个能力写错了，一眼可见。
换成产业机会筛选，要等几个月才知道对错，试跑就失去了意义。

它还有三个附加好处：证据可直接验证（装上跑一下就知道）、
产出可直接入 `domains/ai-coding/insights/`（那个领域现在是空的）、
成本比全量产业筛选低一个数量级。

```bash
# 校验任务包
python3 ../insight-service/checks/validate_brief.py \
        ../insight-service/presets/landscape-survey.brief.json
```

然后在 dsh UI 里调用 `insight-planner`（它是 `user-invocable`）发起 ① 界定。

### 发布

```bash
./bin/publish-report.sh <草稿.md> <批次根>/evidence.jsonl <发布目录>
```

退出码非 0 = 没发布。正确处置是回边 R4：退回 ③ 取证补证，**不是改措辞绕过**。

## 跑完怎么判断跑对了

**照 [`../insight-service/acceptance.md`](../insight-service/acceptance.md) 走八项检验，一个下午做完。**

系统质量是**当场可测**的——要等几个月的是"这个结论最终对不对"，不是"这套系统靠不靠谱"。
八项里 V4（枚举召回，专家盲列 10 个再比对）和 V7（质疑有效性，至少 1 条"我没想到"）
最有信息量，也最容易被跳过。

## 试跑时重点看这五件事

这套设计里有五个参数是我**猜的**，只有跑起来才知道对不对。请重点观察：

| 观察点 | 我的取值 | 怎么判断猜错了 |
|---|---|---|
| 返工预算 `perSubject` | 2 | 大量对象在耗尽预算后仍未解决 → 调高；几乎没用到 → 调低 |
| `topKBuffer` | 3 | 重排后仍频繁有未证伪对象进 Top K → 调高 |
| 单调收敛判据 | 每次返工须产新证据 | 是否出现"补证失败但其实只是慢了一步"的误判 |
| 枚举 effort = `low` | low | 人工抽查出局池，看有无误杀 |
| `maxParallelToolCalls` | 8 | 撞速率限制就调低 |

另外看两个**结构性**问题：

- **十个动作是不是真的够、有没有多**——尤其是"解读"是否真的产出了可用的启示，还是又变成了套话
- **五条回边会不会震荡**——特别是 R2（证伪→取证）和 R3（刻画→聚合）连锁触发时

## 与其他两个包的关系

| 包 | 用途 | 状态 |
|---|---|---|
| `../insight-service/` | 骨架、任务包规范、算子、校验器 | 平台无关，是正本 |
| `../expert-team/` | 角色提示词、证据 schema、发布闸校验脚本 | 平台无关，是正本 |
| `../expert-team-openclaw/` | OpenClaw 部署包 | **角色名尚未同步到通用骨架**，见 DSH-NOTES.md §4.2 |
| 本包 | dsh 试跑包 | 角色名已泛化，对齐十动作骨架 |

## 关于本目录中的数字

不含任何真实产业数据或产品数据。出现的数字只有配置参数（并发、返工预算、effort 档位）。
真实数据只能由专家团在运行时带来源产出，经 `bin/publish-report.sh` 校验后入库。
