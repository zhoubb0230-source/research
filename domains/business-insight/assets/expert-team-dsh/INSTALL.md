# 手工安装

**不需要跑任何脚本。** 全部是复制文件与改配置。

## 前置

- dsh 可运行，`DEEPSEEK_API_KEY` 已设
- Python 3.8+（**只有发布闸校验用**，安装过程不需要）

---

## 第 1 步：让 dsh 发现 13 个 skill

两种方式，**推荐方式一**。

### 方式一：指向本目录（不复制，随仓库同步）

在 `cordis.patch.yml` 里已经写好，只需把 `<REPO>` 替换为你的仓库绝对路径：

```yaml
skills:
  config:
    load:
      extraDirs:
        - 'D:/repo/research/domains/business-insight/assets/expert-team-dsh/skills'
```

优点：仓库更新后 skill 自动同步，不会出现正副本漂移。
skill 发现优先级为 300（custom 档）。

### 方式二：复制到项目级（优先级最高）

把整个 `skills/` 目录下的 13 个子目录复制到你的工作目录：

```
<工作目录>/.dsh/skills/
├── aggregation-operators/SKILL.md
├── arbitration-ruling/SKILL.md
├── catalog-enumeration/SKILL.md
├── challenge-typing/SKILL.md
├── dimension-scoring/SKILL.md
├── evidence-card-writing/SKILL.md
├── export-control-lookup/SKILL.md
├── falsification-memo/SKILL.md
├── implication-drafting/SKILL.md
├── insight-brief-authoring/SKILL.md
├── report-rendering/SKILL.md
├── rework-dispatch/SKILL.md
└── source-back-verification/SKILL.md
```

优先级 100（项目级最高）。代价是仓库更新后要手工同步。

> **Windows 复制注意**：`SKILL.md` 必须是 **UTF-8 无 BOM**。
> 用记事本另存为会加 BOM，**BOM 会让 frontmatter 解析失败，而且可能不报错、只是静默忽略这个 skill**。
> 用 VS Code / Notepad++ 并确认编码为「UTF-8」而非「UTF-8 with BOM」。
> 直接用资源管理器复制文件不会改变编码，是安全的。

---

## 第 2 步：合并配置

把 `cordis.patch.yml` 的内容并进你的 `cordis.patch.yml`（profile 级或 home 级），
替换 `<REPO>` 占位符。

然后**务必核对形状**（见 `DSH-NOTES.md` §5 的四项待校验）：

```
dsh --profile web --dump-config
```

配置写错**不报错，只是静默失效**——所以这一步不能跳。

---

## 第 3 步：启动

```
npx @deepseek-ai/dsh web
```

默认 `http://127.0.0.1:3080`。

---

## 第 4 步：建队友时绑定 persona（**最容易漏的一步**）

skill 已经被 dsh 发现了，但**队友还不是专家**。

skill 是「可被调用的资源」，persona 才是「我是谁」。绑定发生在建队友的那一刻：

```
spawnTeammate(
  name        = "red-team-challenger",
  description = "🥊 质疑审查专家 · 负责 ⑦ 证伪",
  prompt      = <agents/red-team-challenger/persona.md 的全文>,   ← 关键
  contextMode = "isolated",
  provider    = <你的 provider>
)
```

`SpawnTeammateRequest` 带 `prompt` 字段，这是文档明确的。

**12 个专家逐一建好，每个都传自己的 `persona.md` 全文。**
不传，队友就是个通用助手——那 12 个专家等于没装，多智能体只剩成本没有收益。

洞察总调度还要额外带上 `agents/chief-coordinator/playbook.md`（十动作 + 五回边运行手册）。

---

## 第 5 步：发起第一轮

建议首轮用现成预设：

```
../insight-service/presets/landscape-survey.brief.json
```

在 dsh UI 里调用 `insight-planner`（它是 `user-invocable`），把需求给它，
它会先分诊，通过后产出 `brief.json`。

发布时由洞察总调度执行：

```
python bin/publish_report.py <草稿.md> <批次根>/evidence.jsonl <发布目录>
```

退出码非 0 = 没发布，没有旁路。

---

## 装完自检

| 检查 | 怎么看 |
|---|---|
| 13 个 skill 被发现了吗 | dsh 的 skill 列表里能看到这 13 个名字 |
| SKILL.md 有没有 BOM | 用 VS Code 打开，右下角编码应显示 `UTF-8`，不是 `UTF-8 with BOM` |
| 配置生效了吗 | `dsh --profile web --dump-config` 里能看到 12 个 agent id |
| persona 绑上了吗 | 问质疑审查专家"你的目标是什么"，它应该说"推翻结论"而不是"帮助用户" |

**最后一条是最关键的自检。** 如果它回答得像个通用助手，说明 `prompt` 没传进去。
