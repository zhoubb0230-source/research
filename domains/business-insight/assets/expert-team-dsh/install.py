#!/usr/bin/env python3
"""业务洞察专家团 · DeepSeek Harness 装配（跨平台）

    python3 install.py <工作目录>                预演，不落盘
    python3 install.py <工作目录> --write        写入
    python3 install.py <工作目录> --write --preset <preset-root>
                                                 额外把 preset 目录装到指定 root

产出（在 <工作目录> 下）：

    AGENTS.md                        全队共用层：护栏 + 委托方模型 + 批次约定
                                     （dsh 按目录加载它，队友共享 cwd，所以这是全队一份）
    .dsh/PROMPTS/<name>.md           12 位专家的人格正文 —— spawnTeammate(prompt) 的实参
    .dsh/skills/<skill>/SKILL.md     全部技能（项目级 rank 100，优先级最高）
    .dsh/roster.json                 名册：name → 中文名/职责/provider 路由/人格文件/技能

为什么人格是 PROMPTS/*.md 而不是配置：
    AgentOptions 只有 { provider, model, maxTokens } —— 没有 prompt 字段。
    人格的唯一通道是 spawnTeammate(prompt)。见 DSH-NOTES.md §2。

为什么技能是共用目录而不是逐专家目录：
    dsh 的技能注册表是按 scope 分层的，但队友共用 Lead 的组合与 cwd，
    无法逐队友给不同的技能表。"谁该用哪个技能"只能写在人格里。见 DSH-NOTES.md §4。

依赖：仅 Python 3.8+ 标准库。Windows / macOS / Linux 通用。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = pathlib.Path(__file__).resolve().parent
NEUTRAL = (HERE / ".." / "expert-team" / "experts").resolve()
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def write(path: pathlib.Path, text: str) -> None:
    """统一 UTF-8 无 BOM、LF。

    BOM 会让 SKILL.md 的 frontmatter 解析失败，而且【不一定报错】——
    可能只是该技能被静默忽略。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def build_team_agents_md() -> str:
    g = (NEUTRAL / "_shared" / "GUARDRAILS.md").read_text(encoding="utf-8")
    u = (NEUTRAL / "_shared" / "USER.md").read_text(encoding="utf-8")
    b = (NEUTRAL / "_shared" / "BATCH-LAYOUT.md").read_text(encoding="utf-8")
    return f"""# 业务洞察专家团 · 全队共用层

<!-- 本文件由 expert-team-dsh/install.py 生成，不要手工编辑。
     正本：assets/expert-team/experts/_shared/

     dsh 的 AGENTS.md 是【按目录】加载的：从项目根走到会话 cwd。
     队友共享 Lead 的 cwd，所以这一份对全队 12 位都成立 ——
     它承载的只能是「对每一位专家都成立」的内容。
     逐专家的人格在 .dsh/PROMPTS/<name>.md，由 spawnTeammate(prompt) 绑定。 -->

{g}

---

{u}

---

{b}

---

## 三条不可违反的编排规则（全队都要知道，不只是 Lead）

1. **判据版本在一轮批次中途不得变更。** 变更必须递增版本号并整轮重跑。
2. **证伪最多 2 轮。** 第 2 轮只能针对第 1 轮应答中的新证据。
3. **发布闸没有旁路。** 校验脚本退出码非 0 就是没发布，
   正确处置是回边补证，不是改措辞绕过。

之所以把它们放在这一层而不是只放在 Lead 的人格里：
dsh 的人格只在会话开头出现一次，长会话经过压缩后可能淡出；
而这一层每轮都在。
"""


