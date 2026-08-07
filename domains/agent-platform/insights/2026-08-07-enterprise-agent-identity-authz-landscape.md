---
id: agent-platform-insight-0001
title: 企业级 Agent 的身份、授权与数据隔离：九个业界范式
domain: agent-platform
type: insight
status: draft
created: 2026-08-07
updated: 2026-08-07
tags: [identity, authz, data-isolation, audit, mcp, rag, guardrail, market-landscape]
vendors: [entra-agent-id, agentforce, glean, m365-copilot, openfga, cedar, camunda, agentgateway]
related: [agent-platform-solution-0001]
summary: 严肃的企业级 Agent 方案都把重心放在身份、授权、审计，而非编排能力
---

# 企业级 Agent 的身份、授权与数据隔离：九个业界范式

> 来源说明：本文由外部调研整理，【业界】标记的内容据称有公开产品文档/论文/官方博客支撑，来源清单见文末。**多数条目只给了机构与文档名，缺少精确 URL 与访问日期**，少数条目（Camunda 2026 报告数据、MCP 2026-07-28 修订内容）尚未独立核实——引用前请按文末「待核清单」逐条验证。当前状态 `draft`，不可直接对外汇报。

## TL;DR

- **技术难点不是"能不能跑起来一个 Agent"，而是身份、授权、审计三件事。** 业界所有严肃的企业级方案（Microsoft Entra Agent ID、Salesforce Agentforce、Glean）都把重心放在这里，而不是编排能力本身——编排能力已经是开源商品化组件。
- **数据隔离必须做在架构里，不能做在提示词里。** Glean 的架构原则是"模型收不到的信息就泄不出去"：权限校验发生在检索层、在模型之外。任何依赖"提示词里写了不许透露他人数据"的方案，在红队测试下都会失效。
- **"用户问到他人数据"的根因多数不在 AI，而在源系统里早已存在的过度共享。** 微软为 Copilot 专门出了过度共享治理蓝图（Pilot → Deploy → Operate），并把"上线前先做过度共享评估与整改"作为部署前置。AI 只是把历史权限债务变得"可被一句话问出来"。
- **开源选型应当"分层组装"，而不是"选一个平台包打天下"。** 主流开源 Agent 平台的企业级权限与审计能力偏弱（Dify 社区版官方文档明确不支持多个工作空间），应让运行时不承担权限判定职责，鉴权下沉到网关 + 独立授权引擎。
- **流程节点上的护栏必须是结构化的，不能是提示词式的。** 写在系统提示词里的"删除前必须审批"只是建议；建模为必须经过人工审批的流程子过程才是强制。
- **对我们的启示**：能力越强的数字员工，越要靠架构收窄而不是靠模型自觉。落地设计见 `agent-platform-solution-0001`。

## 1. 身份范式：Microsoft Entra Agent ID / Agent 365【业界】

问题意识（微软官方博客原话大意）：

- **过度授权**：Agent 常在运行时获得权限、随时间累积、且无限期保留，风险成倍放大。
- **无人担责**：当 Agent 自主行动时，谁来负责？没有明确责任人，就没人对其访问权和生命周期负责。
- **人工生命周期管理无法规模化**：管理成百上千个跨平台 Agent，需要可规模化的一致治理策略。

其解法：

- Agent 在目录中是**一等身份账号**（Agent Identity），拥有独立的登录历史、审计轨迹、授予范围，可作为条件访问策略的目标主体。
- 纳入身份治理：生命周期管理、访问评审、权限包管理，覆盖从注册、凭据管理到停用、下线的全周期。
- 每个 Agent 必须有**责任人（sponsor）**提供全生命周期监督。
- 支持 On-Behalf-Of（OBO）代客模式，并把"人→Agent 的委派关系"本身作为治理对象。
- 通过 CLI/SDK 为其他框架（含 LangChain、CrewAI、AWS Bedrock、各家 Agent SDK）的 Agent 统一签发身份。

**启示**：数字员工必须在企业 IdP 中有独立身份和责任人，且"授权"要能被定期评审和自动回收。

## 2. 权限继承范式与其风险：Salesforce Agentforce【业界】

- Agentforce 的模型是 **Agent 继承其运行用户的访问权限**，会暴露该用户能访问的全部组织数据。
- 由此带来的实际风险（第三方安全厂商总结）：Agent 往往获得远超任务所需的敏感数据访问权；甚至能以高于构建者本人的权限访问和操作数据；业务团队可在无安全评审的情况下自建并部署 Agent，形成"影子 Agent"。
- 官方侧的对策：Einstein Trust Layer（送模型前脱敏、零留存、毒性检测、全量审计日志、可配置的数据访问控制）；Agent Script 使 Agent 行为更确定化，执行前即定义可走哪些步骤、按什么顺序；Agentforce Observability 提供会话轨迹与指令遵循率监控。

