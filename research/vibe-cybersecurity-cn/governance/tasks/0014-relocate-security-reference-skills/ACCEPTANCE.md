# Task-Level Acceptance

- `skills/reference-only/` 存在，且包含 7 个固定 source-id 目录、`source-registry.yaml` 和 7 份 manifests。
- 目标项目 active skill 仍为 13 个，现有目录和文件未被覆盖。
- 新 catalog validator 对 7 个来源全部通过，逐文件 SHA-256 无漂移。
- Codex 全局 `assets/upstream/`、global source registry 和 global manifests 不再保存完整参考包。
- 项目 governance strict/health 通过。
- 未执行任何上游 skill 内容、脚本、安装器、hook、插件或安全工具。
- 主要任务复用采样已生成并通过 `auto-assets` strict validator。

## Verification Commands

```bash
python3 <CODEX_SKILLS>/project/modules/security-catalog/scripts/validate_catalog.py --project-root .
bash <CODEX_SKILLS>/project/modules/security-catalog/scripts/test-catalog.sh .
python3 governance/tools/validate_governance_package.py --project-root . --strict
python3 governance/tools/governance_health_report.py --project-root . --strict
```

# Validation Plan

```bash
python3 <codex-home>/skills/project/modules/security-catalog/scripts/validate_catalog.py --project-root .
bash <codex-home>/skills/project/modules/security-catalog/scripts/test-catalog.sh .
python3 governance/tools/validate_governance_package.py --project-root . --strict
python3 governance/tools/governance_health_report.py --project-root . --strict
python3 <codex-home>/skills/task/modules/tasks/scripts/validate_task_docs.py --task-dir governance/tasks/0014-relocate-security-reference-skills --phase closeout
python3 <codex-home>/skills/project/modules/assets/scripts/validate_reuse_sampling.py --file governance/tasks/0014-relocate-security-reference-skills/REUSE_SAMPLING.json --task-root governance/tasks/0014-relocate-security-reference-skills --repo-root . --strict
```

# Review Gate

- `PASS`：新路径、来源元数据、逐文件摘要、active 边界和治理校验均与本任务契约一致。
- `WARN`：reference-only 内容尚未逐项准入审计；未来按需使用前必须由 owner workflow 重新审查。
- `BLOCK`：发现文件集合/摘要漂移、旧全局包仍存在、active skill 变化、上游内容被执行或任一 required validator 失败。

# Runtime Verification Gate

本任务为 `reference-only` 目录迁移，不运行上游内容。运行时验证仅覆盖 catalog/manifest、目录边界、任务文档和项目治理校验。

# Ship Readiness

本地交付包括项目 `skills/reference-only/`、全局轻量 catalog 路径契约、项目架构/治理文档和本任务 closeout 证据；不安装、不部署、不提交、不推送。

# Task Package Acceptance

- TP-01：来源、目标、active 边界、回滚和禁止动作已记录。
- TP-02：7 个来源及 registry/manifests 已迁移到项目 reference-only 目录。
- TP-03：完整性、边界、catalog negative tests、governance strict/health 已验证。
- TP-04：任务文档具备完整契约、状态为 Done，且无陈旧 global raw 路径作为真相源。

# Anti-Goals

- 不把 932 个 reference-only `SKILL.md` 注册为 Codex 全局或项目 active skill。
- 不以本次迁移结果替代来源逐项安全审计、授权判断或运行时隔离。
- 不执行任何上游脚本、安装器、hook、插件、命令或安全工具。
- 不使用破坏性 Git 操作清理并行工作区。
