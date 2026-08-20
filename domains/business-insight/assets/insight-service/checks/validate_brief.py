#!/usr/bin/env python3
"""洞察任务包校验器。

JSON Schema 管字段形态，本脚本管**跨字段一致性**——算子与维度是否匹配、
对象来源与算子是否匹配、退化是否已声明、领域包是否缺失。

这些错误不会让任务包"看起来不合法"，但会让洞察跑出无意义的结果：
比如声明了 rank 算子却一个 ordinal 维度都没有，系统会照跑，然后给出一个全是 NA 的榜单。

用法:
    python3 validate_brief.py <brief.json> [<brief.json> ...] [--json]

退出码: 0 通过（可含警告）｜1 存在错误｜2 用法或读写错误
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "schemas" / "brief.schema.json"


class Result:
    def __init__(self, name: str):
        self.name = name
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, code: str, msg: str) -> None:
        self.errors.append(f"[{code}] {msg}")

    def warn(self, code: str, msg: str) -> None:
        self.warnings.append(f"[{code}] {msg}")


def schema_check(brief: dict, r: Result) -> None:
    """有 jsonschema 就做完整校验；没有就跳过（跨字段规则不依赖它）。"""
    try:
        import jsonschema  # type: ignore
    except ImportError:
        r.warn("SCHEMA-SKIP", "未安装 jsonschema，跳过字段形态校验（跨字段规则仍已执行）")
        return
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for e in sorted(validator.iter_errors(brief), key=lambda x: list(x.path)):
        loc = "/".join(str(p) for p in e.path) or "(root)"
        r.err("SCHEMA", f"{loc}: {e.message}")


def cross_field_check(b: dict, r: Result) -> None:
    dims = {d["id"]: d for d in b.get("criteria", {}).get("dimensions", [])}
    ordinals = [d for d in dims.values() if d.get("type") == "ordinal"]
    categoricals = [d for d in dims.values() if d.get("type") == "categorical"]
    ops = [a.get("operator") for a in b.get("aggregation", [])]
    src = b.get("subject", {}).get("source", {})
    src_type = src.get("type")
    degraded = {d.get("action") for d in b.get("degradations", [])}

    # ---- 对象来源与其必填项 ----
    need = {
        "catalog_enumeration": ("catalogs", "目录穷举必须列出要扫的目录，否则枚举无从谈起也无法回溯"),
        "given": ("givenList", "given 来源必须给出对象清单"),
        "baseline": ("baselineRef", "baseline 来源必须指向上一批次产出"),
    }
    if src_type in need:
        field, why = need[src_type]
        if not src.get(field):
            r.err("SRC-1", f"subject.source.type={src_type} 但缺 {field} —— {why}")

    # ---- 算子与维度的匹配 ----
    for agg in b.get("aggregation", []):
        op = agg.get("operator")
        cfg = agg.get("config") or {}

        if op == "rank":
            if not ordinals:
                r.err("AGG-RANK-1", "算子 rank 需要至少 1 个 ordinal 维度，当前一个都没有——会跑出全 NA 的榜单")
            missing_w = [d["id"] for d in ordinals if d.get("weight") is None]
            if missing_w:
                r.err("AGG-RANK-2", f"算子 rank 下这些 ordinal 维度缺 weight: {', '.join(missing_w)}")
            weights = [d.get("weight", 0) for d in ordinals if d.get("weight") is not None]
            if weights and abs(sum(weights) - 100) > 1e-6:
                r.err("AGG-RANK-3", f"ordinal 维度 weight 之和为 {sum(weights)}，应为 100")
            if not cfg.get("confidenceLayering", True):
                r.warn("AGG-RANK-4", "关闭了置信度分层。高分+低置信度最可能是「缺失数据被乐观填充」，不建议关闭")

        elif op == "cluster":
            by = cfg.get("byDimension")
            if not by:
                r.err("AGG-CLUSTER-1", "算子 cluster 必须指定 config.byDimension")
            elif by not in dims:
                r.err("AGG-CLUSTER-2", f"config.byDimension={by} 不在维度列表中")
            elif dims[by].get("type") != "categorical":
                r.err("AGG-CLUSTER-3", f"分组维度 {by} 的类型是 {dims[by].get('type')}，cluster 要求 categorical")
            if not categoricals:
                r.err("AGG-CLUSTER-4", "算子 cluster 需要至少 1 个 categorical 维度")

        elif op == "matrix":
            if len(dims) < 2:
                r.err("AGG-MATRIX-1", f"算子 matrix 需要 ≥2 个维度，当前 {len(dims)} 个")
            if cfg.get("emptyCellPolicy") not in (None, "must-mark-unknown"):
                r.warn("AGG-MATRIX-2", "矩阵空白单元会被读者默认理解为「否」，建议 emptyCellPolicy=must-mark-unknown")

        elif op == "diff":
            if src_type != "baseline":
                r.err("AGG-DIFF-1", f"算子 diff 要求 subject.source.type=baseline，当前为 {src_type}")
            if not (cfg.get("baselineRef") or src.get("baselineRef")):
                r.err("AGG-DIFF-2", "算子 diff 必须给出 baselineRef")

        elif op == "rank_hypotheses":
            if src_type != "hypothesis_generation":
                r.err("AGG-HYP-1", f"算子 rank_hypotheses 要求 source.type=hypothesis_generation，当前为 {src_type}")

    # ---- 闸门 ----
    for g in b.get("criteria", {}).get("gates", []):
        if g.get("evaluateAfter") == "characterize":
            for dep in g.get("dependsOn", []) or []:
                if dep not in dims:
                    r.err("GATE-1", f"闸门 {g.get('id')} 依赖的维度 {dep} 不存在")
            if not g.get("dependsOn"):
                r.warn("GATE-2", f"闸门 {g.get('id')} 在 characterize 后判定却未声明 dependsOn，无法确认它依赖什么")
        if g.get("action") == "reject" and "数据" in (g.get("rule", "") + g.get("name", "")) and "可得" in (g.get("rule", "") + g.get("name", "")):
            r.err("GATE-3", f"闸门 {g.get('id')} 以数据可得性为由 reject。数据缺失是我们的信息问题，不是对象的质量问题，应用 defer")

    # ---- 退化必须声明 ----
    if not dims and "characterize" not in degraded:
        r.err("DEG-1", "dimensions 为空（刻画退化为事实摘录），必须在 degradations 中声明 action=characterize")
    if src_type == "given" and "enumerate" not in degraded:
        r.warn("DEG-2", "对象集合由需求方给定（枚举退化），建议在 degradations 中声明，报告需说明不保证覆盖完整")
    if (b.get("subject", {}).get("cardinality") or {}).get("expected") == 1 and "enumerate" not in degraded:
        r.warn("DEG-3", "预期对象数为 1（枚举退化），建议在 degradations 中声明")
    for d in b.get("degradations", []):
        if not d.get("disclosure"):
            r.warn("DEG-4", f"退化 {d.get('action')} 未写 disclosure —— 降级必须可见，报告首屏要能说清影响")

    # ---- 领域包 ----
    dom_dims = [d["id"] for d in dims.values() if d.get("ownerRole") == "domain-analyst"]
    if dom_dims and not b.get("domainPack"):
        r.err("DOM-1", f"维度 {', '.join(dom_dims)} 指派给领域分析专家，但 domainPack 为空——它没有领域知识可用")
    comp_dims = [d["id"] for d in dims.values() if d.get("ownerRole") == "compliance"]
    if comp_dims:
        r.warn("DOM-2", f"维度 {', '.join(comp_dims)} 需要合规审查专家，运行前确认该可选角色已启用")

    # ---- 证据政策 ----
    ep = b.get("evidencePolicy", {})
    dv = ep.get("directVerification") or {}
    if dv.get("required") and not dv.get("methods"):
        r.err("EV-1", "directVerification.required=true 但未给出 methods，无法执行")
    if dv.get("available") and not dv.get("required"):
        r.warn("EV-2", "对象可直接验证却未设为必需。直接验证是最强的一手证据，建议 required=true")
    if ep.get("minGrade") == "C" and not ep.get("crossCheckRequired", True):
        r.err("EV-3", "minGrade=C 且未要求交叉验证。C 级来源必须有独立交叉来源方可入表")
    grades = ep.get("grades") or {}
    if grades and not grades.get("A"):
        r.err("EV-4", "证据等级 A 的实例清单为空。等级机制通用，但每级的实例是领域专属的，必须由任务包声明")

    # ---- 时效 ----
    t = b.get("temporal") or {}
    max_age = ep.get("maxAgeMonths")
    if max_age and max_age > 12 and t.get("reportValidityMonths") and t["reportValidityMonths"] < 6:
        r.warn("TMP-1", "证据最大年龄较宽但报告有效期很短，二者不匹配，检查是否写反")
    if t.get("horizonMonths") and not t.get("lookbackMonths"):
        r.warn("TMP-2", "声明了前瞻窗口却没有回溯窗口——趋势判断需要历史依据，否则只能是猜测")

    # ---- 决策问题 ----
    dq = b.get("decisionQuestion", "")
    if dq and not any(k in dq for k in ("？", "?", "是否", "该", "哪", "应")):
        r.warn("DQ-1", "decisionQuestion 读起来不像一个决策问题。答不上「这支持什么决策」的多半是检索需求，应在分诊环节拦下")

    # ---- 其他 ----
    topk = (b.get("subject", {}).get("cardinality") or {}).get("topK")
    if topk and "rank" not in ops:
        r.warn("MISC-1", f"设了 topK={topk} 但没有 rank 算子，无法确定「Top」按什么排")
    for d in ordinals:
        bad = [k for k in (d.get("anchors") or {}) if not k.lstrip("-").isdigit()]
        if bad:
            r.err("DIM-1", f"维度 {d['id']} 的锚点键不是数字: {', '.join(bad)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="洞察任务包校验")
    ap.add_argument("briefs", nargs="+", type=pathlib.Path)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    results = []
    for p in args.briefs:
        if not p.is_file():
            print(f"找不到文件: {p}", file=sys.stderr)
            return 2
        r = Result(p.name)
        try:
            brief = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            r.err("JSON", str(e))
        else:
            schema_check(brief, r)
            cross_field_check(brief, r)
        results.append(r)

    failed = any(r.errors for r in results)

    if args.as_json:
        print(json.dumps(
            {"passed": not failed,
             "results": [{"brief": r.name, "errors": r.errors, "warnings": r.warnings} for r in results]},
            ensure_ascii=False, indent=2))
        return 1 if failed else 0

    for r in results:
        status = "✗ 不通过" if r.errors else ("✓ 通过（有提示）" if r.warnings else "✓ 通过")
        print(f"\n── {r.name} ── {status}")
        for e in r.errors:
            print(f"   错误  {e}")
        for w in r.warnings:
            print(f"   提示  {w}")

    print()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
