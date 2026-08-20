# ⚙️ 领域分析专家

| | |
|---|---|
| agentId | `domain-analyst` |
| 动作 | ⑤ 刻画（`ownerRole=domain-analyst` 的维度） |
| 算力档 | high |
| 可派发 | 无（叶子） |
| 技能 | `assess-capability-overlap` |
| 可选 | **是**——`brief.domainPack` 为空时不派发 |

## 边界（一句话）

**它只碰属于自己 ownerRole 的维度，一格都不多碰。**

## 什么时候需要它

- 产业机会筛选、技术路线评估 → 需要
- 工具/产品的现状调研（对比维度都是通用的） → 通常不需要

判断依据只有一条：`brief.domainPack` 里有没有东西。没有就别派——
没有领域知识的领域分析专家，不比通用分析强，只是多花一份钱。

## 怎么验收它装对了

1. 看 `sub_capability_hits` 是否填全。空着就是给了印象分。
2. 抽查判 `direct` 的项，理由是否具体到技术点。写"同属精密制造"就是没装对。
3. 看它有没有碰别的 `ownerRole` 的维度。
4. 把 `domainPack.lastReviewed` 改成过期日期，看它有没有在产出里标记。
