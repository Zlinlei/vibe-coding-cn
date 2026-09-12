# Task Status

- Overall Status: `Done`
- Snapshot: `2026-09-09`
- Source: Codex global security catalog upstream package
- Destination: project `skills/reference-only/`
- Current phase: physical move, integrity verification and documentation closeout complete.

# Task Package Status Table

| Node ID | Parent | Depth | Depends On | Ready | Status | Recent Evidence | Blocker | Unblock Needed |
|---|---|---:|---|---|---|---|---|---|
| TP-01 | ROOT | 1 | - | No | Done | 7 sources、目标路径、active 边界和 manifest 前置条件已核实 | - | - |
| TP-02 | ROOT | 1 | TP-01 | No | Done | 7 个来源及 catalog metadata 已移动到项目 reference-only | - | - |
| TP-03 | ROOT | 1 | TP-02 | No | Done | catalog、negative tests、manifest、governance strict/health 通过 | - | - |
| TP-04 | ROOT | 1 | TP-03 | No | Done | 文档结构、路径契约、任务索引和回滚说明已收口 | - | - |

# Next Executable Leaves

无。本任务已完成；未来按需激活 reference-only 内容时另建任务并重新执行授权、工具、隔离和证据检查。

# Blockers

- 无当前阻塞。

# Runtime State

- 项目 reference-only 包：7 个来源、932 个 `SKILL.md`，不参与 active skill 注册。
- 项目 active skill：13 个，`skills/SKILLS_MANIFEST.json` 未被本次迁移扩展。
- 全局 Codex：仅保留轻量 catalog/入口；原始完整 upstream、registry 和 manifests 已移出。
- 上游执行：未执行；后续使用必须经 owner workflow、授权、工具检查和隔离验证。
- 复用采样：`REUSE_SAMPLING.json` 已记录 `no_reuse_value` 并通过 strict validator。

## Rollback

移动失败或校验不通过时，停止后续步骤，不执行清理；将 reference-only 目录整体移回原 global source path，并恢复对应 registry 路径后重新校验。
