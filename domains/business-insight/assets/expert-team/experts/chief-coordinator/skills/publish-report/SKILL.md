---
name: publish-report
description: 报告发布闸：唯一通往发布目录的路径，内含确定性数字校验。校验不过时的正确处置在这里。
user-invocable: true
disable-model-invocation: false
---

# 发布闸

## 为什么发布是一个脚本而不是一个动作

报告落盘这一步是整条流水线上**唯一不可被模型说服的防线**。
把它做成"渲染后请检查一下"，等于把最后一道闸交给自觉。

所以设计是：**报告生成专家写不到发布目录**（沙箱 + 工具权限），
**唯一通往发布目录的路径是这个脚本**，脚本内部先跑确定性校验，退出码非 0 就不落盘。

这比"钩子拦截"更强——不是"有人会拦住"，而是**根本没有第二条路**。

## 怎么跑

```
<harness 包>/bin/publish-report.sh  <草稿.md>  <批次根>/evidence.jsonl  <发布目录>
```

Windows 上等价地跑 `bin\publish-report.ps1`，或直接 `python bin/publish_report.py <三个参数>`——
逻辑只有一份，在 `.py` 里，三端行为一致。

脚本内部执行 `assets/expert-team/checks/verify_report.py`，检查四类违规：

| 违规 | 含义 |
|---|---|
| 无出处数字 | 正文出现的数字在 `evidence.jsonl` 里找不到对应 `evidence_id` |
| 悬空引用 | 引用了不存在的 `evidence_id` |
| 不确定性标注被删 | `NA` / `undetermined` / 【判断】/【假设】/ 置信度标记在结构化输入里有、报告里没了 |
| 区间被写成点值 | 输入是区间，报告写成了单值 |

## 退出码非 0 时怎么办

**唯一正确的处置是回边 R4：退回 ③ 取证补证。**

以下都是错的，一条都不许做：

- ❌ 改报告措辞让校验通过（比如把数字改写成文字描述）
- ❌ 手工把草稿复制进发布目录
- ❌ 加一条"人工已确认"的旁路
- ❌ 放宽校验器的判据

校验器是代码不是模型。**它不会被说服，也不该被说服。**

## 自测

上线前先用夹具确认闸门是活的：

```
python3 assets/expert-team/checks/verify_report.py \
        assets/expert-team/checks/fixtures/report.pass.sample.md \
        assets/expert-team/checks/fixtures/evidence.sample.jsonl      # 期望 exit 0

python3 assets/expert-team/checks/verify_report.py \
        assets/expert-team/checks/fixtures/report.fail.sample.md \
        assets/expert-team/checks/fixtures/evidence.sample.jsonl      # 期望 exit 1 并列出四类违规
```

**pass 用例返回非 0，或 fail 用例返回 0，都说明闸门坏了——先修闸门，不要开始跑批次。**
