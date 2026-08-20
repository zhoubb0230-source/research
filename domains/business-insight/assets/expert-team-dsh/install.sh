#!/usr/bin/env bash
# 薄封装：逻辑在 install.py（跨平台）。三端跑同一份代码。
#   ./install.sh <项目目录> [--write]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$HERE/install.py" "$@"
