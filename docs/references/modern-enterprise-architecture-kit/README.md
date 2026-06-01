# 现代企业数字化平台 Starter Kit

本目录把《现代企业数字化平台架构说明文档》的 V2.2 起点转成可执行资产。

## 文件说明

| 文件 | 用途 |
| ---- | ---- |
| `domain.schema.json` / `domain.example.yaml` | 领域边界、owner、能力和上下游依赖模板。 |
| `service.schema.json` / `service.example.yaml` | 领域服务运行契约模板。 |
| `api-contract.schema.json` / `api-contract.example.yaml` | API producer、consumer、auth、版本和兼容策略模板。 |
| `event-contract.schema.json` / `event-contract.example.yaml` | 事件 topic、schema、幂等键、投递语义和消费者模板。 |
| `data-product.schema.json` / `data-product.example.yaml` | 数据产品契约模板。 |
| `ai-product.schema.json` / `ai-product.example.yaml` | AI 产品契约模板。 |
| `ai-tool-contract.schema.json` / `ai-tool-contract.example.yaml` | AI 工具输入输出、风险等级、人工确认、权限和审计模板。 |
| `rag-index-contract.schema.json` / `rag-index-contract.example.yaml` | RAG 来源、Embedding、切分、访问控制、刷新和删除策略模板。 |
| `fine-tuning-contract.schema.json` / `fine-tuning-contract.example.yaml` | 微调数据授权、实验追踪、评估、发布门禁和回滚模板。 |
| `catalog-component.schema.json` / `catalog-component.example.yaml` | catalog 组件登记模板。 |
| `catalog-data-product.schema.json` / `catalog-data-product.example.yaml` | catalog 数据产品登记模板。 |
| `catalog-ai-product.schema.json` / `catalog-ai-product.example.yaml` | catalog AI 产品登记模板。 |
| `gitops-deployment.schema.json` / `gitops-deployment.example.yaml` | GitOps 环境期望状态、镜像 digest 和准入策略模板。 |
| `production-readiness.schema.json` / `production-readiness.example.yaml` | 生产就绪门禁模板。 |
| `raci.schema.json` / `raci.example.yaml` | 决策权和职责矩阵模板。 |
| `tiering-policy.schema.json` / `tiering-policy.example.yaml` | 可靠性等级、RTO/RPO 和错误预算模板。 |
| `deprecation-policy.schema.json` / `deprecation-policy.example.yaml` | 迁移、兼容和弃用策略模板。 |
| `audit-evidence-index.schema.json` / `audit-evidence-index.example.yaml` | 审计证据索引模板。 |
| `scorecard.schema.json` / `scorecard.example.yaml` | 架构和生产就绪评分模板。 |

## 使用方式

1. 复制需要的 `*.example.yaml` 到目标项目对应目录。
2. 按 `*.schema.json` 的 required 字段补齐 owner、生命周期、风险等级和证据字段。
3. 运行仓库校验命令，验证 schema、示例、嵌套字段约束和示例间一致性：

```bash
make check-modern-architecture-kit
```

4. 目标项目落地时，应把这些 schema 接入 CI、Developer Portal、catalog 生成和发布准入。

## V2.2 校验范围

- 检查每组 `*.schema.json` 和 `*.example.yaml` 是否同时存在。
- 检查 schema 的 draft 版本、根类型、`required`、`properties`、`items`、`enum`、`pattern`、`minLength`、`minItems` 和 `format: date`。
- 检查示例 YAML 的类型、必填字段、枚举、命名格式、数组最小长度和日期格式。
- 检查 starter kit 示例中的领域、服务、API、事件、数据产品、AI 产品、AI 工具、RAG、微调、GitOps、catalog 和 scorecard 是否保持关键字段一致。

## 边界

- 本目录是企业架构 starter kit，不是某个真实业务系统的生产配置。
- schema 只定义最低字段基线，不替代企业内部更细的安全、合规、成本和行业监管要求。
- `make check-modern-architecture-kit` 是零依赖 starter gate，不替代生产级 JSON Schema、YAML、OpenAPI、AsyncAPI、Policy as Code、GitOps diff 和供应链安全校验器。
- 示例中的团队名、域名、服务名和指标值只用于说明，落地时必须替换为真实 owner 和真实目标。
