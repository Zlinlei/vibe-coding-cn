# Acceptance Checklist

## Migration Boundary

- [x] 7 个来源整体移动到 `skills/reference-only/`。
- [x] global raw source、registry、manifests 不再保留内容副本。
- [x] 13 个 active skill 未被覆盖或重新注册。

## Provenance and Integrity

- [x] commit、许可证、activation 和 `reference-only` 状态保持不变。
- [x] 逐文件 SHA-256 manifest 校验通过。
- [x] 无 symlink，未执行上游内容。

## Governance

- [x] AGENTS、README、PROJECT-TOPOLOGY、PROJECT_OPERATING_MODEL、TOOLCHAIN_MODEL 已同步。
- [x] governance strict/health 通过。
- [x] 任务状态和剩余风险已收口。

# Global Standards

- [x] reference-only 内容与 active skill 分层，未扩大默认扫描/触发面。
- [x] 来源 commit、许可证、registry 和 SHA-256 manifest 保持可追溯。
- [x] 外部内容按不可信数据处理，未执行上游内容。
- [x] 未执行破坏性 Git 或全局安装动作。
- [x] 主要任务复用采样已生成并通过 strict validator。

# Task Package Checklists

## TP-01 迁移前置检查与路径契约

- [x] 已确认原目录、目标目录、7 个来源和 active skill 边界。
- Verify: 前置路径与来源 registry/manifest 记录一致。
- Gate: 目标不存在冲突，且不得覆盖现有 13 个 active skill。

## TP-02 跨仓库目录移动

- [x] 7 个 source-id 目录整体位于 `skills/reference-only/`。
- [x] `source-registry.yaml` 与 7 份 manifests 随参考包位于目标根。
- Verify: 新目录文件集合和来源 metadata 完整，旧 global raw/registry/manifest 路径下无文件内容（空目录不构成内容副本）。
- Gate: 不复制双份真相，不执行上游内容，不注册 active skill。

## TP-03 完整性、边界与治理验证

- [x] catalog validator 通过。
- [x] catalog negative tests 通过。
- [x] governance strict/health 通过。
- Verify: 932 个 `SKILL.md`、0 个 symlink、active skill 13 个，且 manifest 摘要无漂移。
- Gate: 任一 required validator 失败即 BLOCK。

## TP-04 文档与状态收口

- [x] 项目 root/skills/catalog/治理文档已同步新路径和 reference-only 边界。
- [x] 任务状态、索引、回滚说明和剩余风险已记录。
- Verify: closeout validator 通过，文档无残留占位符或陈旧路径。
- Gate: 状态为 `Done` 且无未完成叶子节点。
