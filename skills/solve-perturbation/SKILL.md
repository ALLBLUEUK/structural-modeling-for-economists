---
name: solve-perturbation
description: 调用一阶 / 二阶 / 三阶摄动求解 DSGE 模型并保存检查点。当用户说"跑摄动"、"求一阶解"、"算政策矩阵"、"线性化求解"、"stoch_simul"、"BK 条件"时调用。
type: solver
---

# solve-perturbation — 摄动求解

## 触发场景

- "跑一阶摄动"、"算 policy matrix"、"线性化"
- "stoch_simul"、"order=2"、"加二阶修正"
- "BK condition" 报错诊断
- "我要 IRF"（需先解出政策矩阵）

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str | 必须已存在 `model/01_setup/<model>/spec.md` 且通过评审 |
| `language` | enum | `dynare` / `julia` |
| `order` | 1/2/3 | 摄动阶数 |
| `solver` | str? | Dynare 默认 `stoch_simul`；Julia 可选 `RegimeSwitchingPerturbation.jl` 等 |
| `seed` | int? | 默认从 `model/_utils/seed.txt` |

## 前置条件检查

执行前必须确认：

1. `model/01_setup/<model>/spec.md` 存在
2. `model/03_solve/<model>/<model>.mod` 或 `run.jl` 存在
3. `model/02_calibrate/<model>/calibration.csv` 已填实参数（不是占位）
4. `model-reviewer` 评审记录存在（`quality_reports/<model>_review.md`）

任一不满足，停下并报告缺什么。

## 步骤清单

### Step 1. 跑稳态校验

调用 `validate-steady-state` skill，残差容差 `1e-8`。

### Step 2. 配置求解器

- **Dynare**：在 `.mod` 末尾确认 `stoch_simul(order=<order>, irf=40, periods=0);`
- **Julia**：调用对应的 `solve!(model; order=<order>)`

### Step 3. 调用执行 skill

- Dynare → `run-dynare`
- Julia → `run-julia`

### Step 4. 解读输出

- **Blanchard-Kahn**：报告特征值是否满足秩条件。不满足 → `numerics-reviewer`。
- **政策矩阵**：保存到 `output/checkpoints/<model>_policy.json`：
  ```json
  {
    "model": "rbc",
    "order": 1,
    "language": "dynare",
    "version": "Dynare 6.1",
    "seed": 20250613,
    "steady_state": {...},
    "policy_matrix": {...},
    "eigenvalues": [...],
    "bk_pass": true,
    "timestamp": "2026-05-11T15:30:00Z"
  }
  ```
- **二/三阶**：额外保存修正项与展开点。

### Step 5. 写日志

`logs/<model>_perturbation_<timestamp>.log` 包含：
- 运行命令、求解器版本、机器信息
- 稳态值
- 特征值清单
- 警告与错误
- 用时

### Step 6. 更新 session log

## 输出契约

- `output/checkpoints/<model>_policy.json`（必产）
- `logs/<model>_perturbation_<timestamp>.log`（必产）
- 若 `irf` 选项打开：临时 IRF 数据 → 由 `simulate-irf` 接管落盘

## 不允许的操作

- 在 `validate-steady-state` 失败的情况下继续
- 跳过 BK 条件检查
- 把求解器版本号写死在文档但代码用别的版本
- 修改 `spec.md` 中的参数仅为了让模型解出来（必须回到 `setup-dsge` 走流程）

## 常见失败

| 现象 | 原因 / 处理 |
|---|---|
| BK fails (rank deficient) | 状态变量分类错；检查 `var` 与 `predetermined_variables` |
| Steady state not found | 解析稳态错；让 Dynare 自动求或写 `steady_state_model` 块 |
| 二阶修正过大 | 稳态远离非线性中心；考虑投影法 |
| 政策矩阵含 NaN | 参数取值越界（如 `beta>=1`） |
