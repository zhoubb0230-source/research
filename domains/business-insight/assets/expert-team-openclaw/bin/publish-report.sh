#!/usr/bin/env bash
# ===========================================================================
# 唯一的报告发布通道 —— 防编造第三道闸在 OpenClaw 上的落点
#
#   publish-report.sh <草稿.md> <批次证据库.jsonl> <发布目录>
#
# 为什么闸门在这里而不在 hook：
#   OpenClaw 的 internal hooks 是副作用式的，官方文档明确「cannot block actions
#   —— 没有 deny/cancel 语义」。因此校验不能挂在 hook 上，否则它只会记录违规、
#   不会阻止发布。本脚本把校验放进「发布」这个动作本身：校验不过就不落盘。
#
#   配套的权限约束（见 openclaw.config.json5）：
#     · 报告生成专家 sandbox=all —— 写入被限制在自己的工作区，够不到发布目录
#     · 报告生成专家 tools.deny=[exec] —— 无法自行执行命令绕过本脚本
#     · 只有洞察总调度可以执行本脚本
# ===========================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECKER="$HERE/../../expert-team/checks/verify_report.py"

if [[ $# -ne 3 ]]; then
  echo "用法: $(basename "$0") <草稿.md> <批次证据库.jsonl> <发布目录>" >&2
  exit 2
fi

DRAFT="$1"; EVIDENCE="$2"; PUBLISH_DIR="$3"

for f in "$DRAFT" "$EVIDENCE" "$CHECKER"; do
  [[ -f "$f" ]] || { echo "✗ 找不到文件: $f" >&2; exit 2; }
done

echo "── 发布前校验 ────────────────────────────────────"
echo "草稿   : $DRAFT"
echo "证据库 : $EVIDENCE"
echo

if ! python3 "$CHECKER" "$DRAFT" "$EVIDENCE"; then
  cat >&2 <<'MSG'

════════════════════════════════════════════════════════
✗ 发布被阻断：报告中存在无法回源的数字。

正确处置：把违规项退回上游补证（数据采集专家 → 数据核证专家）。
禁止的处置：
  · 修改报告措辞绕过校验（例如把数字写成中文、删掉单位）
  · 用 verify:ignore 块包住真实数据段落
  · 手工把草稿复制进发布目录

本闸没有旁路。没有「人工确认后强推」这个选项。
════════════════════════════════════════════════════════
MSG
  exit 1
fi

mkdir -p "$PUBLISH_DIR"
BASENAME="$(basename "$DRAFT")"
cp "$DRAFT" "$PUBLISH_DIR/$BASENAME"

echo
echo "✓ 校验通过，已发布 → $PUBLISH_DIR/$BASENAME"
echo "  下一步：更新两级索引（领域 INDEX.md + 全局 INDEX.md），否则本次归档视为未完成。"
