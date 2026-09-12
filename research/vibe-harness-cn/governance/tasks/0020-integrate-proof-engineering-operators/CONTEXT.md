# Repo Evidence
- operators/catalog.json 当前登记 56 个 pack、411 个 source、57 个 derived
- operators/source-inventory.json 是 source 覆盖单一真相源
- skills/solve 是现有自包含 Skill，VERSION 当前为 0.2.0
- WSL 与 Windows 的目标 solve 目录均已存在
- vibe-mathing-cn-internal 已有 ProblemContract、Result、checkpoint、failed-route 和形式证明 Skill

# Constraints Matrix
- 不修改或执行数学项目与上游形式证明代码
- 公共 Core 保持宽松，内容保持 reference_only
- 同步不得使用删除目标额外文件的方式
- 不读取凭据，不执行破坏性 Git 操作，不覆盖无关并行改动

# Change Boundary
- operators/packs/problem-solving-methodology.json、formal-logic-automated-reasoning.json、information-knowledge-science.json
- operators/source-inventory.json、operators/catalog.json、operators/taxonomy/、operators 文档
- skills/solve/、项目入口文档、governance/tasks/0020 与相关 module context
- <codex-home>/skills/solve/ 与 <windows-codex-home>/skills/solve/
- 不修改 contracts/、research/upstreams.*、research/upstreams/ 或 vibe-mathing-cn-internal

# Risk Matrix
- 把案例九模型机械建成九个 source 会制造语义重复
- 把 source_locked、build、kernel 和语义审查写成单一阶梯会允许错误跳级
- 静态扫描中的占位符若不做可达性分析，会产生误拒绝或虚假通过
- 同步外部 Skill 目录后若不做摘要比对，可能出现环境漂移
- 不把案例自报或静态扫描写成已完成 kernel/语义验证

# Assumptions and Falsification
- 用户明确授权覆盖两个目标目录中与项目 solve Skill 同名的文件
- 目标目录的额外文件保留，源 Skill 是共享核心内容的真相源
- 本轮新增静态方法，不代表 Agent 效果已经通过真实任务评测

# Critical Ambiguities
- 当前未记录会改变实现路径的关键歧义；若发现此类歧义，必须暂停并回到需求澄清

# Debug Evidence Contract
- 调试模式: Optional
- 回归证据契约: Optional
- 若任务属于 bugfix / regression / flaky / crash / CI-only failure，必须切到 `Required`
- 调试模式为 `Required` 时必须在当前任务目录创建并维护 `DEBUG.md`
- 回归证据契约为 `Required` 时，closeout 必须由 `auto-debug` 校验 `REGRESSION_EVIDENCE.json` 的 RED/GREEN/反事实证据

# Task Package Context Map
## TP-01
- Step Key: `crosswalk-proof-models`
- 标题: 锁定真实证据与九模型去重关系
- 类型: `action`
- 目标: 把 Pi 会话、案例报告、数学项目契约和现有算子映射为可审计 crosswalk
- 父节点: `ROOT`
- 子节点: 无
- 依赖步骤 Key: 无
- 依赖节点 ID: 无
- 输入: 无
- 输出: governance/tasks/0020-integrate-proof-engineering-operators/OPERATOR_CROSSWALK.md
- 允许工具: 默认遵循当前环境与任务范围
- 禁止动作: 无未声明授权的高风险动作
- 证据要求: 命令输出、文件 diff、日志或审查结论
- 停止条件: 越界、缺审批、验证失败或上下文不足时暂停
- 风险: 不把案例自报或静态扫描写成已完成 kernel/语义验证
- 备注: 无

## TP-02
- Step Key: `materialize-proof-operators`
- 标题: 沉淀算子与组合方法
- 类型: `action`
- 目标: 将 6 个独立 source、3 个 derived 和 3 个强化点写入既有 Reference Library
- 父节点: `ROOT`
- 子节点: 无
- 依赖步骤 Key: crosswalk-proof-models
- 依赖节点 ID: TP-01
- 输入: governance/tasks/0020-integrate-proof-engineering-operators/OPERATOR_CROSSWALK.md；operators/catalog.json
- 输出: operators/packs/；operators/source-inventory.json；operators/catalog.json；operators/taxonomy/
- 允许工具: 默认遵循当前环境与任务范围
- 禁止动作: 无未声明授权的高风险动作
- 证据要求: 命令输出、文件 diff、日志或审查结论
- 停止条件: 越界、缺审批、验证失败或上下文不足时暂停
- 风险: 无
- 备注: 无

## TP-03
- Step Key: `upgrade-solve-skill`
- 标题: 升级自包含 solve Skill
- 类型: `action`
- 目标: 刷新内嵌 Reference Library、版本、变更日志、选择说明和真实证明工程压力场景
- 父节点: `ROOT`
- 子节点: 无
- 依赖步骤 Key: materialize-proof-operators
- 依赖节点 ID: TP-02
- 输入: operators/；skills/solve/SKILL.md
- 输出: skills/solve/
- 允许工具: 默认遵循当前环境与任务范围
- 禁止动作: 无未声明授权的高风险动作
- 证据要求: 命令输出、文件 diff、日志或审查结论
- 停止条件: 越界、缺审批、验证失败或上下文不足时暂停
- 风险: 无
- 备注: 无

## TP-04
- Step Key: `sync-codex-installations`
- 标题: 同步 WSL 与 Windows Codex
- 类型: `action`
- 目标: 不删除额外文件地更新两个 solve 安装目录，并形成三份内容一致性回执
- 父节点: `ROOT`
- 子节点: 无
- 依赖步骤 Key: upgrade-solve-skill
- 依赖节点 ID: TP-03
- 输入: skills/solve/
- 输出: governance/tasks/0020-integrate-proof-engineering-operators/INSTALL_SYNC_RECEIPT.json
- 允许工具: 默认遵循当前环境与任务范围
- 禁止动作: 无未声明授权的高风险动作
- 证据要求: 命令输出、文件 diff、日志或审查结论
- 停止条件: 越界、缺审批、验证失败或上下文不足时暂停
- 风险: 无
- 备注: 无

## TP-05
- Step Key: `verify-review-closeout`
- 标题: 验证、审查与收口
- 类型: `action`
- 目标: 同步文档与治理真相，运行全量门禁并记录 review、reuse 和 retro 结果
- 父节点: `ROOT`
- 子节点: 无
- 依赖步骤 Key: sync-codex-installations
- 依赖节点 ID: TP-04
- 输入: 无
- 输出: governance/tasks/0020-integrate-proof-engineering-operators/REVIEW.md；governance/tasks/0020-integrate-proof-engineering-operators/REUSE_SAMPLING.json；governance/tasks/0020-integrate-proof-engineering-operators/RETROSPECTIVE_HANDOFF.json
- 允许工具: 默认遵循当前环境与任务范围
- 禁止动作: 无未声明授权的高风险动作
- 证据要求: 命令输出、文件 diff、日志或审查结论
- 停止条件: 越界、缺审批、验证失败或上下文不足时暂停
- 风险: 无
- 备注: 无
