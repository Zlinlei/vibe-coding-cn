---
id: CTX-SKILLS
type: module-context
status: current
owner: engineering
created: 2026-09-04
last_reviewed: 2026-09-04
code_path: skills
---

# AI Skill 发布层 Context

## 代码路径

`skills/`，当前唯一包为 `skills/solve/`。

## 模块职责

- 提供可安装、自包含的 AI Skill 说明和问题求解算子参考快照。
- 用 `SKILL.md` 定义触发、边界、按需加载和最小调用结果；用 `references/` 携带 catalog、taxonomy、
  schema、source inventory 和 56 个 pack。
- 让不同 Harness 能在不依赖本仓库运行时的情况下消费同一份已校验内容。

## 非职责

- 不编辑或取代 `operators/`，不拥有内容真相源。
- 不实现 selector、planner、Binding、模型/工具执行、权限、业务会话、结果裁决或在线 registry。
- 不把 `experimental` 参考条目包装成 verified 能力，不保存凭据或敏感运行数据。

## 单一真相源与发布关系

- 内容真相源：`operators/catalog.json`、`operators/source-inventory.json`、`operators/taxonomy/`、
  `operators/packs/`。
- 结构真相源：`contracts/problem-solving-operator-pack.schema.json`；Skill 内 schema 是发布副本。
- 发布包：`skills/solve/references/`，catalog 的路径相对于该目录，安装后可以脱离仓库使用。
- 包版本：`skills/solve/VERSION`；变更记录：`skills/solve/CHANGELOG.md`。

## 不变量

- Skill frontmatter 的 `name` 必须是 `solve`，且与目录名一致。
- `references/` 中有 56 个 pack，包内 operator-library 校验必须保持 `417/417`、`60/60`、`477`。
- 所有引用路径必须在安装包内解析；内容刷新不得只修改单个副本。
- Skill strict 校验和包内 library 校验均通过后，才能把包称为可分发快照。

## 常用验证

```bash
bash <codex-home>/skills/workflow/modules/skill-authoring/scripts/validate-skill.sh skills/solve --strict
uv run --locked --script scripts/validate_harness.py --operator-library skills/solve/references/catalog.json
```

## Agent Rules

- 先校验 `operators/`，再刷新 `skills/solve/references/`；禁止在发布副本中手工修条目。
- 不要把全部 pack 默认加载到模型上下文；先读 catalog/taxonomy，按问题选择少量内容。
- 形式证明等多门验收按 required capability set 逐项裁决，禁止 source/build/kernel/semantic 自动跳级。
- 结构变更必须同步更新 `skills/AGENTS.md`、`skills/solve/AGENTS.md`、根 README、拓扑和本 module context。
