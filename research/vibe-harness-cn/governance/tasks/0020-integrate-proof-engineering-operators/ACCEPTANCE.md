# Task-Level Acceptance
- 九模型均有 reuse/strengthen/add 决策
- 417 source、60 derived、477 total 通过 Reference Profile
- solve 0.3.0 在形式证明场景中按证据能力选择算子且不跳级
- 三份 Skill 严格校验通过且核心内容摘要一致
- 公共 Core 和运行时边界不变
- approved plan 已成功编译为递归任务树
- 叶子节点数量: 5
- 当前可立即执行叶子节点: TP-01

# Validation Plan
- uv run --locked --script scripts/validate_harness.py --operator-library operators/catalog.json
- uv run --locked --script scripts/validate_harness.py --self-test
- bash <codex-home>/skills/workflow/modules/skill-authoring/scripts/validate-skill.sh <solve-dir> --strict
- python3 scripts/verify_project.py --gate architecture/behavior/contract/test
- 治理 strict、health、principle、task docs、reuse、retro 和任务级 verification
- TP-01 | Verify: 核对验收项: 九个案例模型均有 reuse、strengthen 或 add 决策，并绑定真实文件证据 | Gate: 任务目标与上下文已确认
- TP-02 | Verify: 核对验收项: 417 source、60 derived、477 total 一致，新增条目结构和引用完整 | Gate: 前置步骤已完成: crosswalk-proof-models
- TP-03 | Verify: 核对验收项: VERSION 为 0.3.0，strict validator 通过，压力场景明确非线性证据能力 | Gate: 前置步骤已完成: materialize-proof-operators
- TP-04 | Verify: 核对验收项: 三目录 strict PASS 且受管文件 SHA-256 manifest 一致 | Gate: 前置步骤已完成: upgrade-solve-skill
- TP-05 | Verify: 核对验收项: required deterministic gates 绑定当前输入和真实产物；独立审查缺失时不伪造 provenance | Gate: 前置步骤已完成: sync-codex-installations

# Review Gate
- 九模型 crosswalk 无遗漏且 6+3 划分合理
- source key、ID、引用、计数、taxonomy 和 Method 图一致
- 压力场景能拒绝仅凭源码扫描宣称 kernel/语义通过
- 三份 Skill 的受管核心文件摘要一致且额外文件未被删除

# Runtime Verification Gate
- [x] 每个 tool/action 结果都有可回指证据或明确未执行原因。
- [x] 高风险动作没有由 worker/agent 自我批准；审批状态可追踪。
- [x] compaction / resume 后目标、计划、修改文件、审批状态和验证项未丢失。
- [x] verifier / 自审已检查关键发现是否有证据支持。
- [x] closeout 明确 coverage gaps、failed packets 和 unresolved questions。
- [x] TP-01: 输出格式 `按 outputs/acceptance 汇报`；证据要求：默认可复核证据
- [x] TP-02: 输出格式 `按 outputs/acceptance 汇报`；证据要求：默认可复核证据
- [x] TP-03: 输出格式 `按 outputs/acceptance 汇报`；证据要求：默认可复核证据
- [x] TP-04: 输出格式 `按 outputs/acceptance 汇报`；证据要求：默认可复核证据
- [ ] TP-05: 输出格式 `按 outputs/acceptance 汇报`；证据要求：默认可复核证据

# Ship Readiness
- Reference Library validator、self-test 与 solve strict PASS
- architecture、behavior、contract、test gates PASS
- 治理 strict/health/principle、task docs、reuse、retro 和 verification 校验通过
- 同步回执记录路径、版本、校验和与验证结果

# Task Package Acceptance
## TP-01
- 标题: 锁定真实证据与九模型去重关系
- 验收标准:
  - 九个案例模型均有 reuse、strengthen 或 add 决策，并绑定真实文件证据
- Verify: 核对验收项: 九个案例模型均有 reuse、strengthen 或 add 决策，并绑定真实文件证据
- Gate: 任务目标与上下文已确认
- 输出物: governance/tasks/0020-integrate-proof-engineering-operators/OPERATOR_CROSSWALK.md

## TP-02
- 标题: 沉淀算子与组合方法
- 验收标准:
  - 417 source、60 derived、477 total 一致，新增条目结构和引用完整
- Verify: 核对验收项: 417 source、60 derived、477 total 一致，新增条目结构和引用完整
- Gate: 前置步骤已完成: crosswalk-proof-models
- 输出物: operators/packs/；operators/source-inventory.json；operators/catalog.json；operators/taxonomy/

## TP-03
- 标题: 升级自包含 solve Skill
- 验收标准:
  - VERSION 为 0.3.0，strict validator 通过，压力场景明确非线性证据能力
- Verify: 核对验收项: VERSION 为 0.3.0，strict validator 通过，压力场景明确非线性证据能力
- Gate: 前置步骤已完成: materialize-proof-operators
- 输出物: skills/solve/

## TP-04
- 标题: 同步 WSL 与 Windows Codex
- 验收标准:
  - 三目录 strict PASS 且受管文件 SHA-256 manifest 一致
- Verify: 核对验收项: 三目录 strict PASS 且受管文件 SHA-256 manifest 一致
- Gate: 前置步骤已完成: upgrade-solve-skill
- 输出物: governance/tasks/0020-integrate-proof-engineering-operators/INSTALL_SYNC_RECEIPT.json

## TP-05
- 标题: 验证、审查与收口
- 验收标准:
  - required deterministic gates 绑定当前输入和真实产物；独立审查缺失时不伪造 provenance
- Verify: 核对验收项: required deterministic gates 绑定当前输入和真实产物；独立审查缺失时不伪造 provenance
- Gate: 前置步骤已完成: sync-codex-installations
- 输出物: governance/tasks/0020-integrate-proof-engineering-operators/REVIEW.md；governance/tasks/0020-integrate-proof-engineering-operators/REUSE_SAMPLING.json；governance/tasks/0020-integrate-proof-engineering-operators/RETROSPECTIVE_HANDOFF.json

# Anti-Goals
- 不得修改或执行 `vibe-mathing-cn-internal`，不得把静态审计冒充 fresh build、kernel replay 或人类语义确认
- 不得改变公共 Core Schema、权限模型、selector、planner、Binding 或 runtime
- 不得删除或重建 WSL/Windows Codex 中的其他 Skill；同步只覆盖 `solve/` 同名文件且不使用 `--delete`
- 不得虚构证据、读取凭据、执行破坏性 Git 操作或覆盖其他 AI 的无关改动
