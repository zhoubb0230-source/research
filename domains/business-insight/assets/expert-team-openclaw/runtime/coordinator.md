## OpenClaw 运行约定（总调度）

<!-- 由 install.sh 追加到 chief-coordinator 的 AGENTS.md 末尾。不要手工编辑生成产物。 -->

### 派发

用 `sessions_spawn`，**每次都要显式带上这五个参数**：

| 参数 | 取值 | 为什么必须显式 |
|---|---|---|
| `agentId` | 目标专家的 agentId | 全局 `requireAgentId: true`，不指名会被拒 |
| `context` | `"isolated"` | 它已是默认值，但显式传能防止线程绑定场景下悄悄变成 `fork` |
| `model` | 该专家 `entry.json5` 里的 `model` | **显式取值优先级最高**；不传时的继承行为文档未明确 |
| `thinking` | 该专家 `entry.json5` 里的 `thinkingDefault` | 同上 |
| `label` | 本次任务的短标题 | 出现在任务台账与会话列表里，便于事后审计 |

任务描述里必须自带批次根绝对路径、动作编号与范围、输入文件具体路径、
输出路径与 schema。**子会话看不到我的会话记录。**

### 等结果

子 Agent 完成后由 OpenClaw **push 式 announce 回来**，我不轮询。
`announceTimeoutMs` 已设为 600000（取证类任务远超默认的 2 分钟）。

### 派发深度

`maxSpawnDepth: 2`。拓扑是：

```
洞察总调度 (depth 0)
   └─ 11 位专家 (depth 1)
         └─ 采集工蜂 (depth 2，仅数据采集专家可派，且只能派它自己)
```

depth-2 是叶子，**永远拿不到 `sessions_spawn`**，不会再分叉。

### 并发

`maxConcurrent: 12`、`maxChildrenPerAgent: 20`。
**这两个数受你的模型速率限制约束，需实测回调。**
撞到限流的表现是子会话大面积超时，不是报错——看到这个先调低并发，不要先怀疑提示词。

### 发布

`bin/publish-report.sh` 是唯一通往发布目录的路径。我是唯一有 `exec` 的角色，
所以发布动作集中在一个可审计的点上。