**启示**：单纯"继承用户权限"是必要但不充分的。必须叠加"任务最小权限"这一层，否则数字员工就是一个把用户全部历史权限债务放大暴露的入口。

## 3. 检索侧隔离范式：Glean【业界】

- **ACL 镜像**：爬取时同时抓取内容和其访问控制列表，把源系统的 ACL（用户、组、团队、仓库/项目级权限）原样附加到每个文档/代码文件上。
- **查询时强制**：即使查询在语义上命中内容，也要先校验该用户是否有权查看底层文档，才决定是否返回。
- **零拷贝倾向**：内容尽量留在源位置，只缓存索引向量与元数据，减少数据扩散面。
- **权限检查在模型之外**：模型收不到的信息就泄不出去；安全由架构保证，而不是交给模型自觉。
- **不覆盖源系统**：只从 IdP 读取组和成员关系，从不覆盖数据源的 ACL；文档级和应用级权限始终由源系统裁定。
- 自定义数据源接入时，索引 API 要求显式声明 `allowedUsers` 等权限字段；使用非匿名权限时，用户必须先被索引才能被引用。
- 一个重要经验：**"藏得深所以安全"是反模式**。搜索和 AI 让这条彻底失效——只要被索引，就能被找到。用户觉得某个结果过于敏感时，第一步永远是回去查源文档的 ACL，绝大多数情况是源应用里的权限设置本身就过宽。

## 4. 源端治理范式：Microsoft 365 Copilot 过度共享治理【业界】

微软的部署蓝图结构为 **Pilot → Deploy → Operate**，核心工具与动作：

| 阶段 | 动作 | 工具 |
|---|---|---|
| 评估 | 识别过度共享站点、风险共享链接、敏感内容、无主/失活站点、权限继承断裂 | Purview DSPM for AI 数据风险评估、SAM 内容管理评估、数据访问治理报告 |
| 临时遏制 | 在整改完成前先降低暴露面 | **RCD（限制内容发现）**：一个开关把整站从 Copilot/Agent 检索与全租户搜索中屏蔽，且不改变站点权限；**DLP for Copilot**：把敏感内容排除在模型接地之外 |
| 整改 | 修复底层权限、补齐站点属主、访问评审 | RAC（限制访问控制，白名单锁定）、站点生命周期管理 |
| 常态运营 | 新建站点默认安全、持续监控 | 租户级默认策略、关闭全员共享组与"任何人"链接、自动化访问评审 |

一个值得注意的细节：RCD 只影响租户级搜索与 Copilot 的**发现类**场景，不影响"总结当前文档"这类数据在用场景，也不会把内容移出搜索索引（不影响电子取证等合规功能）。这说明**"检索可见性"与"访问权限"是两个正交的控制维度**。

## 5. 授权引擎范式：Zanzibar / OpenFGA / Cedar【业界】

- OpenFGA 是 Google Zanzibar 论文的开源实现，CNCF 托管、Okta 维护，采用 **ReBAC（基于关系的访问控制）**：把授权建模为"对象—关系—主体"的元组图，可同时表达 RBAC 与 ABAC。
- 在 RAG 场景的价值：RBAC 的粒度是"HR 文档"这样一个宽泛类别，而 FGA 在查询时逐块判定用户与该 chunk 是否存在有效关系，不满足则整块过滤掉。同一个问题，不同用户得到不同深度的答案。
- **预过滤 vs 后过滤的取舍**（Descope 的分析）：在向量库里做预过滤会遇到权限同步滞后、元数据爆炸、复杂权限下的性能开销；因此他们主张**后置过滤**——让向量库专心做语义检索，让 Zanzibar 式服务专心做实时鉴权，并用"迭代重查询循环"分页补齐被过滤掉的结果，直到凑够目标上下文条数。
- 值得注意的局限（学术综述指出）：Zanzibar 模型及其后继者是为"人类主体访问静态资源"设计的，并未原生解决多 Agent 系统中的委派链问题。

## 6. 流程嵌入范式：Camunda Agentic Orchestration【业界】

- 定位：在**单一受治理的业务流程内**协调 AI Agent、人和系统。Agent 被嵌入流程之中：确定性步骤处理可预测逻辑，Agent 接管需要推理、规划、记忆和检索的部分。
- **职责切分**（最值得借鉴的设计）：
  - LLM 负责：解读系统提示、当前用户提示和可用工具描述，决定调用哪个工具、什么顺序、什么参数。
  - 流程引擎负责：执行被选中的流程活动、保存流程状态、重试与异常处理、协调人工任务和其他确定性逻辑。
  - Agent 可调用的每个工具，都是 ad-hoc 子流程里的一个流程活动——"一个受治理的工具箱"。
