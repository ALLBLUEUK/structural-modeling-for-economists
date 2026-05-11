---
name: setup-ha-bewley
description: 写或扩展异质主体（Aiyagari / Bewley / Krusell-Smith）模型的设定与 Julia 脚手架。当用户说"建一个异质主体模型"、"Aiyagari"、"Bewley"、"sequence-space"、"不完全市场"时调用。
type: setup
---

# setup-ha-bewley — 异质主体模型设定与 Julia 脚手架

## 触发场景

- "建一个 Aiyagari 模型研究 [财富不平等 / 消费保险 / 货币政策传导]"
- "写 Bewley / Krusell-Smith 模型"
- "做 HA-DSGE（用 sequence-space jacobian）"
- "研究异质性下的某个 aggregate shock 的 IRF"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str | 如 `aiyagari_baseline`、`hank_simple` |
| `idiosyncratic_shock` | str | 个体不确定性来源（劳动效率、健康、…） |
| `aggregate_shock` | str? | 可选：总量冲击（货币政策、TFP） |
| `solver` | enum | `egm` / `vfi` / `ssj` |

## 步骤清单

1. 读 `templates/master-ha-template.jl` 与 `templates/model-spec-template.md`。
2. 写 `spec.md`：偏好、预算约束、个体过程的转移矩阵、资产网格、市场出清条件。
3. 维度自检：状态空间维数 = (资产网格大小) × (收入状态数)；总量出清方程数。
4. 提交 `model-reviewer` + `math-reviewer`。
5. 通过后：复制 `templates/master-ha-template.jl` 为 `model/03_solve/<model>/run.jl`。
6. 若是 HA-DSGE，添加 sequence-space jacobian 计算（`SequenceJacobian.jl`）。
7. 生成 `equations.tex`。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `model/01_setup/<model>/spec.md` | ✅ |  |
| `model/01_setup/<model>/equations.tex` | ✅ |  |
| `model/03_solve/<model>/run.jl` | ✅ | Julia 脚手架 |

## 不允许的操作

- 把资产网格上界设得截尾（用 `model-reviewer` 检查）
- 跳过个体策略函数收敛诊断
- 在 sequence-space 上不做雅可比缓存而每次重算

## 失败回退

| 症状 | 处理 |
|---|---|
| 必备前置未满足 | 报错并指出缺什么；不绕过 |
| 上游产物 stale | 重跑上游 skill；不"凭旧的 checkpoint 继续" |
| 用户口径模糊 | 调用 `interview-me` skill 反向访谈 |
