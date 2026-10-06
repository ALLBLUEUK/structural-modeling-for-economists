---
name: setup-cge-gtap
description: 写或扩展一个 CGE / GTAP 模型的设定文档，提供免 GAMS 授权的 Python 求解模板（v0.3，多地区多部门 Armington）与 GAMS 脚手架。当用户说"建一个 CGE 模型"、"写 GAMS 文件"、"GTAP"、"关税反事实"、"social accounting matrix"时调用。
type: setup
---

# setup-cge-gtap — CGE / GTAP 设定与 GAMS 脚手架

## 触发场景

- "建一个 CGE / GTAP 模型研究 [关税 / 补贴 / 气候政策 / 区域贸易协定]"
- "写 GAMS 主文件"
- "扩展 GTAP v11 数据库到 [区域 / 行业 / 要素]"
- "做关税反事实仿真"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str | 如 `gtap_tariff`、`china_us_cge` |
| `regions` | list[str] | 区域列表（来自 GTAP 数据库） |
| `sectors` | list[str] | 行业列表 |
| `policy_lever` | str | 政策杠杆类型（关税 / 补贴 / 排放定价） |

## 步骤清单

1. 读 `templates/master-cge-template.gms` 与 `templates/model-spec-template.md`。
2. 写 `model/01_setup/<model>/spec.md`：代理人（家庭、生产部门、政府、国外）、嵌套 CES、闭合规则、SAM 平衡。
3. 维度自检：方程数 = 内生变量数；列出 numéraire；显式声明 macroclosure。
4. 提交 `model-reviewer` + `math-reviewer`。
5. 通过后：复制 `templates/master-cge-template.gms` 到 `model/03_solve/<model>/main.gms`。
6. 把 SAM 与弹性表导入 `data/calibration/<model>/`，并登记到 `manifest.json`。
7. 生成 `equations.tex` 用于 LaTeX 引用。
8. Walras 律自检（`scripts/check_walras.py`）。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `model/01_setup/<model>/spec.md` | ✅ | 事实源 |
| `model/01_setup/<model>/equations.tex` | ✅ | 方程 LaTeX |
| `model/03_solve/<model>/main.gms` | ✅ | GAMS 脚手架 |
| `data/calibration/<model>/manifest.json` | ✅ | 数据登记 |

## 不允许的操作

- 在未登记 manifest.json 的情况下使用 GTAP 数据
- 跳过 Walras 律校验进入反事实
- 在 spec 之外硬编码弹性参数

## 失败回退

| 症状 | 处理 |
|---|---|
| 必备前置未满足 | 报错并指出缺什么；不绕过 |
| 上游产物 stale | 重跑上游 skill；不"凭旧的 checkpoint 继续" |
| 用户口径模糊 | 调用 `interview-me` skill 反向访谈 |

## v0.3 新增：免 GAMS 授权的 Python 路径（推荐研究生先用）

`templates/master-cge-template.py` 求解多地区多部门 Armington 模型的关税反事实（Dekle–Eaton–Kortum 精确变化法），不需要 GAMS 或 GTAP 授权即可练习。

1. spec 通过双评审后，复制模板到 `model/03_solve/<model>/solve.py`，改 `MODEL_NAME`。
2. 数据放在 `data/calibration/<model>/trade_flows.csv`（`exporter,importer,sector,value`，出厂价），并登记到 `manifest.json`；若用示意数据，必须在 manifest、spec、所有图表与报告中声明。
3. 参数 `model/02_calibrate/<model>/calibration.csv` 中给出每个部门的 `eps_<sector>`；情形写在 `scenarios.csv`（`scenario,exporter,importer,sector,tariff_new`）。
4. 运行：`python model/03_solve/<model>/solve.py --purge --checks --scenario S1`。`--purge` 按 DEK (2008) 剔除基期赤字；`--checks` 运行 11 项数值验证（含独立水平量求解器交叉核对），结果写入 `output/checkpoints/<model>_checks.json`。
5. 用 `python scripts/check_walras.py output/checkpoints/<model>_<scenario>.json --tol 1e-9` 复核 Walras 律。
6. 情形汇总、贸易弹性稳健性与最优关税等反事实写在单独脚本中（`counterfactual-run`），调用 solve.py 的函数；注意每换一个弹性都要重新剔除赤字。

验收案例：`结项/工作流验收/case_cge_armington_tariff/`（示意数据下的单边关税与对等报复）。
