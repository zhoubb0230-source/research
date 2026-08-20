# 业务洞察专家团 · OpenClaw 部署包

把 [`../expert-team/experts/`](../expert-team/experts/) 的 12 位专家装配到 OpenClaw 上的
**可直接部署形态**。

| 读这个 | 干什么 |
|---|---|
| [`../expert-team/BOUNDARIES.md`](../expert-team/BOUNDARIES.md) | **先读。** 配置 / 人格 / 技能的三层边界 |
| [`OPENCLAW-NOTES.md`](OPENCLAW-NOTES.md) | **上线前必读。** 平台事实、工作区文件全表、四项待校验 |
| [`../expert-team/experts/README.md`](../expert-team/experts/README.md) | 12 位专家的名册与工具面一览 |

## 目录

```
expert-team-openclaw/
├── README.md                  本文件
├── OPENCLAW-NOTES.md          平台事实 / 适配决策 / 待校验项 ← 上线前必读
├── openclaw.config.json5      【编排框架】agents.defaults + bindings + hooks + session
├── experts/                   【12 位专家】每位一个独立目录
│   └── <agentId>/
│       ├── entry.json5        该专家的 agents.entries 片段（T1 配置层）
│       └── README.md          它的 T1 约束落在哪个字段、怎么验收
├── runtime/
│   ├── coordinator.md         OpenClaw 运行约定（派发/等待/并发），追加到总调度的 AGENTS.md
│   └── leaf.md                OpenClaw 运行约定（完成即返回/隔离），追加到叶子的 AGENTS.md
├── install.py                 ★ 装配逻辑（跨平台，已实测）
├── install.sh                 薄封装：找 Python 然后转调
├── bin/publish-report.sh      唯一的报告发布通道（内含数字校验闸）
└── hooks/
    ├── bootstrap-guardrails/  引导期重新注入护栏（第二重保险，不是闸门）
    └── run-ledger/            阶段留痕，供批次复盘与成本归因
```

**`workspaces/` 与 `openclaw.config.generated.json` 是生成产物，不入库。**
人格与技能的正本只有一份，在 `../expert-team/experts/` —— 本包不复制它们。

## 装配后的工作区长什么样

`install.py` 为每位专家生成一个符合 OpenClaw 约定的工作区：

```
workspaces/<agentId>/
├── IDENTITY.md        ← experts/<id>/IDENTITY.md 原样
├── SOUL.md            ← _shared/GUARDRAILS.md 内联在最前 + experts/<id>/SOUL.md
├── AGENTS.md          ← experts/<id>/AGENTS.md + runtime/{coordinator,leaf}.md 追加在末尾
├── USER.md            ← _shared/USER.md（12 位共用）
├── BATCH-LAYOUT.md    ← _shared/BATCH-LAYOUT.md
└── skills/<skill>/SKILL.md   ← experts/<id>/skills/ 原样
```

**没有 `TOOLS.md`** —— OpenClaw 里工具约定是 `AGENTS.md` 的 `## Tools` 小节，
而且它**不控制工具可用性**，真正的约束在 `entry.json5` 的 `tools` 字段。
详见 `OPENCLAW-NOTES.md` §1.2。

**没有 `MEMORY.md`** —— 跨批次的记忆载体是 `baseline.json`，理由见 `OPENCLAW-NOTES.md` §1.4。

## 12 位专家

