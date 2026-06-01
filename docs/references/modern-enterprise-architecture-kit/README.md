# 现代企业数字化平台 Starter Kit

本目录把《现代企业数字化平台架构说明文档》的 V2.11 起点转成可执行资产，当前包含 43 组 schema/example。

V2.11 在严格 schema 模式之上补齐控制证据映射和审计导出清单。所有对象节点必须声明 `additionalProperties=false`，示例和落地契约中出现未声明字段会被门禁阻断。

## 文件说明

| 文件 | 用途 |
| ---- | ---- |
| `domain.schema.json` / `domain.example.yaml` | 领域边界、owner、能力和上下游依赖模板。 |
| `service.schema.json` / `service.example.yaml` | 领域服务运行、可靠性等级、RTO/RPO、on-call 和演练证据模板。 |
| `api-contract.schema.json` / `api-contract.example.yaml` | API producer、consumer、auth、版本和兼容策略模板。 |
| `event-contract.schema.json` / `event-contract.example.yaml` | 事件 topic、schema、幂等键、投递语义和消费者模板。 |
| `data-product.schema.json` / `data-product.example.yaml` | 数据产品契约、保留期、访问策略、审计、成本和 SLO 模板。 |
| `ai-product.schema.json` / `ai-product.example.yaml` | AI 产品风险、模型版本、SLO、预算、降级、供应商策略和数据使用模板。 |
| `ai-tool-contract.schema.json` / `ai-tool-contract.example.yaml` | AI 工具输入输出、风险等级、人工确认、权限和审计模板。 |
| `rag-index-contract.schema.json` / `rag-index-contract.example.yaml` | RAG 来源、Embedding、切分、访问控制、刷新和删除策略模板。 |
| `fine-tuning-contract.schema.json` / `fine-tuning-contract.example.yaml` | 微调数据授权、实验追踪、评估、发布门禁和回滚模板。 |
| `catalog-component.schema.json` / `catalog-component.example.yaml` | catalog 组件登记模板。 |
| `catalog-data-product.schema.json` / `catalog-data-product.example.yaml` | catalog 数据产品登记模板。 |
| `catalog-ai-product.schema.json` / `catalog-ai-product.example.yaml` | catalog AI 产品登记模板。 |
| `gitops-deployment.schema.json` / `gitops-deployment.example.yaml` | GitOps 环境期望状态、镜像 digest、ServiceAccount、Pod 安全、网络策略、HPA、PDB 和准入策略模板。 |
| `release-evidence.schema.json` / `release-evidence.example.yaml` | 发布 commit、GitOps revision、镜像 digest、pipeline run、测试、批准和验证证据模板。 |
| `supply-chain-attestation.schema.json` / `supply-chain-attestation.example.yaml` | SLSA、source control、SBOM、provenance、签名、证书、透明日志、漏洞扫描、Scorecard 和验签证据模板。 |
| `policy-exception.schema.json` / `policy-exception.example.yaml` | 治理例外、补偿控制、到期复审、补救计划和自动阻断模板。 |
| `api-compatibility-report.schema.json` / `api-compatibility-report.example.yaml` | API 兼容性检查、消费者影响、breaking change 和豁免状态模板。 |
| `event-compatibility-report.schema.json` / `event-compatibility-report.example.yaml` | 事件兼容性检查、消费者影响、重放要求和豁免状态模板。 |
| `gitops-drift-report.schema.json` / `gitops-drift-report.example.yaml` | GitOps 期望状态、运行观测状态、配置/策略漂移和发布阻断模板。 |
| `production-readiness.schema.json` / `production-readiness.example.yaml` | 结构化生产就绪证据、阻断规则、豁免策略和验证命令模板。 |
| `raci.schema.json` / `raci.example.yaml` | 决策权和职责矩阵模板。 |
| `tiering-policy.schema.json` / `tiering-policy.example.yaml` | 可靠性等级、RTO/RPO 和错误预算模板。 |
| `deprecation-policy.schema.json` / `deprecation-policy.example.yaml` | 迁移、兼容和弃用策略模板。 |
| `audit-evidence-index.schema.json` / `audit-evidence-index.example.yaml` | 审计证据索引模板。 |
| `scorecard.schema.json` / `scorecard.example.yaml` | 架构和生产就绪评分模板。 |
| `extension-policy.schema.json` / `extension-policy.example.yaml` | 严格 schema 下的受控扩展前缀、审批记录和未知字段处理模板。 |
| `feature-flag-control.schema.json` / `feature-flag-control.example.yaml` | Feature Flag、Kill Switch、灰度策略、SLO 燃尽回滚和曝光事件模板。 |
| `ai-threat-model.schema.json` / `ai-threat-model.example.yaml` | OWASP LLM / Agentic AI、MCP 工具同意、红队和残余风险模板。 |
| `lineage-event.schema.json` / `lineage-event.example.yaml` | 数据产品运行血缘事件、job、run、inputs、outputs、schema 和质量证据模板。 |
| `platform-product-metrics.schema.json` / `platform-product-metrics.example.yaml` | Platform PM、Golden Path、采用率、满意度、认知负载和平台 SLO 模板。 |
| `privacy-impact-assessment.schema.json` / `privacy-impact-assessment.example.yaml` | DPIA、处理目的、合法基础、主体权利、删除传播和 AI 使用限制模板。 |
| `tenant-boundary.schema.json` / `tenant-boundary.example.yaml` | 租户、namespace、ServiceAccount、Secret 范围、ResourceQuota、NetworkPolicy 和准入策略模板。 |
| `recovery-drill-evidence.schema.json` / `recovery-drill-evidence.example.yaml` | 恢复演练、RTO/RPO 目标、实际恢复结果、备份、恢复日志和复盘证据模板。 |
| `policy-test-report.schema.json` / `policy-test-report.example.yaml` | 策略引擎、测试数、失败数、阻断决策和执行命令证据模板。 |
| `genai-observability-contract.schema.json` / `genai-observability-contract.example.yaml` | OpenTelemetry GenAI、Token、成本、工具调用、RAG span、日志脱敏和留存模板。 |
| `cost-allocation-evidence.schema.json` / `cost-allocation-evidence.example.yaml` | 成本周期、owner、allocation tag、标签覆盖率、未分摊成本、成本来源和优化行动模板。 |
| `identity-access-review.schema.json` / `identity-access-review.example.yaml` | 身份源、角色、特权访问、break-glass、MFA 和访问复核证据模板。 |
| `secrets-rotation-evidence.schema.json` / `secrets-rotation-evidence.example.yaml` | Secret provider、KMS、静态加密、轮换结果和泄露扫描证据模板。 |
| `vulnerability-remediation-evidence.schema.json` / `vulnerability-remediation-evidence.example.yaml` | 漏洞 ID、严重度、KEV 状态、修复 SLA、残余风险和发布准入模板。 |
| `incident-postmortem.schema.json` / `incident-postmortem.example.yaml` | 事故影响、检测/恢复时间、根因、行动项、runbook 更新、门禁反哺和关闭审批模板。 |
| `evidence-freshness-policy.schema.json` / `evidence-freshness-policy.example.yaml` | 证据最大年龄、按类型过期策略、CI 执行和过期阻断模板。 |
| `control-evidence-map.schema.json` / `control-evidence-map.example.yaml` | 控制项到证据路径、状态、新鲜度、必需性和阻断属性的映射总账模板。 |
| `audit-export-manifest.schema.json` / `audit-export-manifest.example.yaml` | 审计导出包的版本、范围、内容、验证、签名和留存模板。 |

