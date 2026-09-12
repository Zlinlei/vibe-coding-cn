# Execution Checklist

[x] TP-01 | P0 | 迁移前置检查与路径契约 | Verify: source/destination、工作区和旧路径依赖已核实 | Gate: 不覆盖既有 active skill | Parallelizable: No
[x] TP-02 | P0 | 跨仓库目录移动 | Verify: 7 个来源及 catalog metadata 到位 | Gate: 不执行上游内容 | Parallelizable: No
[x] TP-03 | P0 | 完整性、边界与治理验证 | Verify: catalog + governance strict/health | Gate: 文件集合和摘要无漂移 | Parallelizable: No
[x] TP-04 | P1 | 文档与状态收口 | Verify: 文档、任务状态、回滚说明一致 | Gate: 无陈旧路径 | Parallelizable: No

说明：
- 每一行均绑定 `TP-XX` 叶子节点。
- 本任务已完成，后续 reference-only 使用需另行建立授权和运行时验证任务。
