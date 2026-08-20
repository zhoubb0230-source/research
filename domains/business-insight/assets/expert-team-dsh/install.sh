#!/usr/bin/env bash
# ===========================================================================
# 业务洞察专家团 · DeepSeek Harness 安装
#
#   ./install.sh <项目目录>            预演：把 12 个角色生成到 <项目目录>/.dsh/skills/
#   ./install.sh <项目目录> --write    真正写入
#
# 为什么装成 skills：dsh 的 skill 发现规则是文档明确的——
#   .dsh/skills 排名 100（项目级最高优先），格式 <name>/SKILL.md，名字 kebab-case。
# 这比 cordis.patch.yml 的形状确定得多，所以角色定义全部走 skills。
#
# 依赖：bash、python3（仅标准库）。
# ===========================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-}"
WRITE=0
[[ "${2:-}" == "--write" ]] && WRITE=1

if [[ -z "$TARGET" ]]; then
  echo "用法: $(basename "$0") <项目目录> [--write]" >&2
  echo "  项目目录 = 你打算跑洞察的工作目录（dsh 以最近的 .git 祖先为项目根）" >&2
  exit 2
fi
TARGET="$(cd "$TARGET" 2>/dev/null && pwd)" || { echo "找不到目录: ${1}" >&2; exit 2; }

SKILL_DIR="$TARGET/.dsh/skills"
echo "资产目录 : $HERE"
echo "项目目录 : $TARGET"
echo "技能目录 : $SKILL_DIR"
echo "模式     : $([[ $WRITE == 1 ]] && echo '写入' || echo '预演（不落盘）')"
echo

python3 - "$HERE" "$SKILL_DIR" "$WRITE" <<'PY'
import json, pathlib, sys

here    = pathlib.Path(sys.argv[1])
out_dir = pathlib.Path(sys.argv[2])
write   = sys.argv[3] == "1"

cfg        = json.loads((here / "roles.json").read_text(encoding="utf-8"))
prompt_dir = (here / cfg["_promptDir"]).resolve()
guardrails = (prompt_dir / cfg["_sharedGuardrails"]).read_text(encoding="utf-8")

def build(role: dict) -> str:
    body = (prompt_dir / role["promptFile"]).read_text(encoding="utf-8")
    if role.get("playbook"):
        body += "\n\n---\n\n" + (here / role["playbook"]).read_text(encoding="utf-8")

    extra = role.get("extraContract") or []
    extra_md = "\n".join(f"- {x}" for x in extra) if extra else "- （无）"

    # dsh skill frontmatter：只用文档中明确记载的两个字段
    fm = [
        "---",
        f"name: {role['agentId']}",
        f"description: \"{role['emoji']} {role['nameCn']} —— 负责骨架的 {'、'.join(role['actions'])}\"",
        f"user-invocable: {'true' if role.get('userInvocable') else 'false'}",
        "disable-model-invocation: false",
        "---",
    ]

    return "\n".join(fm) + f"""

# {role['emoji']} {role['nameCn']}

> **本文件由 install.sh 生成，不要手工编辑。**
> 正本：`assets/expert-team/prompts/{role['promptFile']}` 与 `assets/expert-team-dsh/roles.json`
> 骨架：`assets/insight-service/spine.md`

## 我在骨架里的位置

我负责 **{'、'.join(role['actions'])}**。{role.get('note','')}

建议 `reasoningEffort`：`{role['reasoningEffort']}`
{'（dsh 无 medium 档，原设计的 medium 已落到 low）' if role['reasoningEffort'] == 'low' else ''}

## 本骨架下我的附加契约

{extra_md}

## 运行约定

- 任务包 `brief.json` 是本次洞察的全部参数来源。**判据、证据等级、时效要求每次都不同**，
  不要沿用上一次的口径。
- 我的结构化产出必须符合 `assets/expert-team/schemas/` 下的 JSON Schema。
- 需要别人做的事，写进产出交给洞察总调度，**不要自己代劳**——跨角色代劳会让责任链断裂。
{'- 我可以用 `spawnTeammate()` / `sendMessage()` 派发队友，用 `waitForChange()` 等结果（有界等待，十秒到一小时），**不要写忙轮询**。' if role.get('canDelegate') else '- 我不派发队友。我是叶子节点。'}

---

{guardrails}

---

{body}
"""

made = []
for r in cfg["roles"]:
    d = out_dir / r["agentId"]
    text = build(r)
    made.append((r["agentId"], len(text)))
    if write:
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(text, encoding="utf-8")

total = sum(n for _, n in made)
print(f"{'已写入' if write else '将生成'} {len(made)} 个 skill：")
for name, n in made:
    flag = "  ⚠ 偏大" if n > 40000 else ""
    print(f"  .dsh/skills/{name}/SKILL.md  ({n:,} 字符){flag}")
print(f"合计 {total:,} 字符")
PY

if [[ $WRITE == 0 ]]; then
  echo
  echo "预演完成，未写入。确认无误后："
  echo "  ./install.sh \"$TARGET\" --write"
else
  echo
  echo "下一步："
  echo "  1. 按 DSH-NOTES.md §5 校验 cordis.patch.yml 的字段形态："
  echo "       dsh --profile web --dump-config"
  echo "  2. 启动：npx @deepseek-ai/dsh web    （默认 http://127.0.0.1:3080）"
  echo "  3. 在 UI 里调用 insight-planner 发起 ① 界定"
fi