## 使用方式

1. 复制需要的 `*.example.yaml` 到目标项目对应目录。
2. 按 `*.schema.json` 的 required 字段补齐 owner、生命周期、风险等级和证据字段。
3. 运行仓库校验命令，验证 schema、示例、嵌套字段约束和示例间一致性：

```bash
make check-modern-architecture-kit
```

4. 目标项目落地时，应把这些 schema 接入 CI、Developer Portal、catalog 生成和发布准入。

## V2.11 校验范围

- 检查每组 `*.schema.json` 和 `*.example.yaml` 是否同时存在。
- 检查 `modern-enterprise-architecture-version.json` 中的当前版本、发布状态、pair 数量、pair 名称、控制项数量和索引提及是否一致。
- 检查 `modern-enterprise-architecture-controls.json` 中的控制项是否能追溯到 schema 字段、example 字段和 checker 规则。
- 检查 schema 的 draft 版本、根类型、`required`、`properties`、`items`、`enum`、`pattern`、`minLength`、`minItems`、`minimum`、`maximum`、`format: date` 和 `format: date-time`。
- 检查所有对象 schema 是否声明 `additionalProperties=false`，并阻断 YAML 示例中的未知字段。
- 检查示例 YAML 的类型、必填字段、枚举、命名格式、数组最小长度和日期格式。
- 检查 starter kit 示例中的领域、服务、API、事件、数据产品、AI 产品、AI 工具、RAG、微调、GitOps、catalog、scorecard、发布证据、供应链证明、治理例外、兼容性报告和漂移报告是否保持关键字段一致。
- 检查服务可靠性等级、GitOps ServiceAccount、生产供应链策略、AI 工具风险映射、AI 预算 owner、供应链漏洞和 Scorecard 结果是否形成可阻断门禁。
- 检查扩展字段策略、Feature Flag、AI 威胁模型、数据运行血缘、平台产品指标、隐私影响评估、租户隔离、恢复演练、策略测试、GenAI 观测、成本分摊证据、访问复核、密钥轮换、漏洞修复、事故复盘、证据新鲜度、控制证据映射和审计导出清单是否形成 schema、example 和 checker 证据链。

## 边界

- 本目录是企业架构 starter kit，不是某个真实业务系统的生产配置。
- schema 只定义最低字段基线，不替代企业内部更细的安全、合规、成本和行业监管要求。
- 需要企业自定义字段时，必须先把字段纳入 schema、示例、控制项或明确的扩展字段策略，不能用未知字段绕过治理。
- `make check-modern-architecture-kit` 是零依赖 starter gate，不替代生产级 JSON Schema、YAML、OpenAPI、AsyncAPI、Policy as Code、GitOps diff 和供应链安全校验器。
- 示例中的团队名、域名、服务名和指标值只用于说明，落地时必须替换为真实 owner 和真实目标。
