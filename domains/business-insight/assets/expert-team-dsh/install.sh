#!/usr/bin/env bash
# 薄封装：找 Python 然后转调 install.py。业务逻辑只有一份，在 .py 里。
set -euo pipefail
cd "$(dirname "$0")"
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1; then exec "$py" install.py "$@"; fi
done
echo "✗ 找不到 python3。装一个 Python 3.8+ 后重试。" >&2
exit 1
