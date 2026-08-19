#!/usr/bin/env python3
"""渲染前的确定性数字校验 —— 防编造的第三道闸。

这道闸是代码不是模型：它不会被说服，也不该被说服。

规则：报告正文里出现的每一个「数据型数字」（带单位或百分号）都必须
  1) 在同一行（或同一表格单元格）携带引用标记 —— evidence_id 或 rubric 版本号；
  2) 该 evidence_id 在证据库中存在；
  3) 该证据的 verify_status == "verified"；
  4) 报告中的数值与证据卡记录的数值一致。

用法:
    python3 verify_report.py <report.md> <evidence.jsonl> [--json] [--rubric rubric-v1]

退出码:
    0  全部通过
    1  存在违规（报告不予发布）
    2  用法或读写错误
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ---------------------------------------------------------------------------
# 「数据型数字」的识别：数字 + 单位。纯序号、章节号、列表编号不在其列。
# ---------------------------------------------------------------------------
UNITS = [
    "亿元", "万元", "亿美元", "万美元", "亿", "万",
    "个百分点", "百分点", "家", "台", "套", "款", "人",
    "年", "个月", "月", "天", "倍", "元", "美元",
    "nm", "µm", "μm", "mm", "kW", "MW", "GW", "℃", "%",
]
_UNIT_ALT = "|".join(re.escape(u) for u in sorted(UNITS, key=len, reverse=True))

NUM = r"[0-9][0-9,]*(?:\.[0-9]+)?"
# 数字（可带范围 / 比较符）+ 紧邻单位
DATA_NUMBER_RE = re.compile(
    rf"(?P<full>(?:[≥≤><约]\s*)?(?P<num>{NUM})(?:\s*[-–~至]\s*{NUM})?\s*(?P<unit>{_UNIT_ALT}))"
)

EVIDENCE_REF_RE = re.compile(r"EV-\d{4}-\d{4}")
RUBRIC_REF_RE = re.compile(r"rubric-v\d+")

# 中文数字写法 —— 渲染器被禁止把数字改写成文字来绕过校验，这里做检测
CJK_NUMERAL_RE = re.compile(r"[一二三四五六七八九十百千]+\s*(?:亿|万)(?:元|美元)?")

IGNORE_START = "<!-- verify:ignore-start -->"
IGNORE_END = "<!-- verify:ignore-end -->"
FENCE_RE = re.compile(r"^\s*(```|~~~)")
TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
FOOTNOTE_DEF_RE = re.compile(r"^\s*\[\^[^\]]+\]:")


@dataclass
class Violation:
    line: int
    kind: str
    text: str
    detail: str

    def render(self) -> str:
        return f"  L{self.line:<5} [{self.kind}] {self.text}\n          {self.detail}"


@dataclass
class Report:
    violations: list[Violation] = field(default_factory=list)
    warnings: list[Violation] = field(default_factory=list)
    checked_numbers: int = 0
    evidence_loaded: int = 0

    def fail(self, *a) -> None:
        self.violations.append(Violation(*a))

    def warn(self, *a) -> None:
        self.warnings.append(Violation(*a))


def load_evidence(path: Path) -> dict[str, dict]:
    db: dict[str, dict] = {}
    with path.open(encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"证据库第 {lineno} 行不是合法 JSON: {exc}")
            eid = rec.get("evidence_id")
            if not eid:
                raise SystemExit(f"证据库第 {lineno} 行缺少 evidence_id")
            db[eid] = rec
    return db


def numeric_forms(rec: dict) -> set[str]:
    """证据卡中该条证据可接受的数值表述集合（归一化为无逗号字符串）。"""
    forms: set[str] = set()
    value = rec.get("value") or {}
    for key in ("raw", "normalized"):
        v = value.get(key)
        if v is None:
            continue
        s = str(v).replace(",", "").strip()
        forms.add(s)
        # 1200.0 与 1200 视为同一个数
        try:
            f = float(s)
            forms.add(f"{f:g}")
            if f.is_integer():
                forms.add(str(int(f)))
        except ValueError:
            # 原始表述可能是区间或含文字，从中抽出所有数字
            for m in re.finditer(NUM, s):
                forms.add(m.group(0).replace(",", ""))
    return forms


def normalize(num_text: str) -> str:
    s = num_text.replace(",", "").strip()
    try:
        f = float(s)
        return str(int(f)) if f.is_integer() else f"{f:g}"
    except ValueError:
        return s


def strip_frontmatter(lines: list[str]) -> int:
    """返回正文起始行索引（0-based）。"""
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return i + 1
    return 0


def check(report_path: Path, db: dict[str, dict], rubric: str | None) -> Report:
    out = Report(evidence_loaded=len(db))
    lines = report_path.read_text(encoding="utf-8").splitlines()
    start = strip_frontmatter(lines)

    in_fence = False
    in_ignore = False

    for idx in range(start, len(lines)):
        lineno = idx + 1
        line = lines[idx]

        if IGNORE_START in line:
            in_ignore = True
            continue
        if IGNORE_END in line:
            in_ignore = False
            continue
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or in_ignore:
            continue
        if TABLE_SEP_RE.match(line) or HEADING_RE.match(line) or FOOTNOTE_DEF_RE.match(line):
            continue

        # 中文数字改写检测（渲染器绕过校验的典型手法）
        for m in CJK_NUMERAL_RE.finditer(line):
            out.warn(lineno, "CJK_NUMERAL", m.group(0),
                     "数据以中文数字书写，无法自动核对。渲染器禁止把数字改写成文字。")

        matches = list(DATA_NUMBER_RE.finditer(line))
        if not matches:
            continue

        refs = EVIDENCE_REF_RE.findall(line)
        has_rubric_ref = bool(RUBRIC_REF_RE.search(line)) or (rubric and rubric in line)

        for m in matches:
            out.checked_numbers += 1
            full = m.group("full").strip()
            num = normalize(m.group("num"))

            if not refs:
                if has_rubric_ref:
                    continue  # 口径类数字（权重、阈值、锚点）来自 rubric，不来自证据库
                out.fail(lineno, "MISSING_CITATION", full,
                         "数据型数字未携带 evidence_id 引用。正文中每个数字都必须可回源。")
                continue

            resolved = False
            problems: list[str] = []
            for ref in refs:
                rec = db.get(ref)
                if rec is None:
                    problems.append(f"{ref} 不在证据库中")
                    continue
                status = rec.get("verify_status")
                if status != "verified":
                    problems.append(f"{ref} 的 verify_status={status!r}，只有 verified 可用")
                    continue
                if num in {normalize(x) for x in numeric_forms(rec)}:
                    resolved = True
                    break
                problems.append(f"{ref} 记录的数值为 {sorted(numeric_forms(rec)) or '（无数值）'}")

            if not resolved:
                kind = "UNKNOWN_EVIDENCE" if any("不在证据库" in p for p in problems) else (
                    "UNVERIFIED_EVIDENCE" if any("verify_status" in p for p in problems) else "VALUE_MISMATCH")
                out.fail(lineno, kind, full, "；".join(problems))

    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="报告数字校验（防编造第三道闸）")
    ap.add_argument("report", type=Path)
    ap.add_argument("evidence", type=Path)
    ap.add_argument("--rubric", default="rubric-v1",
                    help="口径版本号；带该标记的行上的数字视为口径值，豁免证据引用")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    for p in (args.report, args.evidence):
        if not p.is_file():
            print(f"找不到文件: {p}", file=sys.stderr)
            return 2

    db = load_evidence(args.evidence)
    result = check(args.report, db, args.rubric)

    if args.as_json:
        print(json.dumps({
            "passed": not result.violations,
            "checked_numbers": result.checked_numbers,
            "evidence_loaded": result.evidence_loaded,
            "violations": [asdict(v) for v in result.violations],
            "warnings": [asdict(v) for v in result.warnings],
        }, ensure_ascii=False, indent=2))
        return 1 if result.violations else 0

    print(f"证据库条目: {result.evidence_loaded}    检查数字: {result.checked_numbers}")
    if result.warnings:
        print(f"\n警告 {len(result.warnings)} 处:")
        for w in result.warnings:
            print(w.render())
    if result.violations:
        print(f"\n✗ 校验未通过 —— {len(result.violations)} 处违规，报告不予发布:")
        for v in result.violations:
            print(v.render())
        print("\n修复方式：回上游补证，禁止修改报告措辞绕过校验。")
        return 1
    print("\n✓ 校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
