# Review: 证明工程算子与 solve 0.3.0

## Scope

- `target`: release_gate
- `review_depth`: deep
- `subject`: 九模型 crosswalk、6 个 source、3 个 derived Method、3 个强化条目、477 条 Reference Library、solve 0.3.0 与 WSL/Windows 安装快照
- `base`: `7b3e95c2176affd6999aacbdea9d64f757b32b06`
- `review mode`: 主 Codex 本地自审；不具备外部独立 reviewer provenance

## Verdict

- `local decision`: PASS
- `ship decision`: BLOCKED
- `summary`: 内容、契约、回归和三端安装一致性均通过本地确定性检查；高风险复盘仍缺受信外部 reviewer 签名与 `RETROSPECTIVE_HANDOFF.json`，且本轮未获授权提交 Git，因此不能把工作树结果宣称为正式 closeout、独立审查或已交付 revision。

## Selected Profiles

- architecture、build-release、concurrency、correctness、feature-safety、operability
- ponytail-complexity、reliability、repo-hygiene、security
- 关键词路由产生的 payment / reverse-engineering 信号不适用：本轮没有支付、二进制、协议或动态样本分析。

## Findings

- 已处理：先读取真实 Pi 会话、数学项目案例报告、规范、证明 Skill、Schema 与循环脚本，再形成九模型逐项 `reuse / strengthen / add` crosswalk。
- 已处理：没有逐字复制九个模型；新增 6 个独立原子 source、组合 3 个 derived Method，并强化 3 个已有条目。
- 已处理：首次宽范围 JSON 补丁误改无关 pack 数量，被全库 validator 阻断；改为按 domain 身份核对后恢复。
- 已处理：首轮 behavior/test 暴露旧总数 `468` 被测试、运行记录样例和活跃 QA 写死；测试现从 catalog 动态派生总数，相关当前消费者更新为 `477`，原样回归通过。
- 未发现：公共 Core Schema、selector、planner、Binding、权限或 runtime 行为没有改变。
- 未发现：数学项目没有被修改或执行；静态源码证据仍只支持 `source_locked / needs-replay`，不支持 fresh build、kernel replay 或人类语义确认。

## Evidence

- Reference Library：`417/417 source + 60/60 derived = 477`，全库 validator 与负例 self-test PASS。
- 项目门禁：architecture、behavior、contract、test 均 PASS。
- Skill：项目、WSL、Windows 三目录 strict PASS；各 71 个文件，聚合 SHA-256 均为 `5049a0f821d553a3dbdc57138215c32cc35cfbee1601ed6be82938cfd47bc980`，递归 diff 为空。
- 同步方式：`rsync -a --checksum`，未使用 `--delete`，未删除目标目录额外文件。
- Audit-case 与 reuse sampling 的 owner validator 均 PASS；复盘 record 本地严格校验 PASS，但独立签名门禁未满足。
- 任务级 verification 已生成并重跑 required gates；owner strict 因存在 uncommitted non-evidence paths 判定 `BLOCK`，未被降级或绕过。

## Security And Reliability

- 未读取凭据、未执行远端写入、未部署、未运行上游代码，也未执行破坏性 Git 操作。
- 算子只提供候选方法；权限由 Harness policy、结果由 verifier 裁决，Skill 不得自授权或把源码检查升级成更强证据。
- 安装目录是发布副本，项目 `skills/solve/` 是待纳入版本控制的源快照；本轮没有自动提交或推送。

## Efficiency And Cost

- 全库校验时间复杂度 `O(F + E + R)`、空间复杂度 `O(E + R)`；当前 `F=56`、`E=477`，增加 9 个条目不是性能热点。
- Skill 按 taxonomy 和候选 pack 延迟加载，不把 477 条内容全部塞入上下文；运行选择成本主要取决于候选数，而非全库规模。
- 立即值得保留：单一 catalog 派生数量、精确引用/计数验证和按需加载。
- 需要数据后再做：10x/100x 规模的索引、缓存或数据库；当前引入只会增加所有权面，暂不优化。

## Document Drift

- 已同步根 README/AGENTS、operators/docs、项目操作模型、拓扑、工具链、上下文路由、operators/skills module context、运行样例和活跃 QA。
- 历史研究报告、ADR、旧任务与根 AGENTS 的变更历史保留当时 `468` 快照，不把历史事实改成当前值。

## Remaining Blockers

- 高风险 `auto-retro` 要求受信外部 reviewer 对固定 sealed digest 签名；主 Codex 不能自签，故不生成伪造的 `RETROSPECTIVE_HANDOFF.json`。
- 工作树包含并行 AI 改动且用户未要求 Git commit；没有 clean review HEAD、commit、push、PR 或 CI provenance。

## Rollback

- 通过后续反向提交撤销本轮算子、文档、Skill 源快照和安装副本；不使用 reset、checkout、clean 或覆盖其他 AI 改动。
