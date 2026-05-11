# Orchestrator Protocol — 任务编排协议

本协议规范 agent 在面对结构建模任务时的高层调度行为。

## 入口判断

任何用户请求进入项目时，agent 按以下顺序执行：

1. 读 `AGENTS.md`
2. 读 `MEMORY.md`
3. 读 `.claude/skills/strucmod/SKILL.md`
4. 根据用户请求关键字与产物形态，定位入口 skill（见父技能的"入口决策树"）

## 调用顺序

调用任意 solve / simulate / counterfactual 系列 skill 之前，必须确认：

- `spec.md` 存在 ✅
- `model-reviewer` 评审通过 ✅
- `calibration.csv` 含实参 ✅
- `validate-steady-state` 通过 ✅

**任何一项不满足，立即停下并向用户报告缺什么。** 不要私自补全。

## 必经子 agent

以下场景必须调用对应子 agent，不可省略：

| 阶段 | 子 agent | 触发 |
|---|---|---|
| spec 完成 | `model-reviewer` | 经济逻辑评议 |
| 方程落入代码前 | `math-reviewer` | 维度一致 |
| 求解后 | `numerics-reviewer` | 数值稳定 |
| 报告前 | `verifier` | 复现核对 |

## 工具与产物分离

- agent 不直接写 LaTeX 论文文本到 `reports/`，必须先产出 `output/latex/<model>/*.tex` 片段，再由 `render-report` skill 拼装。
- agent 不直接动 `data/raw/`、`data/derived/`，仅调用 `data/calibration/<model>/manifest.json` 中登记的派生数据。
- 任何对外数字必须经过 `verifier`，否则只能写为 "preliminary, not verified"。

## 失败传播

- 子 skill 失败 → 父 skill 立即停止，不继续后续步骤。
- 写入 `quality_reports/<model>_<step>_<timestamp>.md`。
- 向用户出具失败位置与下一步建议。

## 用户中断

- 用户随时可以打断流水线，agent 应保留已生成的中间产物（特别是 checkpoint）。
- 重启时通过 `run-pipeline` 的 `mode=from_<step>` 跳过已完成步骤。

## 记忆

- 跨会话信息走 `MEMORY.md`（项目根目录）。如果记忆条目较多，可在 `MEMORY.md` 同目录新建分文件并在 `MEMORY.md` 中索引；本仓库不预置 `.claude/memory/` 目录，以保持 `.claude/` 仅承载流水线本身。
- 项目级常识写入 `master_supporting_docs/`。
