# Planning Summary
先锁定真实证据与九模型去重关系，再更新三类 pack 和索引，随后升级 solve Skill、同步双环境，最后完成全量验证与治理收口。
- 编译节点总数: 5
- 叶子执行项: 5
- 执行波次数: 5
- 当前任务必须遵守 `SPEC -> PLAN -> BUILD -> TEST -> REVIEW -> SHIP`

# Lifecycle Gates
- 必须按顺序完成并保留证据，不得跳过任何 required gate。
- SPEC：固定 6 source + 3 derived + 3 strengthen 和非线性证据语义
- PLAN：固定来源、边界、同步方式、停止条件与回滚
- BUILD：只更新既有 JSON/Markdown/Skill
- TEST：运行库、自测、Skill 三份 strict 与摘要一致性
- REVIEW：检查重复、证据跳级、引用、文档漂移和外部安装漂移
- SHIP：绑定当前工作树的新鲜证据；无独立 reviewer 时不伪造其 provenance

# Simplest Path
增强现有 solve Skill 和既有 pack；不新增 Skill、领域、公共 Schema、运行时或同步框架。

# Split Strategy
按证据 crosswalk、内容入库、Skill 升级、双环境同步、验证收口五段串行推进。

# Execution Waves
- Wave 1: TP-01
- Wave 2: TP-02
- Wave 3: TP-03
- Wave 4: TP-04
- Wave 5: TP-05

# Runtime Workflow Contract
- workflow artifact 必须存入任务目录，而不是只留在聊天上下文。
- worker 只能消费当前 packet 的最小上下文、允许工具、禁止动作、证据要求和停止条件。
- verifier / 自审必须独立挑战关键发现，不能把 worker 自评当作验收。
- integrator / closeout 必须报告 verified、rejected、unresolved、failed、not-covered。
- 全局预算: 仅 6 个新增 source、3 个 derived、3 个既有强化
- 全局预算: 仅静态 JSON/Markdown、Skill 内容同步与确定性校验
- 全局预算: 不执行形式证明、模型训练、网络研究或远端写入
- 全局停止条件: 发现候选与既有条目完全同义且无法证明独立语义
- 全局停止条件: 需要改变公共 Core、实现 runtime 或执行数学项目才能表达
- 全局停止条件: 目标 Skill 路径不是用户指定环境或同步将删除额外文件
- 全局停止条件: 需要凭据、远端写入、删除或其他不可逆操作
- 需要审批: 改变公共 Core Schema、运行时权限或外部服务
- 需要审批: 删除目标文件、凭据、远端写入或破坏性操作

# Next Executable Leaves
- TP-01 | Wave 1 | Depends On: 无 | Gate: 任务目标与上下文已确认

# Dependency Graph
TP-01 -> TP-02
TP-02 -> TP-03
TP-03 -> TP-04
TP-04 -> TP-05

# Rollback Protocol
- 恢复 `INDEX.md` 当前任务行
- 恢复本任务目录到初始化状态
- 不得影响其他任务目录
