#!/usr/bin/env python3
"""业务洞察专家团 · OpenClaw 装配（跨平台）

    python3 install.py                  预演：生成工作区与严格 JSON 配置，不碰 ~/.openclaw
    python3 install.py --merge          键级合并进 ~/.openclaw/openclaw.json（先备份）
    python3 install.py --workspace-root <目录>   指定工作区根（默认 ./workspaces）

装配来源（全部是仓库里的正本，本脚本不含任何专家内容）：

    ../expert-team/experts/<id>/IDENTITY.md   ─┐
    ../expert-team/experts/<id>/SOUL.md        ├→ <工作区>/<id>/ 同名文件
    ../expert-team/experts/<id>/AGENTS.md     ─┘   （AGENTS.md 末尾追加 runtime 片段）
    ../expert-team/experts/_shared/GUARDRAILS.md → 内联进 SOUL.md 最前面
    ../expert-team/experts/_shared/USER.md       → <工作区>/<id>/USER.md
    ../expert-team/experts/<id>/skills/         → <工作区>/<id>/skills/
    ./experts/<id>/entry.json5                  → 生成配置的 agents.entries.<id>
    ./openclaw.config.json5                     → 生成配置的其余部分

生成产物（<工作区>/ 与 openclaw.config.generated.json）不入库。
依赖：仅 Python 3.8+ 标准库。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = pathlib.Path(__file__).resolve().parent
NEUTRAL = (HERE / ".." / "expert-team" / "experts").resolve()
PLACEHOLDER = re.compile(r"<(CHANNEL|ACCOUNT_ID|REPO)>")


def strip_json5(text: str) -> str:
    """剥掉整行 // 注释。主本刻意不使用行尾注释，所以这样足够且不会误伤字符串里的 //。"""
    return "\n".join(l for l in text.split("\n") if not l.strip().startswith("//"))


def load_json5(path: pathlib.Path) -> dict:
    try:
        return json.loads(strip_json5(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as e:
        sys.exit(f"✗ {path} 剥注释后不是合法 JSON：{e}")


def deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def write(path: pathlib.Path, text: str) -> None:
    """统一 UTF-8 无 BOM、LF。BOM 会破坏 frontmatter 解析，而且不一定报错。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def build_workspace(agent_id: str, root: pathlib.Path, is_coordinator: bool) -> int:
    src = NEUTRAL / agent_id
    if not src.is_dir():
        sys.exit(f"✗ 找不到专家正本目录：{src}")
    ws = root / agent_id
    guard = (NEUTRAL / "_shared" / "GUARDRAILS.md").read_text(encoding="utf-8")
    runtime = (HERE / "runtime" / ("coordinator.md" if is_coordinator else "leaf.md")).read_text(encoding="utf-8")

    write(ws / "IDENTITY.md", (src / "IDENTITY.md").read_text(encoding="utf-8"))

    # 护栏内联到 SOUL.md 最前面：内容稳定，落在提示词缓存断点之前。
    write(ws / "SOUL.md", guard + "\n\n---\n\n" + (src / "SOUL.md").read_text(encoding="utf-8"))

    # runtime 片段追加到 AGENTS.md 末尾：它是平台约定，不是角色立场。
    write(ws / "AGENTS.md", (src / "AGENTS.md").read_text(encoding="utf-8") + "\n\n---\n\n" + runtime)

    write(ws / "USER.md", (NEUTRAL / "_shared" / "USER.md").read_text(encoding="utf-8"))
    write(ws / "BATCH-LAYOUT.md", (NEUTRAL / "_shared" / "BATCH-LAYOUT.md").read_text(encoding="utf-8"))

    n_skills = 0
    skills_src = src / "skills"
    if skills_src.is_dir():
        for sk in sorted(skills_src.iterdir()):
            if (sk / "SKILL.md").is_file():
                write(ws / "skills" / sk.name / "SKILL.md", (sk / "SKILL.md").read_text(encoding="utf-8"))
                n_skills += 1

    # 引导文件字符预算自检（OpenClaw 数的是字符，不是字节）
    for name, cap in (("IDENTITY.md", 20000), ("SOUL.md", 20000), ("AGENTS.md", 20000)):
        n = len((ws / name).read_text(encoding="utf-8"))
        if n > cap:
            sys.exit(f"✗ {agent_id}/{name} 有 {n} 字符，超过 bootstrapMaxChars={cap}，会被静默截断")
    total = sum(len((ws / f).read_text(encoding="utf-8"))
                for f in ("IDENTITY.md", "SOUL.md", "AGENTS.md", "USER.md"))
    if total > 60000:
        sys.exit(f"✗ {agent_id} 引导文件合计 {total} 字符，超过 bootstrapTotalMaxChars=60000")
    return n_skills, total


def main() -> int:
    ap = argparse.ArgumentParser(description="装配业务洞察专家团到 OpenClaw")
    ap.add_argument("--merge", action="store_true", help="合并进 ~/.openclaw/openclaw.json（默认只预演）")
    ap.add_argument("--workspace-root", type=pathlib.Path, default=HERE / "workspaces")
    ap.add_argument("--config", type=pathlib.Path, default=pathlib.Path("~/.openclaw/openclaw.json").expanduser())
    args = ap.parse_args()

    root = args.workspace_root.expanduser().resolve()
    frame = load_json5(HERE / "openclaw.config.json5")

    entries = {}
    ids = sorted(p.name for p in (HERE / "experts").iterdir() if (p / "entry.json5").is_file())
    if len(ids) != 12:
        print(f"⚠ experts/ 下有 {len(ids)} 位专家，预期 12", file=sys.stderr)

    print(f"工作区根：{root}\n")
    for aid in ids:
        entry = load_json5(HERE / "experts" / aid / "entry.json5")
        entry["workspace"] = str(root / aid)
        entries[aid] = entry
        n_sk, total = build_workspace(aid, root, aid == "chief-coordinator")
        print(f"  ✓ {aid:22} 技能 {n_sk}  引导文件 {total} 字符  "
              f"模型 {entry.get('model')}  thinking {entry.get('thinkingDefault')}")

    frame["agents"]["entries"] = entries
    out = json.dumps(frame, ensure_ascii=False, indent=2)

    left = sorted(set(PLACEHOLDER.findall(out)))
    gen = HERE / "openclaw.config.generated.json"
    write(gen, out + "\n")
    print(f"\n生成配置：{gen}")

    if left:
        print(f"\n✗ 仍有未替换的占位符：{', '.join('<'+x+'>' for x in left)}")
        print("  编辑 openclaw.config.json5 填上你实际的通道与账号后重跑。")
        return 1

    if not args.merge:
        print("\n预演完成，未改动你的配置。")
        print("下一步：按 OPENCLAW-NOTES.md §「上线前必须校验」逐项比对 `openclaw config schema`，")
        print("        确认无误后跑 `python3 install.py --merge`。")
        return 0

    cfg = args.config
    if cfg.is_file():
        bak = cfg.with_suffix(cfg.suffix + ".bak")
        shutil.copy2(cfg, bak)
        print(f"\n已备份原配置 → {bak}")
        merged = deep_merge(json.loads(cfg.read_text(encoding="utf-8")), frame)
    else:
        merged = frame
    write(cfg, json.dumps(merged, ensure_ascii=False, indent=2) + "\n")
    print(f"已合并 → {cfg}")
    print("重启 gateway 使 hooks 生效。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
