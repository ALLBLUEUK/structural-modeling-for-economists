$ontext
==========================================================================
master-cge-template.gms · CGE / GTAP 主文件模板
语言版本：GAMS 45+ · 推荐 GTAP v11 数据库
模型：<MODEL_NAME>
spec：model/01_setup/<MODEL_NAME>/spec.md
==========================================================================

把本模板复制到 model/03_solve/<MODEL_NAME>/main.gms 后填空。
$offtext

* ---- 0. 基础设置 ----
$ondollar onmulti
option seed = 20250613;          // 与 model/_utils/seed.txt 一致
option iterlim = 10000;
option reslim  = 600;
option solprint = silent;
option mcp = path;

* ---- 1. 集合：区域、行业、要素、商品 ----
sets
    r       "regions"           / /
    i       "sectors / commodities" / /
    f       "factors"           / lab, cap, lnd /
;

* ---- 2. 数据：SAM / 弹性 ----
parameters
    sam(*,*,*)      "social accounting matrix per region"
    sigma(*)        "elasticities of substitution / transformation"
;

$include ../../02_calibrate/<MODEL_NAME>/parameters.gms

* ---- 3. 内生变量与价格 ----
variables
    Y(i,r)          "sectoral output"
    C(i,r)          "household consumption"
    G(i,r)          "government consumption"
    INV(i,r)        "investment by use"
    M(i,r)          "imports by region"
    X(i,r)          "exports by region"
    P(i,r)          "consumer prices"
    PF(f,r)         "factor prices"
    Y_TOT(r)        "regional GDP"
;

* ---- 4. 方程系统：来自 spec.md §5 ----
$include ../../01_setup/<MODEL_NAME>/equations.gms

* ---- 5. 模型声明（mixed-complementarity）----
model cge / all /;

* ---- 6. 校准与基准求解 ----
solve cge using mcp;

* ---- 7. 后处理：Walras 律与 SAM 校验数据落盘 ----
*   把市场出清残差与 SAM 行/列和写入 GDX，供 scripts/check_walras.py 读取
execute_unload 'output/checkpoints/<MODEL_NAME>_baseline.gdx';

* 可选：导出 JSON（依靠 gdxpds 或 gamspy 的后处理 Python 脚本）
$ontext
后处理 Python（model/03_solve/<MODEL_NAME>/postprocess.py）应：
  1. 读 baseline.gdx
  2. 计算每个市场的剩余（供给 - 需求）
  3. 计算 SAM 行和、列和
  4. 写 output/checkpoints/<MODEL_NAME>_baseline.json
     字段：market_clearing_residuals, sam_balance, prices, quantities
  5. 触发 scripts/check_walras.py
$offtext

* ---- 8. 反事实场景钩子 ----
*   反事实由 skills/counterfactual-run 接管，本文件保留 baseline 求解；
*   反事实脚本应单独建 model/04_simulate/<MODEL_NAME>/cf_<scenario>.gms。
