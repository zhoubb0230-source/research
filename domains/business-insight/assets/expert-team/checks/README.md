# 防编造第三道闸 · 确定性校验

## 为什么这道闸必须是代码

前两道闸（schema 强制引用、核证官回源）都由模型执行，模型可以被绕过、被说服、被"这次情况特殊"说动。这一道是脚本——它不会被说服，也不该被说服。

`pipeline.yaml` 的 INV-3 把它定为平台选型的硬性验收点：**做不到渲染前执行确定性校验钩子的平台不能用。**

## 用法

```bash
python3 verify_report.py <报告.md> <evidence.jsonl> [--json] [--rubric rubric-v1]
```

退出码：`0` 通过 / `1` 存在违规（报告不予发布）/ `2` 用法或读写错误。

无第三方依赖，Python 3.9+。

## 校验规则

报告正文中每个「数据型数字」（数字 + 单位或百分号）必须满足：

1. 同一行携带 `EV-YYYY-NNNN` 形式的引用；
2. 该 `evidence_id` 存在于证据库；
3. 该证据 `verify_status == "verified"`；
4. 报告中的数值与证据卡记录的数值一致。

## 违规类型

| 类型 | 含义 |
|---|---|
| `MISSING_CITATION` | 数字没有引用。最常见，通常是渲染器为了行文顺畅自己补的数 |
| `UNKNOWN_EVIDENCE` | 引用了不存在的 evidence_id。典型的编造引用 |
| `UNVERIFIED_EVIDENCE` | 引用的证据未通过核证。只有 `verified` 可用 |
| `VALUE_MISMATCH` | 数值与证据卡不符。多为口径换算错误或抄写错误 |

## 警告（不阻断）

| 类型 | 含义 |
|---|---|
| `CJK_NUMERAL` | 数据以中文数字书写。渲染器被禁止把数字改写成文字——这是绕过校验的典型手法，需人工确认 |

## 豁免机制

| 场景 | 写法 |
|---|---|
| 口径值（权重、阈值、锚点数字，来自 rubric 而非证据库） | 该行出现 `rubric-v1` 标记即豁免 |
| 引用经纬线原文、方法学说明等非数据段落 | 用 `<!-- verify:ignore-start -->` / `<!-- verify:ignore-end -->` 包裹 |
| 代码块、表格分隔行、标题编号、脚注定义行 | 自动跳过 |
| YAML frontmatter | 自动跳过 |

**豁免机制只用于确实不是产业数据的数字。** 用 ignore 块包住真实数据段落来让校验通过，等于关掉了这道闸——评审时应检查 ignore 块的用法。

## 夹具

`fixtures/` 下是自测夹具，**其中所有数字均为占位示例，不是任何真实产业数据**。

```bash
python3 verify_report.py fixtures/report.pass.sample.md fixtures/evidence.sample.jsonl   # exit 0
python3 verify_report.py fixtures/report.fail.sample.md fixtures/evidence.sample.jsonl   # exit 1，四类违规各一
```

## 已知局限

- 只校验数字，不校验实体名（公司名、产品名）与因果断言。这两类编造需靠 A2 首席洞察官与人工复核发现。
- 口径一致性（全球 vs 中国大陆、行业 vs 设备）不在校验范围——数值对得上但口径错了，脚本查不出来。这是 C2 核证官的职责。
- 中文数字只警告不阻断，需人工确认。