- **结构化护栏 > 提示词护栏**：把审批步骤、合规检查、升级路径建模进流程本身，而不是写成提示词里的一句话。提示词里的"删除前必须审批"是建议；流程里的强制人工审批子过程是约束，Agent 绕不过去。
- **自治度是渐进的**：同一个 BPMN 模型里可以同时存在完全确定性步骤、混合步骤（Agent 提议、人或规则确认）、完全自治步骤（Agent 在护栏内自行决策）。今天可以只让 Agent 做建议、人始终在环；随着模式稳定、信任建立，再逐步调高自治度——先自动通过低风险案例，再扩大阈值，再扩展类别。
- **失败必须是一等公民**：配置最大规划循环次数与重试次数；返回结构化的"无法完成"结果并附原因与上下文；按流程模型升级给另一个 Agent 或人工任务。这样失败在运维台上可观测、可审计，也能控制成本。
- **流程引擎是状态与历史的唯一真相源**，Agent 保持无状态或短状态。
- 数据参考（**待核**）：其 2026 年报告称 71% 的组织在使用 AI Agent，但过去一年只有 11% 的 agentic 用例进入了生产。

## 7. 协议与令牌范式：MCP 授权规范演进【业界】

MCP 授权规范经过 2024-11-05、2025-03-26、2025-06-18、2025-11-25、2026-07-28 多次修订，跨版本稳定不变的硬要求有五条：

1. MCP Server 的角色是 **OAuth 2.1 资源服务器**，不是授权服务器（授权服务器与资源服务器角色分离）。
2. 必须实现 RFC 9728 受保护资源元数据；未授权时返回 401 并在 `WWW-Authenticate` 头中携带 `resource_metadata` 地址。
3. 客户端**必须**在授权请求和令牌请求中都携带 RFC 8707 的 `resource` 参数，无论授权服务器是否声称支持——令牌因此被绑定到唯一目标服务器，把"可重放的持有者凭据"变成"单一目的地凭据"。
4. **受众校验**：服务器必须验证令牌是签发给自己的，拒绝签发给其他服务的令牌。这是规范的安全核心，也是大多数自研服务器翻车的地方。
5. **禁止令牌透传**：服务器不得接受或转发不是签发给它的令牌。如需代表用户调用下游 API，必须重新获取一个面向下游受众的令牌——常见实现是 RFC 8693 令牌交换或 OBO 流程。

违反 3~5 的后果就是**混淆代理（confused deputy）**：下游服务错误地信任了并非为它签发的令牌。

**待核**：2026-07-28 修订据称进一步引入 RFC 9207 签发者校验（防 IdP 混淆攻击）并收紧客户端注册，同时远程传输转为无状态、移除会话。

## 8. 跨应用委派范式：ID-JAG / Cross-App Access【业界】

- **ID-JAG（Identity Assertion JWT Authorization Grant）**是 IETF 正在标准化的 OAuth 扩展（draft-ietf-oauth-identity-assertion-authz-grant），Okta 的 Cross-App Access（XAA）是其商业实现与品牌名。
- 核心思想：把企业 SSO 已建立的信任关系延伸到 API 调用——IdP 不仅管"谁能登录哪个应用"，还管"哪个应用能代表用户调用哪个应用的 API"。
- 流程：用户 SSO 登录 Agent/应用 → 应用把身份断言在企业 IdP 换成 ID-JAG（OAuth 2.0 令牌交换）→ 把 ID-JAG 作为 JWT 授权许可向资源方授权服务器换取该资源作用域的访问令牌 → 调用资源。用户全程不看到 OAuth 同意页，是否放行由企业 IdP 按管理员策略预先决定。
- 为什么 Agent 场景推动了它：Agent 无法为了一个同意弹窗而暂停工作流，也不应长期持有 API Key；IdP 集中执行策略、签发短时效令牌、保留审计轨迹。
- 生态状态：仍是 IETF 草案，应用支持尚早期；已有开源实现跟进（如 LY Corporation 的 Athenz），agentgateway 社区也在讨论原生支持。

## 9. 攻击面参考：OWASP Agentic 威胁与提示注入设计模式【业界】

OWASP Agentic 威胁清单中与企业级 Agent 强相关的几条：

- **记忆投毒**：恶意数据被持久化进 Agent 记忆，影响后续会话**或其他用户**。
- **工具滥用**：通过欺骗性提示诱导 Agent 滥用已集成工具。
- **权限失陷**：权限管理弱点被利用，常见于动态角色继承与配置错误。
- **过度自治**：Agent 在缺乏适当人工监督的情况下执行高影响动作。
- **身份伪造与冒充**、**多 Agent 通信投毒**、**级联失效**。

