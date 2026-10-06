---
name: setup-ha-bewley
description: 写或扩展异质主体（Aiyagari / Bewley / Krusell-Smith）模型的设定，并提供可直接运行的 Python 稳态求解模板（v0.3）与 Julia 脚手架。当用户说"建一个异质主体模型"、"Aiyagari"、"Bewley"、"sequence-space"、"不完全市场"时调用。
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

## v0.3 新增：Python 稳态求解路径（推荐研究生先用）

`templates/master-ha-template.py` 是可直接运行的 Aiyagari / Bewley 稳态求解器，无需 Julia 环境。

1. spec 通过 `model-reviewer` 与 `math-reviewer` 后，复制模板到 `model/03_solve/<model>/solve.py`，把 `MODEL_NAME` 改为模型名。
2. 在 `model/02_calibrate/<model>/calibration.csv` 中至少给出：`beta, mu, alpha, delta, rho, sigma, n_z, n_a, a_max, b`；可选 `use_rouwenhorst`（默认 1）、`m`（Tauchen 宽度）、`tol_ss`（默认 1e-6，建议 1e-8）。
3. 运行：`python model/03_solve/<model>/solve.py --scenario baseline`；比较静态：`--scenario b2 --set b=2`。拼错的参数名会直接报错。
4. 读检查点 `output/checkpoints/<model>_<scenario>_ss.json`：`validated` 为 true 才能进入表格与报告。它同时要求出清与资源约束残差、分布与 EGM 收敛、网格上端质量 < 1e-8、唯一性扫描单次穿越、离散化质量（方差相对误差 < 5%、自相关误差 < 0.01）。
5. 必做的极限检验：取 `--set sigma=0.001 --set r_hi_eps=1e-8`，利率应回到 1/β − 1、储蓄率应回到完全市场基准。
6. 求解后调用 `numerics-reviewer`；对外报告前用 `scripts/replicate_compare.py` 与 `scripts/check_claims.py`（见 `replicate`）。

验收案例：`结项/工作流验收/case_ha_aiyagari_borrowing/`（借贷限额的比较静态）。
