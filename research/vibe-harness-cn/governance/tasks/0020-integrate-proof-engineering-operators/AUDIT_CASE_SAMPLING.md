# Audit Case Sampling Decision

- Source: governance/tasks/0020-integrate-proof-engineering-operators
- Fixed Problem: 初次判断先于真实会话/项目读取，以及一次宽范围 JSON 补丁误触无关领域计数；前者已改为任务前置约束，后者已被既有全库 validator 阻断并修复。
- Decision: no-case
- Case ID: -
- Case Path: -
- Root Cause Class: source-inspection-order-and-unscoped-repeated-field-edit
- Trigger Signals: 来源型研究在未读取指定 source 时先下结论；大型结构化文件中同名字段多次出现；计数或引用验证失败。
- Evidence: governance/tasks/0020-integrate-proof-engineering-operators/RETROSPECTIVE_EVIDENCE.md；governance/tasks/0020-integrate-proof-engineering-operators/TASK_INTENT.json；`uv run --locked --script scripts/validate_harness.py --operator-library operators/catalog.json`。
- No-Case Reason: 两个模式都已被现有项目硬规则和机器门禁直接覆盖：AGENTS.md 已要求先查真实资料，Task Intent 已把 source inspection 固化为前置条件，Reference Library validator 已能精确阻断错误计数、引用和 taxonomy；新增案例不会增加新的审查问题或检测能力。

## Decision Values

- `case-created`
- `case-updated`
- `project-overlay`
- `promoted-to-gate`
- `no-case`

## Rule

`no-case` 不是跳过：只有现有规则和 validator 已覆盖同一触发信号、审查问题与证据要求时才能使用。