def build_prompt(agent_id: str, is_lead: bool) -> str:
    src = NEUTRAL / agent_id
    parts = [
        (src / "IDENTITY.md").read_text(encoding="utf-8"),
        (src / "SOUL.md").read_text(encoding="utf-8"),
        (src / "AGENTS.md").read_text(encoding="utf-8"),
        (HERE / "runtime" / ("lead.md" if is_lead else "teammate.md")).read_text(encoding="utf-8"),
    ]
    head = (
        f"<!-- 本文件由 expert-team-dsh/install.py 生成，不要手工编辑。\n"
        f"     正本：assets/expert-team/experts/{agent_id}/\n"
        f"     用法：spawnTeammate(prompt=<本文件正文>)；Lead 的这一份贴进它的首条消息。 -->\n"
    )
    return head + "\n" + "\n\n---\n\n".join(p.strip() for p in parts) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="装配业务洞察专家团到 dsh")
    ap.add_argument("target", type=pathlib.Path, help="工作目录（dsh 以最近的 .git 祖先为项目根）")
    ap.add_argument("--write", action="store_true", help="真正写入；默认只预演")
    ap.add_argument("--preset", type=pathlib.Path, default=None,
                    help="额外把 preset 目录装到这个 root（通常是 <dshHome>/.agent-presets）")
    args = ap.parse_args()

    target = args.target.expanduser()
    if not target.is_dir():
        print(f"✗ 找不到目录：{target}", file=sys.stderr)
        return 2
    target = target.resolve()

    ids = sorted(p.name for p in (HERE / "experts").iterdir() if (p / "spawn.json").is_file())
    if len(ids) != 12:
        print(f"⚠ experts/ 下有 {len(ids)} 位专家，预期 12", file=sys.stderr)

    roster, plan, skills_seen = {}, [], {}
    for aid in ids:
        if not KEBAB.match(aid):
            print(f"✗ `{aid}` 不是合法的 kebab-case 名字（dsh 要求 ^[a-z0-9]+(?:-[a-z0-9]+)*$）",
                  file=sys.stderr)
            return 2
        spawn = json.loads((HERE / "experts" / aid / "spawn.json").read_text(encoding="utf-8"))
        is_lead = spawn.get("role") == "lead"
        prompt = build_prompt(aid, is_lead)
        plan.append((target / ".dsh" / "PROMPTS" / f"{aid}.md", prompt))

        sk_dir = NEUTRAL / aid / "skills"
        my_skills = []
        if sk_dir.is_dir():
            for sk in sorted(sk_dir.iterdir()):
                f = sk / "SKILL.md"
                if not f.is_file():
                    continue
                body = f.read_text(encoding="utf-8")
                # frontmatter 自检：省略 disable-model-invocation 会默认为 true，模型就看不到它
                if "disable-model-invocation:" not in body:
                    print(f"✗ {f} 缺 `disable-model-invocation: false` —— "
                          f"省略时 dsh 默认为 true，模型将看不到这个技能", file=sys.stderr)
                    return 2
                if sk.name in skills_seen and skills_seen[sk.name] != aid:
                    print(f"✗ 技能名冲突：`{sk.name}` 同时属于 {skills_seen[sk.name]} 与 {aid}",
                          file=sys.stderr)
                    return 2
                skills_seen[sk.name] = aid
                my_skills.append(sk.name)
                plan.append((target / ".dsh" / "skills" / sk.name / "SKILL.md", body))

        node = {
            "nameCn": spawn.get("nameCn") or spawn["spawnTeammate"]["description"],
            "role": spawn.get("role", "teammate"),
            "prompt": f".dsh/PROMPTS/{aid}.md",
            "skills": my_skills,
            "optional": spawn.get("optional", False),
        }
        if is_lead:
            node["provider"] = spawn["provider"]
        else:
            node["spawnTeammate"] = {k: v for k, v in spawn["spawnTeammate"].items() if k != "prompt"}
        roster[aid] = node

        print(f"  {'★' if is_lead else '·'} {aid:22} {node.get('provider') or node['spawnTeammate']['provider']:15}"
              f" 技能 {len(my_skills)}  人格 {len(prompt)} 字符")

    plan.append((target / ".dsh" / "roster.json",
                 json.dumps({
                     "_note": "洞察总调度用本清单查 name → 人格文件 → provider 路由。"
                              "人格绑定发生在 spawnTeammate(prompt=<人格文件正文>)。",
                     "members": roster,
                 }, ensure_ascii=False, indent=2) + "\n"))
    plan.append((target / "AGENTS.md", build_team_agents_md()))

    print(f"\n共 {len(plan)} 个文件 → {target}")

    if args.preset:
        proot = args.preset.expanduser().resolve() / "business-insight-team"
        src = HERE / "orchestration" / "preset" / "business-insight-team"
        guard = (NEUTRAL / "_shared" / "GUARDRAILS.md").read_text(encoding="utf-8")
        comp = (src / "agent.cordis.yml").read_text(encoding="utf-8")
        MARK = "    text: __GUARDRAILS_TEXT__"
        if MARK not in comp:
            print(f"✗ preset 组合里找不到占位行：{MARK!r}", file=sys.stderr)
            return 2
        # 整行替换成 YAML 块标量。只换这一行 —— 注释里提到同名 token 时不会误伤。
        # `|` 后每行缩进 6 格（比 `text:` 的 4 格深一级），空行不留尾随空格。
        block = ("    text: |\n"
                 + "\n".join(("      " + l).rstrip() for l in guard.split("\n")))
        plan.append((proot / "agent.cordis.yml", comp.replace(MARK, block)))
        plan.append((proot / "preset.yml", (src / "preset.yml").read_text(encoding="utf-8")))
        for name, owner in sorted(skills_seen.items()):
            body = (NEUTRAL / owner / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            plan.append((proot / "skills" / name / "SKILL.md", body))
        print(f"preset → {proot}")

    if not args.write:
        print("\n预演完成，未落盘。加 --write 真正写入。")
        print("写入后请先跑 `dsh --profile web --dump-config`，")
        print("按 DSH-NOTES.md §8 核对 cordis.patch.yml 的形状，再开始跑批次。")
        return 0

    for path, body in plan:
        write(path, body)
    print(f"\n✓ 已写入 {len(plan)} 个文件")
    print("下一步：")
    print("  1. 复制 orchestration/cordis.patch.yml 到 profile 或 dshHome 目录")
    print("  2. dsh --profile web --dump-config   ← 核对形状，形状错了不报错只静默失效")
    print("  3. npx @deepseek-ai/dsh web")
    return 0


if __name__ == "__main__":
    sys.exit(main())
