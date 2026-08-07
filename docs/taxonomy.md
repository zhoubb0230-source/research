# 分类体系与标签词表

分类是**两层固定 + 标签自由**：领域（domain）→ 内容类型（type）为固定维度，其余靠 `tags` / `vendors` 描述。检索时优先用固定维度收窄，再用标签过滤。

## 1. 领域（domain）

领域 ID 即目录名，全局唯一，小写短横线。

### `agent-platform` — 智能体平台

**收录**：Agent 编排与运行时、多智能体协作协议、工具调用/MCP、记忆与上下文工程、Agent 可观测与评测、智能体平台类产品（Dify、Coze、LangGraph、Bedrock Agents、字节/阿里/腾讯系平台等）、企业级 Agent 落地方案。

**不收录**：纯模型能力对比（属未来 `model` 领域）；仅面向编码场景的 Agent（归 `ai-coding`）。

**子主题（建议作为一级 tag）**：`orchestration` `multi-agent` `tool-use` `mcp` `memory` `rag` `runtime` `observability` `eval` `platform-product` `enterprise-landing`

### `ai-coding` — AI Coding 工具

**收录**：编码助手与编码 Agent（Claude Code、Cursor、Copilot、Windsurf、通义灵码等）、代码生成/补全/重构能力、代码库理解与索引、研发流程集成（CI、Code Review、测试生成）、编码类评测集与效能度量。

**不收录**：通用 Agent 平台机制（归 `agent-platform`，可用 `related` 互链）。

**子主题（建议作为一级 tag）**：`ide-assistant` `coding-agent` `cli-agent` `code-review` `test-gen` `repo-understanding` `benchmark` `devex-metrics` `enterprise-rollout`

### 待扩展领域（尚未建目录，需要时再建）

`model`（基础模型能力与选型）、`infra`（推理/训练基础设施）、`rag-search`（企业检索）、`ai-product`（AI 产品形态与商业化）。

## 2. 内容类型（type）

| type | 目录 | 判定标准 |
|---|---|---|
| `insight` | `insights/` | 面向"业界怎么做"，含横向对比、趋势判断、启示与建议 |
| `solution` | `solutions/` | 面向"我们怎么做"，含目标、架构、选型、里程碑、风险 |
| `vendor` | `vendors/` | 单一产品/厂商的事实档案，被 insight/solution 反复引用 |

## 3. 标签词表（tags）

标签用小写英文短横线，**新增标签必须登记到本节**，避免同义词发散。

### 技术主题
`orchestration` `multi-agent` `tool-use` `mcp` `memory` `context-engineering` `rag` `runtime` `sandbox` `observability` `eval` `guardrail` `cost-optimization` `identity` `authz` `data-isolation` `audit`

### 编码场景
`ide-assistant` `coding-agent` `cli-agent` `code-review` `test-gen` `repo-understanding` `benchmark` `devex-metrics`

### 视角
`market-landscape` （竞品格局）· `tech-route` （技术路线）· `architecture` （架构设计）· `selection` （选型）· `landing` （落地实施）· `enterprise-landing` （企业级落地）· `pricing` （商业与定价）· `security` （安全合规）

### 成熟度
`emerging` （早期）· `mainstream` （主流）· `deprecated` （已淘汰）

## 4. 厂商/产品词表（vendors）

统一使用小写短名，避免中英文混用导致检索失效。**新增产品必须登记到本节。**

### 智能体平台
`dify` `coze` `coze-studio` `langgraph` `langchain` `llamaindex` `autogen` `crewai` `bedrock-agents` `vertex-agent` `azure-ai-foundry` `n8n` `flowise` `bailian`（阿里百炼）`tencent-agent`

### 企业级 Agent 治理与基础设施
- 身份与授权：`entra-agent-id`（Microsoft Entra Agent ID / Agent 365）`keycloak` `openfga` `cedar` `spicedb` `okta-xaa`（Cross-App Access / ID-JAG）
- 网关：`agentgateway`
- 流程引擎：`camunda` `flowable` `activiti` `temporal`
- 企业 AI 应用与检索：`agentforce`（Salesforce）`glean` `m365-copilot`
- 数据与可观测：`milvus` `pgvector` `langfuse` `cozeloop` `promptfoo`

### AI Coding
`claude-code` `cursor` `github-copilot` `windsurf` `cline` `aider` `devin` `codex` `lingma`（通义灵码）`comate`（百度）`trae`

## 5. 状态（status）

`draft` 初稿未校验 → `review` 待评审 → `stable` 结论可引用 → `archived` 已过时（保留但不再维护，需在正文顶部标注失效原因）。

引用规则：对外汇报只引用 `stable`；`draft` 必须标注不确定性。
