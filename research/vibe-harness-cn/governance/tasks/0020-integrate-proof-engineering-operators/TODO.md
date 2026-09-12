# Execution Checklist
[x] TP-01 | P0 | 锁定真实证据与九模型去重关系 | Verify: 核对验收项: 九个案例模型均有 reuse、strengthen 或 add 决策，并绑定真实文件证据 | Gate: 任务目标与上下文已确认 | Parallelizable: No
[x] TP-02 | P0 | 沉淀算子与组合方法 | Verify: 核对验收项: 417 source、60 derived、477 total 一致，新增条目结构和引用完整 | Gate: 前置步骤已完成: crosswalk-proof-models | Parallelizable: No
[x] TP-03 | P0 | 升级自包含 solve Skill | Verify: 核对验收项: VERSION 为 0.3.0，strict validator 通过，压力场景明确非线性证据能力 | Gate: 前置步骤已完成: materialize-proof-operators | Parallelizable: No
[x] TP-04 | P0 | 同步 WSL 与 Windows Codex | Verify: 核对验收项: 三目录 strict PASS 且受管文件 SHA-256 manifest 一致 | Gate: 前置步骤已完成: upgrade-solve-skill | Parallelizable: No
[ ] TP-05 | P0 | 验证、审查与收口 | Verify: 核对验收项: required deterministic gates 绑定当前输入和真实产物；独立审查缺失时不伪造 provenance | Gate: 前置步骤已完成: sync-codex-installations | Parallelizable: No

说明：
- 每一行后续必须绑定 `TP-XX(.YY...)`
- 不允许出现无归属 TODO
