# Modeling Coding Conventions — 建模代码规范

## 通用

- **语言版本** 在文件顶部声明：`version 6.1` (Dynare) / `using Pkg; Pkg.activate("@v1.10")` (Julia) / `% MATLAB R2023a` 注释 / `$ondollar onmulti` (GAMS)。
- **相对路径**：所有 IO 用相对路径。`cd` 集中在 `model/_utils/setup_paths.*`。
- **日志开闭**：可执行脚本顶部 `log open ...` / 末尾 `log close`。文件名 `logs/<model>_<step>_<YYYYMMDD_HHMMSS>.log`。
- **种子读取**：从 `model/_utils/seed.txt` 读，禁止硬编码。
- **检查点保存**：求解后立即保存到 `output/checkpoints/<model>_<artifact>.json`。
- **图表导出**：同时输出 `.pdf` 与 `.png` 到 `output/figures/`。
- **LaTeX 公式**：写入 `output/latex/<model>/<topic>.tex`，由 `reports/` 下报告 `\input{}` 引用。
- **中文注释**：所有新写或修改代码的注释默认中文。

## Dynare (.mod)

```dynare
// model/03_solve/<model>/<model>.mod
// 语言版本：Dynare 6.1
// 模型：<model> · spec：model/01_setup/<model>/spec.md

@#define MODEL = "<model>"

var c k z;       // 内生变量
varexo eps_z;    // 外生冲击
parameters beta alpha rho sigma;

// 参数赋值（来自 calibration.csv）
@#include "../../02_calibrate/<model>/parameters.mod"

model;
  // FOC：消费欧拉方程
  1/c = beta * (1/c(+1)) * (alpha*exp(z(+1))*k^(alpha-1) + 1 - delta);
  // 资本积累
  k = (1-delta)*k(-1) + exp(z)*k(-1)^alpha - c;
  // 技术冲击 AR(1)
  z = rho*z(-1) + eps_z;
end;

steady_state_model;
  // 解析稳态（若有）
end;

shocks;
  var eps_z; stderr sigma;
end;

stoch_simul(order=1, irf=40, periods=0);

// 检查点保存（在 .mod 末尾或 wrapper 脚本中）
// 见 scripts/run_dynare.sh 的 post-processing
```

⚠️ **不要**在 Dynare 文件中放包含 `/*` 的注释（如路径 `output/tables/*`），Dynare 会把 `/*` 当块注释起点而吞掉后续内容。

## Julia

```julia
# model/03_solve/<model>/run.jl
# 语言版本：Julia 1.10 + SequenceJacobian 0.x

using Pkg
Pkg.activate(joinpath(@__DIR__, "..", ".."))

include(joinpath(@__DIR__, "..", "..", "_utils", "setup_paths.jl"))
include(joinpath(@__DIR__, "..", "..", "_utils", "seed.jl"))

# 加载校准
params = load_calibration("<model>")

# 模型构建
model = build_model(params)

# 稳态
ss = steady_state(model)
save_checkpoint("output/checkpoints/<model>_ss.json", ss)

# 求解
sol = solve!(model; order=1, ss=ss)
save_checkpoint("output/checkpoints/<model>_policy.json", sol)
```

## MATLAB

```matlab
% model/03_solve/<model>/main.m
% 语言版本：MATLAB R2023a · Dynare 6.1

% 路径设置
run(fullfile(fileparts(mfilename('fullpath')), '..', '..', '_utils', 'setup_paths.m'));

% 种子
seed = load_seed();
rng(seed);

% 调用 Dynare
dynare <model>.mod noclearall;

% 后处理与保存检查点
save_checkpoint('output/checkpoints/<model>_policy.json', oo_);
```

## GAMS

```gams
* model/03_solve/<model>/main.gms
* 版本：GAMS 45.x · GTAP v11

$ontext
模型：<model>
spec：model/01_setup/<model>/spec.md
$offtext

$include ../../02_calibrate/<model>/parameters.gms
$include ../../01_setup/<model>/equations.gms

solve cge using mcp;

* 检查点
execute_unload 'output/checkpoints/<model>_baseline.gdx';
```

## 受保护文件

下列文件**不**得随意修改，必须经显式 PR 审议：

- `model/00_master.{mod,jl,m,gms}`
- `.gitignore`
- `data/calibration/<model>/manifest.json`
- `model/_utils/seed.txt`

## 命名

- 模型名：snake_case，全小写，例 `rbc`、`smets_wouters`、`open_economy_dsge`
- 脚本：`<purpose>_<model>.<ext>`，例 `solve_rbc.jl`、`irf_open_economy_dsge.m`
- 检查点：`<model>_<artifact>.json`，例 `rbc_ss.json`、`rbc_policy.json`
- 图表：`<model>_<topic>.{pdf,png}`，例 `rbc_irf_z.pdf`
