# Acceptance Checklist

# Global Standards
- [x] 证据能力是可组合能力集合，不压成可跳级线性等级
- [x] 已有同义能力优先强化或组合，不复制
- [x] source 事实、derived 组合和运行时策略分离
- [x] 内容保持 experimental/reference_only，结果只由 verifier 裁决

# Task Package Checklists
## TP-01
- 标题: 锁定真实证据与九模型去重关系
- 验收项:
  - [x] 九个案例模型均有 reuse、strengthen 或 add 决策，并绑定真实文件证据
- Verify: 核对验收项: 九个案例模型均有 reuse、strengthen 或 add 决策，并绑定真实文件证据
- Gate: 任务目标与上下文已确认
- 输出物:
  - [x] governance/tasks/0020-integrate-proof-engineering-operators/OPERATOR_CROSSWALK.md
- 标准清单:
  - [x] Verify: 核对验收项: 九个案例模型均有 reuse、strengthen 或 add 决策，并绑定真实文件证据
  - [x] Gate: 任务目标与上下文已确认
  - [x] 完成后更新 `STATUS.md` 的 `Recent Evidence`
  - [x] 交付前完成 REVIEW / SHIP 自检

## TP-02
- 标题: 沉淀算子与组合方法
- 验收项:
  - [x] 417 source、60 derived、477 total 一致，新增条目结构和引用完整
- Verify: 核对验收项: 417 source、60 derived、477 total 一致，新增条目结构和引用完整
- Gate: 前置步骤已完成: crosswalk-proof-models
- 输出物:
  - [x] operators/packs/
  - [x] operators/source-inventory.json
  - [x] operators/catalog.json
  - [x] operators/taxonomy/
- 标准清单:
  - [x] Verify: 核对验收项: 417 source、60 derived、477 total 一致，新增条目结构和引用完整
  - [x] Gate: 前置步骤已完成: crosswalk-proof-models
  - [x] 完成后更新 `STATUS.md` 的 `Recent Evidence`
  - [x] 交付前完成 REVIEW / SHIP 自检

## TP-03
- 标题: 升级自包含 solve Skill
- 验收项:
  - [x] VERSION 为 0.3.0，strict validator 通过，压力场景明确非线性证据能力
- Verify: 核对验收项: VERSION 为 0.3.0，strict validator 通过，压力场景明确非线性证据能力
- Gate: 前置步骤已完成: materialize-proof-operators
- 输出物:
  - [x] skills/solve/
- 标准清单:
  - [x] Verify: 核对验收项: VERSION 为 0.3.0，strict validator 通过，压力场景明确非线性证据能力
  - [x] Gate: 前置步骤已完成: materialize-proof-operators
  - [x] 完成后更新 `STATUS.md` 的 `Recent Evidence`
  - [x] 交付前完成 REVIEW / SHIP 自检

## TP-04
- 标题: 同步 WSL 与 Windows Codex
- 验收项:
  - [x] 三目录 strict PASS 且受管文件 SHA-256 manifest 一致
- Verify: 核对验收项: 三目录 strict PASS 且受管文件 SHA-256 manifest 一致
- Gate: 前置步骤已完成: upgrade-solve-skill
- 输出物:
  - [x] governance/tasks/0020-integrate-proof-engineering-operators/INSTALL_SYNC_RECEIPT.json
- 标准清单:
  - [x] Verify: 核对验收项: 三目录 strict PASS 且受管文件 SHA-256 manifest 一致
  - [x] Gate: 前置步骤已完成: upgrade-solve-skill
  - [x] 完成后更新 `STATUS.md` 的 `Recent Evidence`
  - [x] 交付前完成 REVIEW / SHIP 自检

## TP-05
- 标题: 验证、审查与收口
- 验收项:
  - [ ] required deterministic gates 绑定当前输入和真实产物；独立审查缺失时不伪造 provenance
- Verify: 核对验收项: required deterministic gates 绑定当前输入和真实产物；独立审查缺失时不伪造 provenance
- Gate: 前置步骤已完成: sync-codex-installations
- 输出物:
  - [x] governance/tasks/0020-integrate-proof-engineering-operators/REVIEW.md
  - [x] governance/tasks/0020-integrate-proof-engineering-operators/REUSE_SAMPLING.json
  - [ ] governance/tasks/0020-integrate-proof-engineering-operators/RETROSPECTIVE_HANDOFF.json
- 标准清单:
  - [ ] Verify: 核对验收项: required deterministic gates 绑定当前输入和真实产物；独立审查缺失时不伪造 provenance
  - [x] Gate: 前置步骤已完成: sync-codex-installations
  - [x] 完成后更新 `STATUS.md` 的 `Recent Evidence`
  - [ ] 交付前完成 REVIEW / SHIP 自检