对应控制建议：按会话/主题分区记忆以防止跨会话跨租户污染；仅允许可信来源写入记忆并追踪来源；每工具一份最小权限档案；高影响动作要求动作级认证与人工确认，并提供预演/dry-run。

提示注入的架构级对策（arXiv 2506.08837 提出的六种设计模式）：

- 核心原则：**一旦 Agent 摄入了不可信输入，就必须被约束到该输入不可能触发任何有后果的动作**。
- **Action-Selector**：Agent 只做"自然语言 → 预定义安全动作"的翻译，不接受动作结果回流。
- **Plan-Then-Execute**：先定计划再执行，不可信数据无法改变动作序列（一种控制流完整性保护），但仍可影响动作参数。
- **LLM Map-Reduce**：不可信数据在隔离的 map 环节分别处理，再由受控的 reduce 环节汇总。
- **Dual LLM**：特权 LLM 有工具但从不直接处理不可信数据，隔离 LLM 处理不可信数据但无任何工具；结果只以引用形式传递，由编排器在调用时解引用。
- **Code-Then-Execute**（CaMeL 思路）：特权 LLM 生成沙箱 DSL 代码，可做完整数据流分析，被污染的数据可被标记并全程追踪。
- **Context-Minimization**：最小化进入上下文的内容。

论文作者的诚实结论：只要 Agent 和其防御都依赖当前这代语言模型，通用型 Agent 就很难提供有意义且可靠的安全保证。**这直接支撑"能力越强的数字员工，越要靠架构收窄而不是靠模型自觉"这一设计取向。**

## 待核清单

引用本文任何数据前，以下条目需先补齐来源链接与访问日期：

| # | 待核内容 | 所在章节 | 风险 |
|---|---|---|---|
| 1 | Camunda 2026 报告的 71% / 11% 两个数字 | §6 | 数字被直接引用于汇报，出处必须精确到报告名与页码 |
| 2 | MCP 2026-07-28 修订的具体变更（RFC 9207、无状态传输） | §7 | 影响令牌链设计，须核对规范原文 |
| 3 | 全部来源的精确 URL 与访问日期 | 文末 | 规范要求，当前仅有机构与文档名 |
| 4 | Agentforce 权限继承风险的第三方分析出处 | §2 | 第三方安全厂商结论，需确认非营销材料 |

## 参考资料

> 以下为原始调研给出的来源清单，**尚未补齐 URL 与访问日期**。

**身份与治理**
- Microsoft Entra Agent ID 文档与治理概述：learn.microsoft.com/entra/agent-id/、learn.microsoft.com/entra/id-governance/agent-id-governance-overview
- Microsoft Entra 博客：Govern AI agent identities and access the same way you govern your employees
- Microsoft Entra 博客：Build AI agents for production with secure identities from day one

**权限继承与风险**
- Salesforce：Best Practices for Secure Agentforce Implementation；AI Guardrails
- Varonis / Obsidian Security 对 Agentforce 权限继承风险的分析

**检索侧隔离**
- Glean 文档：How Glean Code Search Works、Permissions and security controls、RBAC FAQ、Indexing API Permissions
- Glean 博客：Secure generative AI for the enterprise requires the right permissions structure

**源端治理**
- Microsoft Learn：Configure a secure and governed foundation for Microsoft 365 Copilot；Restricted Content Discovery
- Microsoft 社区博客：Mitigate Oversharing to Govern Microsoft 365 Copilot and Agents

**授权引擎**
- openfga.dev 文档与概念页
- Descope：Adding Performant ReBAC to RAG Pipelines at Scale
- Couchbase：Securing Agentic/RAG Pipelines with Fine-Grained Authorization

**流程编排**
- Camunda 8 文档：AI agents、Design and architecture（agentic orchestration）
- Camunda 博客：Guardrails and Best Practices for Agentic Orchestration；Why BPMN (Still) Matters；Designing A2A Orchestration with Camunda

**协议与令牌**
- Model Context Protocol 授权规范（2025-06-18 / 2025-11-25 / 2026-07-28 修订）及安全最佳实践
- IETF draft-ietf-oauth-identity-assertion-authz-grant（ID-JAG）
- Okta Developer：Enable Your SAML Requesting App for Cross App Access

**攻击面**
- OWASP AI Agent Security Cheat Sheet；OWASP Top 10 for Agentic Applications
- arXiv 2506.08837《Design Patterns for Securing LLM Agents against Prompt Injections》
- Google DeepMind CaMeL：Defeating Prompt Injections by Design
