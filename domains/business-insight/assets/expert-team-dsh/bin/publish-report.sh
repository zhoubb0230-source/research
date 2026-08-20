#!/usr/bin/env bash
# 薄封装：逻辑在 publish_report.py（跨平台）。
#   ./publish-report.sh <草稿.md> <证据库.jsonl> <发布目录>
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$HERE/publish_report.py" "$@"
