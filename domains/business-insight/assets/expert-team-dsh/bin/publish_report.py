#!/usr/bin/env python3
"""唯一的报告发布通道 —— 防编造第三道闸（跨平台）

    python publish_report.py <草稿.md> <批次证据库.jsonl> <发布目录>

闸门放进"发布"这个动作本身：校验不过就不落盘。
dsh 的 agent/pre-step 钩子也能拒绝（与 OpenClaw 不同），但闸门仍放在这里——
校验逻辑不该随平台重写，而且脚本不会被说服。

退出码：0 已发布 ｜ 1 校验未过（未发布）｜ 2 用法或读写错误
依赖：仅 Python 3.8+ 标准库。
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = pathlib.Path(__file__).resolve().parent
CHECKER = (HERE / ".." / ".." / "expert-team" / "checks" / "verify_report.py").resolve()

BLOCKED = """
════════════════════════════════════════════════════════
✗ 发布被阻断：报告中存在无法回源的数字。

正确处置（回边 R4）：退回 ③ 取证补证 → ④ 核证 → ⑤ 刻画 → ⑥ 聚合 → 重新成文。
禁止的处置：
  · 修改报告措辞绕过校验（把数字写成中文、删掉单位）
  · 用 verify:ignore 块包住真实数据段落
  · 手工把草稿复制进发布目录

本闸没有旁路。
════════════════════════════════════════════════════════
"""


def main() -> int:
    if len(sys.argv) != 4:
        print("用法: python publish_report.py <草稿.md> <批次证据库.jsonl> <发布目录>",
              file=sys.stderr)
        return 2

    draft = pathlib.Path(sys.argv[1]).expanduser()
    evidence = pathlib.Path(sys.argv[2]).expanduser()
    publish_dir = pathlib.Path(sys.argv[3]).expanduser()

    for f in (draft, evidence, CHECKER):
        if not f.is_file():
            print(f"✗ 找不到文件: {f}", file=sys.stderr)
            return 2

    print("── 发布前校验 ────────────────────────────────────")
    print(f"草稿   : {draft}")
    print(f"证据库 : {evidence}")
    print()

    # 用当前解释器跑校验，避开 Windows 上 python / python3 / py 的差异
    result = subprocess.run([sys.executable, str(CHECKER), str(draft), str(evidence)])
    if result.returncode != 0:
        print(BLOCKED, file=sys.stderr)
        return 1

    baseline = evidence.parent / "baseline.json"
    if not baseline.is_file():
        print(f"⚠ 警告：未找到 {baseline}")
        print("  没有基线快照，下一轮的 trend 算子与出局池复检都无从做起。")
        print("  确认报告生成专家是否产出了它（见 insight-service/spine.md §6）。")
        print()

    publish_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(draft, publish_dir / draft.name)
    print(f"✓ 校验通过，已发布 → {publish_dir / draft.name}")
    print("  下一步：更新两级索引（领域 INDEX.md + 全局 INDEX.md），否则本次归档视为未完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
