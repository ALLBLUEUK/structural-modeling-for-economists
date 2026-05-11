---
name: run-pipeline
description: 端到端跑某个模型的完整流水线（setup → calibrate → solve → simulate → output → report）。当用户说"从头到尾跑一遍"、"端到端"、"跑完整流程"、"我要全套结果"时调用。
type: orchestrator
---

# run-pipeline — 完整流水线

## 触发场景

- "把 rbc 模型从头到尾跑一遍"
- "我要全套结果（稳态 + IRF + 反事实 + 表 + 图）"
- "重新跑一遍流水线"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str | 必须存在 `model/01_setup/<model>/spec.md` |
| `mode` | enum | `full`（默认）/ `from_solve`（跳过 setup 与 calibrate）/ `from_simulate` |
| `language` | enum | 推断自 spec |
| `seed` | int? | 默认 `model/_utils/seed.txt` |

## 流程图

```
spec.md 评审通过？─NO─→ 报错并指 model-reviewer
   │YES
   ▼
calibration.csv 已填实参？─NO─→ calibrate-from-moments
   │YES
   ▼
validate-steady-state ──FAIL──→ math-reviewer
   │PASS
   ▼
solve-perturbation 或 solve-vfi（依 spec）
   │
   ▼
simulate-irf ──→ counterfactual-run（如 spec 要求）
   │
   ▼
build-tables（校准表 / IRF 表 / 反事实表）
   │
   ▼
render-report（Quarto / LaTeX）
   │
   ▼
verifier 子 agent 重跑核对
   │
   ▼
完成；commit skill 提交（可选）
```

## 步骤清单

### Step 1. 预检

- 检查 `spec.md`、`calibration.csv`、`equations.tex` 完整性
- 检查求解器可用：`scripts/run_dynare.sh` 或 `scripts/run_julia.sh` 自检命令

### Step 2. 顺序调用子 skill

按上图顺序调用，每步失败立即停止，写入 `quality_reports/<model>_pipeline_<timestamp>.md` 报告失败位置。

### Step 3. 最终验证

调用 `verifier` 子 agent，目标：

- 重跑稳态 → 对比 checkpoint
- 重跑 IRF → 对比 checkpoint，差异 < `1e-6`

### Step 4. 落地报告

- `reports/<model>_analysis.qmd` 编译为 PDF/HTML
- 顶层 `output/<model>_summary.md` 列：跑了哪些步骤、产物路径、关键数值

## 输出契约

整套：
- `model/01_setup/<model>/` 完整
- `model/02_calibrate/<model>/calibration.csv` 完整
- `output/checkpoints/<model>_*.json` 全集
- `output/tables/<model>_*.csv|tex`
- `output/figures/<model>_*.{pdf,png}`
- `output/latex/<model>/*.tex`
- `reports/<model>_analysis.qmd` + 渲染产物
- `quality_reports/<model>_pipeline_<timestamp>.md`

## 不允许

- 跳过 `verifier` 把结果写进报告
- 改动 `spec.md` 但不重跑评审
- 把求解失败的步骤标记为 "已完成"

## 命令行直跑

工作流也提供命令行入口：

```bash
bash scripts/run_pipeline.sh <model_name>
```

agent 调用本技能时，可选择直接执行该脚本 + 解读输出，或拆步执行（推荐拆步以获更细的失败定位）。
