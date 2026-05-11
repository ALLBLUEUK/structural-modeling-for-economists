---
name: calibrate-from-moments
description: 从数据/文献/矩条件组装 calibration.csv，记录每个参数来源。当用户说"校准参数"、"calibrate"、"匹配矩"、"match moments"、"对齐数据"、"找出 beta / alpha 取多少"时调用。本技能是任何 solve-* 系列的强制前置。
type: calibrate
---

# calibrate-from-moments — 校准参数与目标矩匹配

## 触发场景

- "把这个模型校准到中国 2010-2020 数据"
- "alpha 取多少？数据里 K/Y 应该是 2.5"
- "match steady-state moments"
- "我想用 SMM / GMM 校准"
- 任何在 `solve-*` 之前需要确定参数取值的场景

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str | 必须已存在 `model/01_setup/<model>/spec.md` 且通过 `model-reviewer` |
| `target_moments` | list[dict] | 来自 `spec.md` §9.1 的稳态矩列表 |
| `data_sources` | list[path] | 实测数据路径，**仅** `data/calibration/<model>/manifest.json` 中登记过的 |
| `strategy` | enum | `closed-form` / `iterative` / `SMM` / `GMM` / `bayesian` |

## 前置条件

- [ ] `model/01_setup/<model>/spec.md` 存在并通过 `model-reviewer` 评审
- [ ] `data/calibration/<model>/manifest.json` 中登记了所需数据
- [ ] `spec.md` §7 参数表中每个参数都有"来源 / 识别"字段（不能空白）

任一不满足，停下并指明缺什么。

## 步骤清单

### Step 1. 拆分参数

把 `spec.md` §7 的参数表按 **来源类型** 分组：

| 组 | 来源 | 校准方式 |
|---|---|---|
| A. 文献直接采纳 | 引用论文给值 | 复制 + 注引用 |
| B. 数据直接计算 | 国民账户 / 微观调查 | 直接由数据算 |
| C. 稳态矩匹配 | 模型稳态需匹配某矩 | 求解非线性方程 |
| D. 待估 | SMM / GMM / 极大似然 | 调用估计程序 |

A、B 组直接落值；C 组进入 Step 2；D 组进入 Step 3。

### Step 2. 稳态矩匹配（C 组）

对每个目标矩 `m_data`，写出模型隐含矩 `m_model(theta)` 关于参数子集 `theta` 的函数。

求解 `m_model(theta) - m_data = 0`：

- 若可解析 → 直接代入
- 若不可 → 调用 `scipy.optimize.fsolve` / `nlsolve`，初值取文献中位数

数值稳定提示：
- 把 `theta` 限制在合理区间（用 `bounds`）
- 雅可比病态时改用 `least_squares` 或 trust-region 算法
- 一次只匹配一个矩，避免过参数化

### Step 3. 待估参数（D 组，可选）

若 spec 要求 SMM/GMM：
- 输入：`data/calibration/<model>/<series>.csv`、模型仿真器、目标矩函数
- 输出：估计值、标准误、收敛诊断
- 必须在 `quality_reports/<model>_estimation_<timestamp>.md` 中记录优化路径

### Step 4. 写入 calibration.csv

保存到 `model/02_calibrate/<model>/calibration.csv`：

```csv
parameter,value,unit,source_type,source,identification,bounds_lower,bounds_upper,notes
beta,0.99,quarterly,A,Smets-Wouters (2007),literature,0.95,0.999,
alpha,0.33,share,B,NIPA 2010-2020 mean labor share complement,data direct,0.25,0.40,
delta,0.025,quarterly,C,K/Y=2.5 steady-state matching,moment matching,0.01,0.05,solved with rho_z=0.95
rho_z,0.95,persistence,A,King-Rebelo (1999),literature,0.5,0.99,
sigma_z,0.007,std,B,Solow residual stdev 1990-2020,data direct,0.001,0.05,
```

### Step 5. 生成语言专用参数文件

依据语言：
- **Dynare**：写 `parameters.mod`，把每个参数 `param = value;`
- **Julia**：写 `parameters.jl`，构造 `Dict` 或 `NamedTuple`
- **GAMS**：写 `parameters.gms`，`parameters` 段
- **Python**：写 `parameters.py`，`PARAMS = {...}`

每行附 `# source: <source>` 注释，便于回溯。

### Step 6. 维度与边界自检

调用 `math-reviewer` 子 agent 验证：
- 所有参数在 `bounds_lower` / `bounds_upper` 内
- 单位标注一致
- 离散化时间频率一致（季度 / 年）

### Step 7. 写日志

`logs/<model>_calibration_<timestamp>.log` 记录：
- 数据切片范围、N
- 每个矩的目标值与实现值
- 收敛诊断
- 警告与待解决项

### Step 8. 更新 session log

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `model/02_calibrate/<model>/calibration.csv` | ✅ | 单一事实源 |
| `model/02_calibrate/<model>/parameters.{mod,jl,gms,py}` | ✅ | 语言专用文件 |
| `output/tables/<model>_calibration.tex` | ✅ | 论文用 LaTeX 表 |
| `quality_reports/<model>_calibration_<timestamp>.md` | ✅ | 校准报告 |
| `logs/<model>_calibration_<timestamp>.log` | ✅ | 运行日志 |

## 不允许的操作

- 把"经验值"或"惯用值"作为 `source`。每个参数必须有可追溯出处。
- 在校准未通过 `math-reviewer` 边界自检的情况下进入 `solve-*`。
- 静默修改已发布的 `calibration.csv`。改动必须留 git commit 与 `quality_reports/` 记录。
- 用 `data/raw/` 中未经 `manifest.json` 登记的数据。

## 失败回退

| 症状 | 处理 |
|---|---|
| 矩匹配不收敛 | 检查初值；改用 `least_squares`；放宽 bounds；逐个矩匹配 |
| 参数撞到 bounds 边界 | 说明模型机制不足以解释该矩；改 spec 不是改 bounds |
| 数据起止与文献频率不符 | 在 spec.md 显式声明并由 `model-reviewer` 重审 |
| 估计标准误极大 | 弱识别问题；考虑增加矩或改用 bayesian 先验 |
