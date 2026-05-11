---
name: setup-dsge
description: 写或扩展一个 DSGE 模型的设定文档与代码脚手架（Dynare 或 Julia）。当用户说"建一个 DSGE 模型"、"写 Dynare 文件"、"加一段新凯恩斯模块"、"扩展 RBC"、"做一个开放经济 DSGE"时调用。
type: setup
---

# setup-dsge — DSGE 模型设定与脚手架

## 触发场景

- "我想建一个 DSGE 来研究 [关税冲击 / 利率规则 / 财政政策]"
- "扩展 RBC 加入 [资本调整成本 / 名义粘性 / 异质家庭]"
- "把这篇论文（DSGE）的代码用 Dynare 写出来"
- "我有一段经济机制的描述，请生成 spec.md 和 .mod 骨架"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str | 例 `rbc`、`smets_wouters`、`open_economy_dsge` |
| `mechanism` | str | 自然语言描述：要研究的机制、冲击类型、关键特征 |
| `language` | enum | `dynare` (默认) / `julia` |
| `extends` | str? | 可选：基于哪个已有模型扩展 |

## 步骤清单

### Step 1. 读上下文

```
- AGENTS.md 中的"计划先行"段
- .claude/rules/plan-first-modeling.md
- templates/model-spec-template.md
- 若 extends 不为空，读 model/01_setup/<extends>/spec.md
```

### Step 2. 起草 spec.md

把 `templates/model-spec-template.md` 复制到 `model/01_setup/<model_name>/spec.md`，按以下顺序填空：

1. **经济问题**（1 段）：研究问题、关键机制、文献定位
2. **环境**（1 段）：时间设定、随机性来源、信息结构
3. **代理人**（每类 1 段）：家庭、企业、政府、央行、外部经济
4. **变量分类表**：

   | 变量 | 类型 | 时点 | 单位 | 含义 |
   |---|---|---|---|---|
   | `c_t` | 控制 | t | 实物 | 消费 |
   | `k_t` | 状态 | t | 实物 | 资本（期初） |
   | `z_t` | 外生 | t | 比例 | 全要素生产率 |
   | … | | | | |

5. **方程系统**（按家庭/企业/政府/出清/外生过程分块），每个方程附自然语言注释
6. **函数形式**（效用、生产、调整成本等）
7. **参数表**：

   | 参数 | 含义 | 校准值（占位） | 来源 |
   |---|---|---|---|
   | `beta` | 折现因子 | 0.99 | Smets-Wouters (2007) |

8. **求解方法**：摄动阶数 / 网格 / 收敛准则 / 初值策略
9. **验证目标**：稳态矩、复现目标、IRF 形状先验

### Step 3. 维度自检

agent **必须**自己先做一次对账：

- 内生方程数 = 内生变量数？
- 每个方程的两端单位一致？
- 状态变量的时点（t-1 期初 vs t 期末）是否一致？
- 外生过程的协方差矩阵正定？

不通过则停下，提交 `math-reviewer` 子 agent。

### Step 4. 提交 model-reviewer

把 `spec.md` 路径丢给 `model-reviewer` 子 agent。等评审通过后才能进入 Step 5。

### Step 5. 生成代码骨架

依据 `language`：

- **Dynare**：复制 `templates/master-dsge-template.mod` 到 `model/03_solve/<model_name>/<model_name>.mod`，按 spec 填入：
  - `var ...;`（内生变量）
  - `varexo ...;`（外生冲击）
  - `parameters ...;` + 参数赋值
  - `model;` 块（方程）
  - `steady_state_model;`（若可解析）
  - `shocks;` 块
  - `stoch_simul(...);` 调用
- **Julia**：复制 `templates/master-ha-template.jl` 适配为 DSGE 模板，建立 `Model` 结构体、`steady_state` 函数、`linearize` 接口。

### Step 6. 生成 LaTeX 公式镜像

把方程系统输出到 `output/latex/<model_name>/equations.tex`，使用 `align*` 与编号 `\label{eq:<name>}`，与 `spec.md` 中的方程一一对应。

### Step 7. 写入会话日志

把本次操作追加到 `templates/session-log.md` 的工作副本。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `model/01_setup/<model_name>/spec.md` | ✅ | 模型设定单一事实源 |
| `model/01_setup/<model_name>/equations.tex` | ✅ | 方程 LaTeX 镜像 |
| `model/03_solve/<model_name>/<model_name>.mod` 或 `run.jl` | ✅ | 代码骨架（**不**自行求解） |
| `model/02_calibrate/<model_name>/calibration.csv` | ✅ | 占位校准（值待填） |

## 不允许的操作

- 在未通过 `model-reviewer` 之前调用任何求解器
- 把"经验值"写进校准表而无来源
- 跳过维度自检直接生成代码
- 在 `spec.md` 之外的位置放置方程系统

## 失败回退

| 症状 | 处理 |
|---|---|
| 用户机制描述太模糊 | 调用 `interview-me` skill 反向访谈 |
| 维度自检不过 | 写 `quality_reports/<model>_dim_<date>.md` 把矛盾列清楚交给 `math-reviewer` |
| spec 模板缺字段 | 不要漏填，宁可写 "TBD（理由：…）" 也别留空 |
