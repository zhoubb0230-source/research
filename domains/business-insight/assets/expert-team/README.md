# 业务洞察专家团 · 可运行资产

设计说明见 `../../solutions/2026-08-19-business-insight-expert-team.md`；
评分方法学见 `../../solutions/2026-08-19-opportunity-screening-rubric.md`。

本目录是把设计落到可执行形态的全部资产。**平台中立**——不绑定任何厂商 DSL。

## 目录

```
expert-team/
├── rubric/
│   └── rubric-v1.yaml              # 闸门 + 权重 + 六档锚点（执行以此为准）
├── schemas/
│   ├── evidence.schema.json        # 证据卡（证据库的唯一记录单元）
│   ├── opportunity.schema.json     # 候选机会 + 闸门判定
│   ├── scorecard.schema.json       # 评分卡（数值字段强制绑定 evidence_ref）
│   └── verdict.schema.json         # 证伪备忘录 + 质疑 + 裁决
├── prompts/
│   ├── _shared-guardrails.md       # 全角色共用护栏（必须内联到每个角色）
│   └── 00–11-<role>.md             # 12 个角色的系统提示词
├── orchestration/
│   ├── pipeline.yaml               # 阶段 + 契约 + 准入条件
│   ├── model-routing.yaml          # 角色 → 模型 → 参数
│   └── README-platform-mapping.md  # 四类平台的落地映射与选型验收点
├── templates/
│   ├── longlist.md                 # 机会榜单
│   ├── opportunity-report.md       # 单机会深度洞察报告
│   └── evidence-card.md            # 证据卡填写指引与自检清单
├── checks/
│   ├── verify_report.py            # 渲染前确定性数字校验（防编造第三道闸）
│   ├── README.md
│   └── fixtures/                   # 自测夹具（数字均为占位示例）
└── data-sources/
    └── source-registry.md          # 数据源类型、等级判定与口径陷阱
```

## 装配顺序

1. **冻结口径**：按 `rubric/rubric-v1.yaml` 组织业务专家校准（流程见 solution-0002 §6），通过后填 `frozen_at` 并把 `status` 改为 `frozen`。**未冻结不得用于正式筛选。**
2. **建角色**：每个角色的系统提示词 = `prompts/_shared-guardrails.md` 全文内联 + `prompts/NN-*.md`。护栏放最前面，且置于提示词缓存断点之前。
3. **接 schema**：按 `orchestration/model-routing.yaml` 的 `structured_output` 字段，给对应角色挂上 `schemas/` 中的 JSON Schema，开启结构化输出与 `strict: true`。
4. **配模型**：按 `model-routing.yaml` 分配模型与 effort。**C1 红队必须与 S3/S4 异源。**
5. **建编排**：按 `orchestration/pipeline.yaml` 的阶段与准入条件建流程，参照 `README-platform-mapping.md` 映射到你选的平台。
6. **挂校验钩子**：P8 出口处接 `checks/verify_report.py`，退出码非 0 即阻断。**这一步不能省。**
7. **跑 P1 单机会打通**：先用 1 个已知机会端到端跑通，再放量。

## 三条不可妥协的约束

1. **rubric 版本在一轮筛选中途不得变更。** 变更必须递增版本号并整轮重跑，否则跨候选分数不可比。
2. **对抗阶段硬上限 2 轮**，由编排层强制计数，不依赖模型自觉。
3. **渲染校验没有旁路。** 不存在"人工确认后强推"。校验失败的正确处置是回上游补证，不是修改报告措辞绕过。

## 自测

```bash
cd checks
python3 verify_report.py fixtures/report.pass.sample.md fixtures/evidence.sample.jsonl   # 期望 exit 0
python3 verify_report.py fixtures/report.fail.sample.md fixtures/evidence.sample.jsonl   # 期望 exit 1
```

## 关于本目录中的数字

**本目录不含任何真实产业数据。** 出现的数字只有三类：rubric 中的口径阈值（业务侧设定的建议值）、模型价目（Claude API 首方费率，口径日期 2026-06-24）、夹具中的占位示例（显式标注）。真实产业数据只能由专家团在运行时带来源产出，并存入 `../evidence/<batch>/`。
