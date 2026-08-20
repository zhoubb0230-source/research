# 业务洞察专家团 · OpenClaw 部署包

把 `../expert-team/` 的平台中立设计落到 OpenClaw 上的**可直接部署形态**。

- 设计正本：`../../solutions/2026-08-19-business-insight-expert-team.md`
- 评分口径：`../../solutions/2026-08-19-opportunity-screening-rubric.md`
- 部署方案：`../../solutions/2026-08-19-openclaw-deployment.md`
- **平台约束与待校验项：`OPENCLAW-NOTES.md` ← 上线前必读**

## 12 位专家

| agentId | 角色 | 模型 | thinking | 阶段 | 职责一句话 |
|---|---|---|---|---|---|
| `chief-coordinator` | 🧭 洞察总调度 | opus-5 | high | P0–P9 | 推进状态机，不做内容判断 |
| `rubric-owner` | 📐 口径定义专家 | opus-5 | high | P0 | 经纬线 → 可计算评分卡 |
| `opportunity-scanner` | 🔭 机会枚举专家 | opus-5 | medium | P1 | 目录穷举，只管覆盖率 |
| `data-collector` | 🔍 数据采集专家 | sonnet-5 | medium | P3 P7 | 定向取证，产出证据卡不产出结论 |
| `industry-analyst` | 📊 产业分析专家 | opus-5 | high | P4 P7 | B/C/D/E 维 + g 修正项 |
| `techchain-analyst` | ⚙️ 技术链分析专家 | opus-5 | high | P4 P7 | A/F 维 + h 修正项（A 是最高权重 25） |
| `red-team-challenger` | 🥊 质疑审查专家 | fable-5 | high | P5 P7 | 推翻结论，KPI 是推翻数 |
| `fact-verifier` | ✅ 数据核证专家 | sonnet-5 | medium | P3 P7 | 回源核对，硬闸门 |
| `compliance-officer` | 🛡️ 合规管制专家 | opus-5 | high | P2 P4 P7 | 出口管制双向判定 + G-3/G-4 闸门 |
| `arbiter` | ⚖️ 争议仲裁专家 | opus-5 | high | P6 P7 | 按证据等级裁决，不投票不取中值 |
| `insight-director` | 🎯 首席洞察专家 | fable-5 | high | P8 | 只判「结论对决策有没有用」 |
| `report-writer` | 📝 报告生成专家 | haiku-4-5 | low | P8 | 只做措辞改写，不引入新数字 |

只有**洞察总调度**绑定到人类通道，其余 11 位仅作为子 Agent 被派发。

## 目录

```
expert-team-openclaw/
├── README.md                    本文件
├── OPENCLAW-NOTES.md            平台约束、适配决策、上线前待校验项 ← 必读
├── roles.json                   12 角色的 OpenClaw 装配元数据
├── openclaw.config.json5        主配置（带注释的人类可读主本）
├── playbook.md                  洞察总调度的阶段运行手册（含 sessions_spawn 实参）
├── install.sh                   生成 workspaces + 严格 JSON 配置 + 可选合并
├── templates/                   SOUL.md / AGENTS.md 渲染模板
├── bin/publish-report.sh        唯一的报告发布通道（内含数字校验闸）
└── hooks/
    ├── bootstrap-guardrails/    引导期注入共用护栏（第二重保险）
    └── run-ledger/              运行留痕，供批次复盘与成本归因
```

**`workspaces/` 与 `openclaw.config.generated.json` 是生成产物，不入库。**
正本是 `roles.json` + `../expert-team/prompts/`，克隆后跑 `./install.sh` 重新生成——
提交生成物会造成正副本漂移。

## 部署

### 前置

- OpenClaw gateway 可运行，`openclaw` CLI 在 PATH 中
- 已配置 Anthropic provider，且 README 表中的模型 ID 可用（见 `OPENCLAW-NOTES.md` §5 第 2 项）
- `python3`（校验脚本与 install.sh 用，仅标准库）、`node`（hooks 用）

### 步骤

```bash
cd domains/business-insight/assets/expert-team-openclaw

# 1. 填占位符：把 <CHANNEL> / <ACCOUNT_ID> 换成你实际的通道与账号
#    install.sh 会检查残留占位符并拒绝写入
$EDITOR openclaw.config.json5

# 2. 预演：生成 12 个 workspace 与严格 JSON 配置，不改动 ~/.openclaw
./install.sh

# 3. 按 OPENCLAW-NOTES.md §5 逐项校验字段形态
openclaw config schema > /tmp/oc-schema.json

# 4. 确认无误后合并（自动备份原配置）
./install.sh --merge

# 5. 重启 gateway 使 hooks 生效
```

### 验证

```bash
# 发布闸自测：pass 用例应 exit 0，fail 用例应 exit 1 且列出四类违规
cd ../expert-team/checks
python3 verify_report.py fixtures/report.pass.sample.md fixtures/evidence.sample.jsonl
python3 verify_report.py fixtures/report.fail.sample.md fixtures/evidence.sample.jsonl
```

在通道里对洞察总调度发起 P0，确认它按 `playbook.md` 派发口径定义专家而不是自己写 rubric。

## 三条不可妥协的约束

1. **rubric 版本在一轮筛选中途不得变更。** 变更必须递增版本号并整轮重跑，否则跨候选分数不可比。
2. **P5 对抗硬上限 2 轮。** 由总调度计数并写入台账，`run-ledger` hook 供事后审计。
3. **发布闸没有旁路。** `bin/publish-report.sh` 退出码非 0 就是没发布。正确处置是回上游补证，
   不是改报告措辞绕过、不是手工复制文件进发布目录。

## 关于本目录中的数字

**不含任何真实产业数据。** 出现的数字只有配置阈值（并发、深度、超时）与模型档位。
真实产业数据只能由专家团在运行时带来源产出，经 `verify_report.py` 校验后入库。
