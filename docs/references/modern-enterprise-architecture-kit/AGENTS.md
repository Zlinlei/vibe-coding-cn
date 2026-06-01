# Starter Kit 目录 Agent 指南

## 目录职责

本目录维护现代企业数字化平台架构的可执行 starter kit，包括 JSON Schema、YAML 示例和验证入口。

## 文件地图

```text
modern-enterprise-architecture-kit/
├── README.md
├── AGENTS.md
├── *.schema.json     # 机器可读最低字段基线
└── *.example.yaml    # 与 schema 对应的落地示例
```

## 修改规则

- 新增 schema 时必须同时新增同名 `*.example.yaml`。
- schema 必须使用 JSON Schema draft 2020-12，根类型必须是 `object`。
- 每个 schema 必须声明 `required`，关键嵌套对象也应声明自己的 `required`。
- schema 中的关键命名、日期、数组和字符串约束应尽量用 `pattern`、`format`、`minItems` 和 `minLength` 表达。
- 示例必须通过同名 schema 校验，并保持领域、服务、API、事件、数据产品、AI 产品、AI 工具、RAG、微调、GitOps、catalog、scorecard、发布证据、供应链证明、治理例外、兼容性报告和漂移报告之间的基础一致性。
- 示例只放最低可执行字段，不写敏感信息、真实域名、真实密钥或真实客户数据。
- 修改本目录后必须运行 `make check-modern-architecture-kit` 和 `make test`。

## 边界

- 本目录不承载真实环境部署状态。
- 本目录不替代主架构文档，只提供可执行模板和校验证据。
