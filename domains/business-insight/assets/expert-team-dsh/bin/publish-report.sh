#!/usr/bin/env bash
# ===========================================================================
# 唯一的报告发布通道 —— 防编造第三道闸在 DeepSeek Harness 上的落点
#
#   publish-report.sh <草稿.md> <批次证据库.jsonl> <发布目录>
#
# 与 OpenClaw 版同构：闸门放进「发布」这个动作本身，校验不过就不落盘。
#
# dsh 侧的额外加固（可选，见 DSH-NOTES.md §3）：
#   dsh 的 agent/pre-step 钩子决策是 authoritative 的，**可以拒绝**——
#   这一点与 OpenClaw 不同。可以再挂一道 pre-step 拦截，但本脚本不依赖它：
#   脚本内含校验，是平台无关的最后防线。
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

正确处置（回边 R4）：退回 ③ 取证补证 → ④ 核证 → ⑤ 刻画 → ⑥ 聚合 → 重新成文。
禁止的处置：
  · 修改报告措辞绕过校验（把数字写成中文、删掉单位）
  · 用 verify:ignore 块包住真实数据段落
  · 手工把草稿复制进发布目录

本闸没有旁路。
════════════════════════════════════════════════════════
MSG
  exit 1
fi

BASE="$(basename "$DRAFT")"
BATCH_DIR="$(dirname "$EVIDENCE")"
if [[ ! -f "$BATCH_DIR/baseline.json" ]]; then
  echo "⚠ 警告：未找到 $BATCH_DIR/baseline.json"
  echo "  没有基线快照，下一轮的 trend 算子与出局池复检都无从做起。"
  echo "  确认报告生成专家是否产出了它（见 spine.md §6）。"
  echo
fi

mkdir -p "$PUBLISH_DIR"
cp "$DRAFT" "$PUBLISH_DIR/$BASE"
echo "✓ 校验通过，已发布 → $PUBLISH_DIR/$BASE"
echo "  下一步：更新两级索引（领域 INDEX.md + 全局 INDEX.md），否则本次归档视为未完成。"
