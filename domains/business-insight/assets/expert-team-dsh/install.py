#!/usr/bin/env python3
"""业务洞察专家团 · DeepSeek Harness 安装（跨平台）

    python install.py <项目目录>            预演，不落盘
    python install.py <项目目录> --write    写入

产出（在 <项目目录> 下）：
    .dsh/skills/<agentId>/SKILL.md   12 个角色定义
    .dsh/roster.json                 角色清单，洞察总调度用它查 agentId → skill 路径

为什么生成到 .dsh/skills：dsh 的 skill 发现规则是文档明确的——
.dsh/skills 排名 100（项目级最高优先），格式 <name>/SKILL.md，名字 kebab-case。

⚠️ skill 只是"可被调用的指令"，不等于"这个 agent 就是这个角色"。
   人格绑定发生在 spawnTeammate(prompt=<SKILL.md 正文>)，见 playbook.md。

依赖：仅 Python 3.8+ 标准库。Windows / macOS / Linux 通用。
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

# Windows 控制台默认可能是 GBK，制表符与 ✓ 之类会炸；统一转 UTF-8
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = pathlib.Path(__file__).resolve().parent
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def build_skill(role: dict, here: pathlib.Path, prompt_dir: pathlib.Path, guardrails: str) -> str:
    body = (prompt_dir / role["promptFile"]).read_text(encoding="utf-8")
    if role.get("playbook"):
        body += "\n\n---\n\n" + (here / role["playbook"]).read_text(encoding="utf-8")

    extra = role.get("extraContract") or []
    extra_md = "\n".join(f"- {x}" for x in extra) if extra else "- （无）"

    effort_note = (
        "（dsh 无 medium 档，原设计的 medium 已落到 low）"
        if role["reasoningEffort"] == "low" else ""
    )
    delegate = (
        "- 我可以用 `spawnTeammate()` / `sendMessage()` 派发队友，"
        "用 `waitForChange()` 等结果（有界等待，十秒到一小时），**不要写忙轮询**。"
        if role.get("canDelegate")
        else "- 我不派发队友。我是叶子节点。"
    )

    frontmatter = "\n".join([
        "---",
        f"name: {role['agentId']}",
        f'description: "{role["emoji"]} {role["nameCn"]} —— 负责骨架的 {"、".join(role["actions"])}"',
        f"user-invocable: {'true' if role.get('userInvocable') else 'false'}",
        "disable-model-invocation: false",
        "---",
    ])

    return f"""{frontmatter}

# {role['emoji']} {role['nameCn']}

> **本文件由 install.py 生成，不要手工编辑。**
> 正本：`assets/expert-team/prompts/{role['promptFile']}` 与 `assets/expert-team-dsh/roles.json`
> 骨架：`assets/insight-service/spine.md`

## 我在骨架里的位置

我负责 **{'、'.join(role['actions'])}**。{role.get('note', '')}

建议 `reasoningEffort`：`{role['reasoningEffort']}` {effort_note}

## 本骨架下我的附加契约

{extra_md}

## 运行约定

- 任务包 `brief.json` 是本次洞察的全部参数来源。**判据、证据等级、时效要求每次都不同**，
  不要沿用上一次的口径。
- 我的结构化产出必须符合 `assets/expert-team/schemas/` 下的 JSON Schema。
- 需要别人做的事，写进产出交给洞察总调度，**不要自己代劳**——跨角色代劳会让责任链断裂。
{delegate}

---

{guardrails}

---

{body}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 dsh 专家团 skills")
    ap.add_argument("target", type=pathlib.Path, help="项目目录（dsh 以最近的 .git 祖先为项目根）")
    ap.add_argument("--write", action="store_true", help="真正写入；默认只预演")
    args = ap.parse_args()

    target = args.target.expanduser()
    if not target.is_dir():
        print(f"✗ 找不到目录：{target}", file=sys.stderr)
        return 2
    target = target.resolve()

    cfg = json.loads((HERE / "roles.json").read_text(encoding="utf-8"))
    prompt_dir = (HERE / cfg["_promptDir"]).resolve()
    if not prompt_dir.is_dir():
        print(f"✗ 找不到角色提示词目录：{prompt_dir}", file=sys.stderr)
        return 2
    guardrails = (prompt_dir / cfg["_sharedGuardrails"]).read_text(encoding="utf-8")

    skill_root = target / ".dsh" / "skills"
    roster_path = target / ".dsh" / "roster.json"

    print(f"资产目录 : {HERE}")
    print(f"项目目录 : {target}")
    print(f"技能目录 : {skill_root}")
    print(f"模式     : {'写入' if args.write else '预演（不落盘）'}")
    print()

    roster, rows, bad = [], [], []
    for role in cfg["roles"]:
        aid = role["agentId"]
        if not KEBAB.match(aid):
            bad.append(aid)
        text = build_skill(role, HERE, prompt_dir, guardrails)
        rows.append((aid, len(text)))
        roster.append({
            "agentId": aid,
            "nameCn": role["nameCn"],
            "emoji": role["emoji"],
            "actions": role["actions"],
            "reasoningEffort": role["reasoningEffort"],
            "canDelegate": bool(role.get("canDelegate")),
            "optional": bool(role.get("optional")),
            "userInvocable": bool(role.get("userInvocable")),
            # 洞察总调度用它取正文作为 spawnTeammate 的 prompt
            "skillPath": f".dsh/skills/{aid}/SKILL.md",
            "note": role.get("note", ""),
        })
        if args.write:
            d = skill_root / aid
            d.mkdir(parents=True, exist_ok=True)
            # 显式 utf-8 无 BOM + LF：BOM 会破坏 frontmatter 解析
            (d / "SKILL.md").write_text(text, encoding="utf-8", newline="\n")

    if bad:
        print(f"✗ 以下 agentId 不符合 dsh 的 kebab-case 要求：{', '.join(bad)}", file=sys.stderr)
        return 1

    if args.write:
        roster_path.parent.mkdir(parents=True, exist_ok=True)
        roster_path.write_text(
            json.dumps({
                "_comment": "洞察总调度用本清单查 agentId → SKILL.md 路径，"
                            "建队友时把 SKILL.md 正文作为 spawnTeammate 的 prompt 传入。",
                "spine": "十动作，五条回边。见 assets/insight-service/spine.md",
                "roles": roster,
            }, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")

    print(f"{'已写入' if args.write else '将生成'} {len(rows)} 个 skill：")
    for aid, n in rows:
        flag = "  ⚠ 偏大" if n > 40000 else ""
        print(f"  .dsh/skills/{aid}/SKILL.md  ({n:,} 字符){flag}")
    print(f"  .dsh/roster.json  ({len(roster)} 条)")
    print(f"合计 {sum(n for _, n in rows):,} 字符")

    print()
    if not args.write:
        print("预演完成，未写入。确认无误后加 --write。")
    else:
        print("下一步：")
        print("  1. 复制 cordis.patch.yml 到项目目录，并按 DSH-NOTES.md §5 校验形状：")
        print("       dsh --profile web --dump-config")
        print("  2. 启动：npx @deepseek-ai/dsh web    （默认 http://127.0.0.1:3080）")
        print("  3. 在 UI 里调用 insight-planner 发起 ① 界定")
        print("  4. 注意：建队友时必须把 SKILL.md 正文作为 spawnTeammate 的 prompt 传入，")
        print("     否则队友不会变成对应的专家。见 playbook.md「角色人格怎么绑上去」。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
