# Retrospective Evidence

## 时间线

- 用户明确纠正：必须先读取指定 Pi 会话和对应数学项目，再判断应新增的算子。
- 本轮随后把该要求写入 `TASK_INTENT.json` 的首条约束，并读取真实会话、案例报告、项目规范、证明 Skill、Schema 与循环脚本后形成 `OPERATOR_CROSSWALK.md`。
- 编辑多个 JSON 中的重复 `expected_count` 字段时，首次宽范围补丁误触了 `complexity-science` 与 `statistics` 计数；`validate_harness.py --operator-library` 立即失败并指出数量不一致。改为按领域核对后恢复原值，重新验证通过 `417 source / 60 derived / 477 total`。
- 第一轮项目 `behavior` / `test` 门禁发现 Reference Harness 测试、运行记录样例和活跃 QA 仍把变更前总数 `468` 写死；更新当前状态消费者后，测试改为从 catalog 动态计算总数，两项门禁原样重跑通过。
- 数学项目仅被读取，没有执行 Lean 构建、证明重放或上游代码；对外结论保持在 `source_locked / needs-replay` 证据边界。

## 可复发模式

1. 研究结论若先于真实 source inspection，会把聊天摘要或二手报告误当成项目事实。
2. 对含重复字段的大型 JSON 做无上下文补丁，可能改中语法却改错语义对象；精确计数 validator 是必要兜底。
3. 库数量同时被测试、样例和活跃 QA 消费；只更新库存文件和文档会留下可执行契约漂移，数量断言应尽量从单一 catalog 派生。

## 已采取的防复发措施

- 任务合同把“先读真实会话与项目”设为显式约束，crosswalk 对每个新增/复用决策绑定实际证据边界。
- 所有数量、ID、引用、taxonomy 与 Method 图继续由现有 Reference Library validator 复算；不新增第二套计数脚本。
- Reference Harness 测试从 `operators/catalog.json` 派生当前总数；运行记录样例和活跃 QA 同步到 `477`，最终项目门禁负责阻止遗漏。
