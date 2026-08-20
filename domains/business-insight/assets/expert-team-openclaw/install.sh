#!/usr/bin/env bash
# ===========================================================================
# 业务洞察专家团 · OpenClaw 安装脚本
#
#   ./install.sh                 预演：生成 workspaces 与配置，不改 ~/.openclaw
#   ./install.sh --merge         预演 + 合并配置到 ~/.openclaw/openclaw.json（自动备份）
#
# 依赖：bash、python3（仅标准库）。openclaw CLI 可选，用于 schema 校验。
# ===========================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
MERGE=0
[[ "${1:-}" == "--merge" ]] && MERGE=1

OC_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
OC_CONFIG="$OC_HOME/openclaw.json"
GENERATED="$HERE/openclaw.config.generated.json"

echo "仓库根目录 : $REPO"
echo "OpenClaw 家 : $OC_HOME"
echo "模式        : $([[ $MERGE == 1 ]] && echo '生成 + 合并' || echo '仅生成（预演）')"
echo

# --- 1. 生成 12 个 agent 的 workspace -------------------------------------
python3 - "$HERE" "$REPO" <<'PY'
import json, pathlib, sys

here = pathlib.Path(sys.argv[1])
repo = pathlib.Path(sys.argv[2])

cfg          = json.loads((here / "roles.json").read_text(encoding="utf-8"))
prompt_dir   = (here / cfg["_promptDir"]).resolve()
guardrails   = (prompt_dir / cfg["_sharedGuardrails"]).read_text(encoding="utf-8")
soul_tmpl    = (here / "templates/SOUL.md.tmpl").read_text(encoding="utf-8")
agents_tmpl  = (here / "templates/AGENTS.md.tmpl").read_text(encoding="utf-8")

def bullets(items):
    return "\n".join(f"- {x}" for x in items) if items else "- （无特殊限制，遵循共用护栏）"

made = 0
for r in cfg["roles"]:
    ws = here / "workspaces" / r["agentId"]
    ws.mkdir(parents=True, exist_ok=True)

    role_prompt = (prompt_dir / r["promptFile"]).read_text(encoding="utf-8")

    # 总调度额外挂载阶段运行手册
    if r.get("playbook"):
        role_prompt += "\n\n---\n\n" + (here / r["playbook"]).read_text(encoding="utf-8")

    if r.get("canSpawn"):
        allow = "、".join(r.get("allowAgents", []))
        spawn = (
            "**我可以派发子 Agent。** 用 `sessions_spawn` 时必须显式给 `agentId`"
            "（配置里 `requireAgentId: true`，不给会被拒绝），允许派发的对象："
            f"{allow}。\n\n"
            "派发后**必须调用 `sessions_yield` 等待结果**，把子 Agent 的完成事件作为下一条消息接收。\n"
            "**禁止用轮询循环代替 `sessions_yield`** —— 官方文档明确要求，轮询会烧掉并发额度。\n\n"
        )
    else:
        spawn = (
            "**我不派发子 Agent。** 我是叶子节点，`sessions_spawn` 对我不可用。\n"
            "需要别人做的事，写进我的产出交给洞察总调度，不要自己代劳。\n\n"
        )

    excluded = ""
    if r.get("inputsExcluded"):
        excluded = f"| **不给我看** | {'、'.join(r['inputsExcluded'])} |\n"

    subs = {
        "{{EMOJI}}":      r["emoji"],
        "{{NAME_CN}}":    r["nameCn"],
        "{{AGENT_ID}}":   r["agentId"],
        "{{LEGACY_ID}}":  r["legacyId"],
        "{{PROMPT_FILE}}": r["promptFile"],
        "{{STAGES}}":     " / ".join(r["stages"]),
        "{{MODEL}}":      r["model"],
        "{{THINKING}}":   r["thinking"],
        "{{NOTE}}":       r.get("note", ""),
        "{{INPUTS}}":     "、".join(r.get("inputs", [])),
        "{{OUTPUTS}}":    "、".join(r.get("outputs", [])),
        "{{FORBIDDEN}}":  bullets(r.get("forbidden", [])),
        "{{GUARDRAILS}}": guardrails,
        "{{ROLE_PROMPT}}": role_prompt,
        "{{SPAWN_SECTION}}": spawn,
        "{{INPUTS_EXCLUDED_ROW}}": excluded,
    }

    for tmpl, name in ((soul_tmpl, "SOUL.md"), (agents_tmpl, "AGENTS.md")):
        out = tmpl
        for k, v in subs.items():
            out = out.replace(k, v)
        (ws / name).write_text(out, encoding="utf-8")
    made += 1

