---
name: validate-steady-state
description: 数值化校验稳态：把稳态向量代入方程系统，残差应小于 tol。任何 IRF / 反事实 / 福利分析之前必须通过本技能。当用户说"稳态求不出来"、"为什么不收敛"、"算稳态残差"时调用，且作为 solve-* 系列的强制前置。
type: validator
---

# validate-steady-state — 稳态数值校验

## 触发场景

- "稳态求不出来"、"看看稳态对不对"、"为什么 Dynare 报 not in steady state"
- 任何 `solve-perturbation` / `solve-vfi` / `simulate-irf` / `counterfactual-run` 之前

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str | 已设定的模型 |
| `ss_source` | path | 稳态向量文件，默认 `output/checkpoints/<model>_ss.json` |
| `tol` | float | 默认 `1e-8` |

## 步骤清单

### Step 1. 加载稳态向量与方程系统

- 稳态：`output/checkpoints/<model>_ss.json`
- 方程：从 `model/01_setup/<model>/equations.tex` 或 `<model>.mod` 的 `model;` 块解析
- 参数：`model/02_calibrate/<model>/calibration.csv`

### Step 2. 逐方程代入

对每个方程 `f_i(x_ss, params) = 0`，计算 `r_i = |f_i|`，列表展示前 10 大残差。

### Step 3. 报告

写 `quality_reports/<model>_ss_<timestamp>.md`：

```markdown
# 稳态残差报告 · <model> · <timestamp>

- 总方程数：N
- 容差：1e-8
- 通过：YES / NO
- 残差最大方程：
  1. eq_<idx>: r = 1.2e-7  (方程含义：……)
  2. ...
```

### Step 4. 决策

- 全部 < tol → 通过，返回上层 skill。
- 有方程 ≥ tol → **停止**。把残差报告与原方程一起交给 `math-reviewer` 子 agent。

## 输出契约

- `quality_reports/<model>_ss_<timestamp>.md`（必产）
- 通过时：在 `output/checkpoints/<model>_ss.json` 中追加字段 `validated: true, validated_at: <timestamp>`

## 不允许

- 提高容差仅为了让模型"通过"。容差只能由项目协议（`AGENTS.md`）调整。
- 跳过本技能直接进入仿真。
- 把残差报告改成事后追溯的形式。

## 实现参考

完整 Python 实现见 `scripts/check_steady_state.py`，本技能负责调用该脚本并解读输出。
