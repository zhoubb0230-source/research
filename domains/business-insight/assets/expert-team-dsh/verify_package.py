#!/usr/bin/env python3
"""交付件自检 —— 不安装任何东西，只检查这套文件本身是否自洽。

    python verify_package.py

检查：agent.json 合法性、persona 存在、skill 引用完整、frontmatter 合规、
      kebab-case、无孤儿 skill、SKILL.md 无 BOM。
退出码：0 全部通过 / 1 有问题
"""
import json, pathlib, re, sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

HERE = pathlib.Path(__file__).resolve().parent
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
problems, notes = [], []

skill_dirs = {p.name for p in (HERE / "skills").iterdir() if p.is_dir()}
for name in sorted(skill_dirs):
    f = HERE / "skills" / name / "SKILL.md"
    if not f.is_file():
        problems.append(f"skills/{name}: 缺 SKILL.md"); continue
    raw = f.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append(f"skills/{name}/SKILL.md: 带 BOM —— frontmatter 会解析失败且可能不报错")
    t = raw.decode("utf-8-sig")
    if not t.startswith("---\n"):
        problems.append(f"skills/{name}/SKILL.md: 无 frontmatter"); continue
    fm = t.split("---")[1]
    for k in ("name:", "description:", "user-invocable:", "disable-model-invocation:"):
        if k not in fm: problems.append(f"skills/{name}/SKILL.md: 缺 {k}")
    m = re.search(r"^name:\s*(\S+)", fm, re.M)
    if m and m.group(1) != name:
        problems.append(f"skills/{name}/SKILL.md: name={m.group(1)} 与目录名不符")
    if not KEBAB.match(name):
        problems.append(f"skills/{name}: 目录名非 kebab-case，dsh 不会发现它")

used = set()
agent_dirs = sorted(p for p in (HERE / "agents").iterdir() if p.is_dir())
for d in agent_dirs:
    aj = d / "agent.json"
    if not aj.is_file():
        problems.append(f"agents/{d.name}: 缺 agent.json"); continue
    try:
        cfg = json.loads(aj.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        problems.append(f"agents/{d.name}/agent.json: 非法 JSON — {e}"); continue
    if cfg.get("agentId") != d.name:
        problems.append(f"agents/{d.name}: agentId={cfg.get('agentId')} 与目录名不符")
    if not KEBAB.match(d.name):
        problems.append(f"agents/{d.name}: 目录名非 kebab-case")
    persona = d / cfg.get("persona", "persona.md")
    if not persona.is_file():
        problems.append(f"agents/{d.name}: 找不到 {persona.name}")
    else:
        body = persona.read_text(encoding="utf-8")
        if "我的认知姿态" not in body:
            problems.append(f"agents/{d.name}/persona.md: 缺「我的认知姿态」—— 这是 agent 核心差异所在")
        if "我绝不做的事" not in body:
            problems.append(f"agents/{d.name}/persona.md: 缺「我绝不做的事」—— 护栏必须常驻在 persona")
    for s in cfg.get("skills", []):
        used.add(s)
        if s not in skill_dirs:
            problems.append(f"agents/{d.name}: 引用了不存在的 skill `{s}`")
    for e in cfg.get("extraFiles", []):
        if not (d / e).is_file():
            problems.append(f"agents/{d.name}: 找不到 extraFile {e}")

orphans = skill_dirs - used
if orphans:
    notes.append(f"未被任何 agent 引用的 skill：{sorted(orphans)}（专属 skill 正常，但确认不是漏配）")

print(f"agent: {len(agent_dirs)} 个    skill: {len(skill_dirs)} 个（被引用 {len(used)} 个）\n")
for n in notes:  print(f"提示  {n}")
if problems:
    print(f"\n✗ 交付件自检未通过 —— {len(problems)} 处问题：")
    for p in problems: print(f"   {p}")
    sys.exit(1)
print("✓ 交付件自检通过")