print(f"✓ 已生成 {made} 个 agent workspace（每个含 SOUL.md + AGENTS.md）")
PY

# --- 2. json5 → 严格 JSON，并替换 <REPO> ----------------------------------
python3 - "$HERE" "$REPO" "$GENERATED" <<'PY'
import json, pathlib, re, sys

here, repo, out_path = pathlib.Path(sys.argv[1]), sys.argv[2], pathlib.Path(sys.argv[3])
raw = (here / "openclaw.config.json5").read_text(encoding="utf-8")

# 本文件刻意只使用「整行 // 注释」且不含尾逗号，因此剥离是安全且可验证的
stripped = "\n".join(l for l in raw.splitlines() if not l.lstrip().startswith("//"))
stripped = stripped.replace("<REPO>", repo)

try:
    cfg = json.loads(stripped)
except json.JSONDecodeError as e:
    sys.exit(f"✗ 剥离注释后不是合法 JSON：{e}\n  请检查 openclaw.config.json5 是否引入了行尾注释或尾逗号")

leftover = sorted(set(re.findall(r"<[A-Z_]+>", json.dumps(cfg, ensure_ascii=False))))
if leftover:
    sys.exit(
        "✗ 配置中仍有未替换的占位符：" + "、".join(leftover) +
        "\n  请先在 openclaw.config.json5 中替换它们（通道与账号必须填实），再重跑。"
    )

out_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"✓ 已生成严格 JSON：{out_path.name}（{len(cfg['agents']['entries'])} 个 agent 条目）")
PY

# --- 3. schema 校验（有 openclaw CLI 才做） --------------------------------
if command -v openclaw >/dev/null 2>&1; then
  if openclaw config schema >/dev/null 2>&1; then
    echo "✓ openclaw CLI 可用，已取到 live schema（请人工比对本配置的字段形态，见 OPENCLAW-NOTES.md §5 待校验项）"
  fi
else
  echo "· 未检测到 openclaw CLI，跳过 schema 校验。上线前请务必执行：openclaw config schema"
fi

# --- 4. 合并 --------------------------------------------------------------
if [[ $MERGE == 1 ]]; then
  mkdir -p "$OC_HOME"
  if [[ -f "$OC_CONFIG" ]]; then
    BACKUP="$OC_CONFIG.bak.$(date +%Y%m%d%H%M%S)"
    cp "$OC_CONFIG" "$BACKUP"
    echo "✓ 已备份原配置 → $BACKUP"
  fi
  python3 - "$OC_CONFIG" "$GENERATED" <<'PY'
import json, pathlib, sys
target, src = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
base = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
add  = json.loads(src.read_text(encoding="utf-8"))

def deep_merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            deep_merge(a[k], v)
        else:
            a[k] = v
    return a

target.write_text(json.dumps(deep_merge(base, add), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"✓ 已合并到 {target}")
PY
  echo
  echo "下一步：重启 gateway 使 hooks 生效，然后在通道里对「洞察总调度」发起 P0。"
else
  echo
  echo "预演完成，未改动 $OC_CONFIG。"
  echo "确认无误后执行：./install.sh --merge"
fi
