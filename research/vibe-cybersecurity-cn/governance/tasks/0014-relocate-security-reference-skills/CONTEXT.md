# Repo Evidence

## Current Facts

- Source: `<codex-home>/skills/project/modules/security-catalog/assets/upstream/`
- Destination: `<cybersecurity-project-root>/skills/reference-only/`
- Scope: 7 个固定来源、932 个 `SKILL.md`、5,671 个文件、约 42.7 MB logical bytes。
- Default activation: `reference-only`。
- Destination active contract: `skills/SKILLS_MANIFEST.json` 继续只管理现有 13 个 active skill。

## Target End State

Codex 全局只保留轻量安全 catalog、策略和校验器；完整上游参考包、source registry 和 SHA-256 manifests 的唯一内容位置是项目 `skills/reference-only/`，按 source-id 隔离并按需读取。

## Real Constraints

- 用户明确要求不把大量安全 skill 放在全局根目录。
- 现有项目 active skill 与其 manifest 必须保持不变。
- 来源 commit、许可证、完整性 manifest 和 reference-only 语义必须保持可追溯。
- 外部内容必须按数据处理，不能自动执行。

## Inertia Constraints

- 旧 global `assets/upstream/` 路径和旧 catalog 默认路径不能继续作为终态真相源。
- 既有 0007 任务的 13 个 active skill 结论是历史事实，不因本次 reference-only 迁移改写。

## Falsifier and Proof Point

- Proof point：项目 catalog validator 对新路径 7 个来源全部通过，移动前后 manifest 校验一致，旧 global raw 路径不存在。
- Falsifier：出现文件集合/摘要漂移、active skill 被覆盖、global validator 无法定位项目 catalog，或项目治理 strict/health 失败。

# Constraints Matrix

| 约束 | 强制决策 |
|---|---|
| 用户要求不污染全局上下文 | 完整安全/逆向参考包只存项目 `skills/reference-only/` |
| active skill 边界 | `skills/SKILLS_MANIFEST.json` 继续只管理现有 13 个 active skill |
| 供应链可追溯 | 保留来源 ID、固定 commit、许可证、registry 和 SHA-256 manifest |
| 外部内容不可信 | 不自动执行上游 `SKILL.md`、脚本、安装器、hook、插件或工具 |
| 并行工作区安全 | 不执行 reset、clean、stash、强制 checkout 或其他破坏性 Git 操作 |

# Change Boundary

- 允许：跨仓库移动 reference-only 目录、更新 catalog 路径契约、同步项目架构/治理文档和任务状态。
- 不允许：覆盖项目现有 active skill、修改来源内容/commit/许可证、把 reference-only 目录注册为 active skill 或全局 skill。

# Risk Matrix

| 风险 | 影响 | 控制 |
|---|---|---|
| 大量文件移动遗漏或漂移 | 供应链完整性失真 | 逐文件 SHA-256 manifest、文件集合和来源计数校验 |
| reference-only 被递归注册 | 全局上下文膨胀或误触发 | 目录隔离、项目 manifest 分层和不注册约束 |
| 路径契约陈旧 | 后续 validator 找不到来源 | catalog validator 显式接收项目根并检查旧路径不存在 |
| 参考内容被误执行 | 越权或不受控副作用 | 仅按数据读取；执行前须经 owner workflow、授权和工具边界 |

# Assumptions and Falsification

- 假设：用户希望完整上游包保留在项目内，但默认不参与 active skill 扫描；若用户要求按类别准入，则另建审计/准入任务，不改变本任务边界。
- 假设：固定 commit、许可证和 manifest 是本次迁移必须保持的供应链真相；若任一摘要不一致，则以校验失败为准停止收口。
- 推翻条件：项目 catalog validator 无法定位新路径、文件集合或摘要漂移、active skill 数量变化，或治理 strict/health 失败。

# Critical Ambiguities

- reference-only 资料未来按需激活的 owner workflow 和授权范围仍由后续安全任务决定，本任务不授予执行权。
- 57 个可执行文件的存在不代表安全性或可运行性，后续使用前仍需单独工具/授权/隔离检查。
- 当前不做来源内容逐项质量重审；本任务证明的是位置、来源元数据和完整性，不是准入结论。

# Debug Evidence Contract

- 调试模式: `Optional`
- 回归证据契约: `Optional`
- 本任务不是缺陷修复任务；迁移失败由 catalog、manifest、治理或任务文档校验以非零状态暴露。

# Task Package Context Map

- TP-01：全局 catalog、项目 `skills/README.md`、目标 active manifest 和工作区状态。
- TP-02：原 global upstream 目录、项目 `skills/reference-only/`、source registry 与 manifests。
- TP-03：catalog validator、catalog negative tests、项目 governance strict/health 和摘要证据。
- TP-04：本任务七份文档、`governance/tasks/INDEX.md`、项目拓扑/操作模型/工具链文档。

## TP-01 迁移前置检查与路径契约

- 输入：全局 catalog、项目目录和用户“不进入全局根目录”的约束。
- 输出：来源/目标路径、7 个来源、回滚路径和验证边界。
- 结果：前置条件与不覆盖 active skill 的门禁已固定。

## TP-02 跨仓库目录移动

- 输入：全局 `assets/upstream/`、registry 和 7 份 manifest。
- 输出：项目 `skills/reference-only/` 中按 source-id 隔离的完整参考包。
- 结果：目录及 catalog metadata 已移动，未执行上游内容。

## TP-03 完整性、边界与治理验证

- 输入：迁移后的项目目录和全局轻量 catalog。
- 输出：来源、文件集合、SHA-256、symlink、active 边界和 governance 校验结果。
- 结果：catalog 完整性/负例、governance strict/health 均通过。

## TP-04 文档与状态收口

- 输入：验证结果和项目架构边界。
- 输出：同步后的项目文档、任务索引和合规任务包。
- 结果：任务状态收口为 Done；剩余风险仅为 reference-only 内容未来使用前的独立审计。
