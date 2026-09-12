# Planning Summary

## TP-01：迁移前置检查

- 确认 source 存在、destination 不存在、目标 active skill 无同名目录覆盖。
- 运行迁移前 catalog validator，固定 7 个来源和 manifest 证据。
- 检查两个仓库工作区状态，不整理其他并行改动。

## TP-02：目录移动

- 将 `assets/upstream/` 整体移动到项目 `skills/reference-only/`。
- 将 source registry 和 manifests 一并移动到 reference-only 根，避免双份供应链真相。
- 不使用复制后删除，不覆盖目标既有文件。

## TP-03：验证

- 用项目根参数运行 catalog validator 和 catalog negative tests。
- 检查来源数量、`SKILL.md` 数量、文件集合、SHA-256、symlink 和 active skill 数量。
- 运行项目 governance strict/health；不运行上游内容。

## TP-04：收口

- 更新项目与全局 catalog 文档、拓扑、toolchain、manifest 说明和任务状态。
- 记录剩余风险：reference-only 审计不等于逐项准入，57 个可执行脚本仍禁止自动运行。

# Lifecycle Gates

`SPEC -> PLAN -> BUILD -> TEST -> REVIEW -> SHIP`，任一 gate 不得跳过；本任务的目录移动属于 BUILD，catalog/manifest/governance 校验属于 TEST，文档与边界复核属于 REVIEW，状态收口属于 SHIP。

# Simplest Path

- 先确认目标目录与 active skill 无冲突，再整体移动目录和 metadata。
- 复用既有 source registry、SHA-256 manifests、catalog validator 和 governance validator，不新增迁移脚本。
- 只更新路径契约、项目架构文档和任务文档，不执行上游内容，不整理其他并行改动。

# Split Strategy

- TP-01：迁移前置检查与路径契约。
- TP-02：跨仓库目录移动。
- TP-03：完整性、边界与治理验证。
- TP-04：文档与状态收口。

# Execution Waves

```text
TP-01 -> TP-02 -> TP-03 -> TP-04
```

# Runtime Workflow Contract

- Allowed：只读盘点、同一文件系统内的明确目录移动、路径契约/文档编辑、本地校验命令。
- Forbidden：执行上游 `SKILL.md`、脚本、安装器、hook、插件或安全工具；安装全局 skill；修改来源元数据；push 或破坏性 Git 操作。
- Evidence：来源 registry、manifest 摘要、文件计数、旧路径不存在、新路径 validator 结果、治理 strict/health 结果。
- Stop：目标冲突、文件集合/摘要漂移、active skill 被覆盖、validator 失败且无法定位时停止后续收口。

# Next Executable Leaves

无。本任务已完成；后续如需使用任一 reference-only skill，应另行建立授权、工具、隔离和证据边界明确的安全/逆向任务。

# Dependency Graph

```text
全局 catalog 与项目 active manifest
              |
              v
TP-01 前置检查 --> TP-02 目录移动 --> TP-03 完整性/治理验证 --> TP-04 文档收口
```

# Rollback Protocol

- 若迁移或验证失败，停止后续步骤，不执行清理或覆盖。
- 在确认目标目录与原目录状态后，将同一 `reference-only/` 目录整体移回原 global source path，并恢复对应 registry/manifest 路径契约。
- 回滚后重新运行 catalog、manifest 和 governance 校验；不得影响项目现有 13 个 active skill 或其他任务目录。
