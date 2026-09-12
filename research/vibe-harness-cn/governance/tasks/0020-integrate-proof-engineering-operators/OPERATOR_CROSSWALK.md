# 形式证明工程模型到通用算子的 Crosswalk

## 证据边界

- Pi 会话：`<pi-session-root>/--home-lenovo-.projects-vibe-mathing-cn-internal--/2026-09-05T04-19-45-216Z_01a06fcb-3bc0-70f8-b73c-a5509fe9a553.jsonl`，会话 `01a06fcb-3bc0-70f8-b73c-a5509fe9a553`。
- 案例报告：`<vibe-mathing-project-root>/governance/tasks/0002-survey-vibe-mathing-practices/CASE_FLT_ANTHROPIC_PROVE2ME_2026-09-04.md`。
- 项目规范：`<vibe-mathing-project-root>/governance/standards/VIBE-MATHING-SPEC-v0.2.md`。
- 证明 Skill：`<vibe-mathing-project-root>/.codex/skills/math-proof/SKILL.md` 与 `.codex/skills/math-formalization/SKILL.md`。
- 运行契约：数学项目中的 ProblemContract、Result、checkpoint、failed-route Schema，以及 `scripts/persistent_research_loop.py`、`scripts/validate_research_spaces.py`。

本轮只读取这些材料，不修改或执行数学项目。案例目前只支持 `source_locked / needs-replay`：静态审计不能冒充 fresh build、kernel replay 或人类语义确认。

## 九模型逐项决策

| 案例模型 | 决策 | 对应算子或方法 | 去重理由 |
|---|---|---|---|
| 合同模型 | `reuse + add` | `task-framing`、`formal-problem-specification`、新增 `claim-candidate-result-separation` | 现有条目能冻结目标，新条目只补“声明、候选、已接纳结果不可互相覆盖”的对象边界。 |
| 地图模型 | `strengthen` | `proof-state-subgoal-decomposition` | 已有子目标分解；补稳定 obligation ID、DAG、状态与闭合规则，不另造 theorem-DAG 算子。 |
| 接口模型 | `add` | `claim-candidate-result-separation` | 与合同模型共享同一个最小独立语义，因此不重复建“statement/proof/result interface”。 |
| 闸门模型 | `add` | `evidence-capability-admission` | 证据是可组合能力集合/偏序，不建允许跳级的单一线性阶梯。 |
| 双审计模型 | `derived` | `machine-semantic-dual-audit` | 它组合陈述身份、强度、占位可达性、kernel 证据与人类语义确认，不是一次原子动作。 |
| 小步模型 | `derived` | `bounded-obligation-loop` | 它组合有界义务、检查点、进展判断、接纳和失败记录，不复制增量开发或 resource-bounded loop。 |
| 失败记忆模型 | `add` | `failed-route-memory` | 现有 backtracking 会换路，但没有把失败条件、首个阻塞点与重试谓词沉淀为追加式资产。 |
| 导航审计模型 | `derived` | `route-first-artifact-audit` | 它组合路线图、依赖路径、关键节点抽样、正式 artifact 与证据接纳，是审计方法而非新存储对象。 |
| 来源链模型 | `strengthen` | `source-authority-and-provenance` | 现有 provenance 已覆盖来源和派生；只补原创、改编、导入、模型生成角色及许可/版本边界。 |

## 从真实契约抽出的六个原子缺口

| 新条目 | 类型 | 独立语义 | 主要证据 |
|---|---|---|---|
| `claim-candidate-result-separation` | `MentalModelSpec` | 防止候选证明覆盖问题声明，防止未验证候选冒充结果。 | ProblemContract/Result 分离与 statement faithfulness。 |
| `evidence-capability-admission` | `OperatorSpec` | 对某个主张声明所需证据能力集合，只接纳真实具备的能力，不允许从源码锁定推到 kernel/语义通过。 | Result evidence capability set 与案例 `needs-replay` 状态。 |
| `failed-route-memory` | `OperatorSpec` | 追加记录失败路线、适用输入、首个阻塞点、已排除假设和重试条件。 | failed-route Schema 与 persistent checkpoint 规则。 |
| `statement-identity-audit` | `OperatorSpec` | 比对定义域、量词、假设、目标和规范化摘要，证明检查的是同一个陈述。 | ProblemContract、statement hash/faithfulness 检查。 |
| `exact-strength-audit` | `OperatorSpec` | 检查候选结果是否通过增加假设、缩小定义域或弱化结论偷换题目。 | exact-strength/semantic audit 规则。 |
| `placeholder-reachability-audit` | `OperatorSpec` | 先定位占位符，再判断它是否从目标 artifact 可达；测试夹具中的占位符不能直接污染正式结果。 | Challenge fixture 与正式源码边界、占位扫描及依赖检查。 |

## 三个组合方法

| 新方法 | 组合内容 | 停止条件 |
|---|---|---|
| `bounded-obligation-loop` | 对象分离 → 稳定义务/DAG → 有界执行 → 实质进展监控 → 证据接纳/失败路线记录 | 义务被接纳、遇到首个未满足门、预算到期或重复无进展。 |
| `machine-semantic-dual-audit` | 陈述身份 → 精确强度 → 占位可达性 → 形式证据 → 人类语义审查 | 任一 required capability 缺失即停止并报告缺口，不向上伪升级。 |
| `route-first-artifact-audit` | 来源/路线索引 → 依赖主路 → 关键节点抽样 → 正式 artifact 核查 → 证据接纳 | 路线与 artifact 无法对应、关键依赖不可访问或样本不足。 |

## 不新增的近义项

- “proof contract”复用 `task-framing`、`formal-problem-specification` 和新增对象分离模型。
- “theorem DAG”强化 `proof-state-subgoal-decomposition`，不另建图管理算子。
- “checkpoint”由 `bounded-obligation-loop` 组合既有资源预算和元认知监控，不另建 checkpoint 算子。
- “human review”复用现有 review/verification 语义；新 Method 只规定机器证据与语义判断不能互相冒充。
- “source locked / build / kernel / semantic”不建单一证据阶梯；统一由 `evidence-capability-admission` 对 required capability set 做接纳。

## 迁移限制

- 这些条目描述通用问题求解程序，不携带 FLT 定理、Lean 代码或项目私有状态。
- `experimental/reference_only` 只代表可检索方法，不代表真实 Agent 效果、形式证明正确或专业结论成立。
- 外部工具执行、权限、事实采集和最终 verdict 继续由宿主 Harness 与 verifier 负责。