| agentId | 角色 | 模型 | thinking | 联网 | exec | 沙箱 |
|---|---|---|---|---|---|---|
| `chief-coordinator` | 🧭 洞察总调度 | opus-5 | high | ❌ | **✅ 唯一** | off |
| `insight-planner` | 🗺️ 洞察规划专家 | opus-5 | high | 检索 | ❌ | off |
| `scope-definer` | 🔭 范围界定专家 | sonnet-5 | low | 检索 | ❌ | off |
| `data-collector` | 🔍 数据采集专家 | sonnet-5 | low | **浏览器** | ❌ | off |
| `fact-verifier` | ✅ 数据核证专家 | sonnet-5 | low | 检索 | ❌ | off |
| `comparative-analyst` | 📊 对比分析专家 | opus-5 | high | ❌ | ❌ | off |
| `domain-analyst` | ⚙️ 领域分析专家 | opus-5 | high | ❌ | ❌ | off |
| `compliance-reviewer` | 🛡️ 合规审查专家 | opus-5 | high | **浏览器** | ❌ | off |
| `red-team-challenger` | 🥊 质疑审查专家 | **fable-5** | **max** | ❌ | ❌ | off |
| `arbiter` | ⚖️ 争议仲裁专家 | opus-5 | high | ❌ | ❌ | off |
| `insight-director` | 🎯 首席洞察专家 | **fable-5** | **max** | ❌ | ❌ | off |
| `report-writer` | 📝 报告生成专家 | haiku-4-5 | low | ❌ | ❌ | **all/rw** |

只有**洞察总调度**绑定到人类通道，其余 11 位仅作为 `sessions_spawn` 的目标存在。

`red-team-challenger` 的模型**必须**与 `comparative-analyst` / `domain-analyst` 不同——
异源是装配保证的，不是提示词自觉。

## 部署

### 前置

- OpenClaw gateway 可运行，`openclaw` CLI 在 PATH 中
- 已配置 provider，且上表的模型 ID 可用（见 `OPENCLAW-NOTES.md` §8 第 1 项）
- `python3` 3.8+（装配脚本与校验器用，仅标准库）、`node`（hooks 用）
- **报告生成专家的沙箱需要 Docker 或等价后端。** 没有的话看 `OPENCLAW-NOTES.md` §5 的降级方案，
  并如实知道它弱在哪

### 步骤

```bash
cd domains/business-insight/assets/expert-team-openclaw

# 1. 填占位符：<CHANNEL> / <ACCOUNT_ID> / <REPO>
#    install.py 会检查残留占位符并拒绝写入
$EDITOR openclaw.config.json5

# 2. 预演：生成 12 个工作区与严格 JSON 配置，不改动 ~/.openclaw
python3 install.py

# 3. 按 OPENCLAW-NOTES.md §8 逐项校验字段形态
openclaw config schema > /tmp/oc-schema.json

# 4. 确认无误后合并（自动备份原配置）
python3 install.py --merge

# 5. 重启 gateway 使 hooks 生效
```

Windows 上直接跑 `python install.py`，行为完全一致（脚本统一写 UTF-8 无 BOM、LF）。

### 验证

```bash
# 发布闸自测：pass 用例应 exit 0，fail 用例应 exit 1 且列出四类违规
cd ../expert-team/checks
python3 verify_report.py fixtures/report.pass.sample.md fixtures/evidence.sample.jsonl
python3 verify_report.py fixtures/report.fail.sample.md fixtures/evidence.sample.jsonl
```

**pass 用例返回非 0，或 fail 用例返回 0，都说明闸门坏了——先修闸门，不要开始跑批次。**

然后在通道里对洞察总调度发起一次洞察需求，确认它**派发洞察规划专家**去做 ① 界定，
而不是自己写任务包。

逐位专家的验收方法在各自的 `experts/<agentId>/README.md` 与
`../expert-team/experts/<agentId>/README.md` 里。

## 三条不可妥协的约束

1. **判据版本在一轮批次中途不得变更。** 变更必须递增版本号并整轮重跑。
2. **证伪硬上限 2 轮。** 由总调度计数并写入台账，`run-ledger` hook 供事后审计。
3. **发布闸没有旁路。** `bin/publish-report.sh` 退出码非 0 就是没发布。
   正确处置是回边补证，不是改措辞绕过、不是手工复制文件进发布目录。

## 关于本目录中的数字

**不含任何真实产业数据。** 出现的数字只有配置阈值（并发、深度、超时、字符预算）与模型档位。
真实数据只能由专家团在运行时带来源产出，经 `verify_report.py` 校验后入库。
