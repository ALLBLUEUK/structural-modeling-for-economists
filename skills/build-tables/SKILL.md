---
name: build-tables
description: 组装校准表 / 矩比对表 / IRF 表 / 反事实表为 CSV 与 LaTeX。当用户说"做表"、"build tables"、"出 LaTeX 表"、"摘要表"时调用。
type: utility
---

# build-tables — 表格组装

## 触发场景

- "把 calibration.csv 转成 LaTeX 表"
- "做 baseline vs counterfactual 比对表"
- "出 IRF 峰值表"
- "做矩匹配（数据 vs 模型）表"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str |  |
| `table_kind` | enum | `calibration` / `moment` / `irf_peak` / `cf_compare` |
| `source_files` | list[path] |  |
| `format` | enum | `csv` / `tex` / `both`（默认 both） |

## 步骤清单

1. 读源文件（calibration.csv / IRF JSON / cf JSON）。
2. 依 `table_kind` 应用对应模板（在 `templates/` 下）。
3. 导出 CSV 与 LaTeX（`booktabs` 风格）到 `output/tables/`。
4. 更新 LaTeX 报告 `\input{}` 索引。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `output/tables/<model>_<kind>.csv` | ✅ |  |
| `output/tables/<model>_<kind>.tex` | ✅ |  |

## 不允许的操作

- 把未经 verifier 核对的数字直接写进 .tex
- 用 fixed point precision 隐藏数值漂移

## 失败回退

| 症状 | 处理 |
|---|---|
| 必备前置未满足 | 报错并指出缺什么；不绕过 |
| 上游产物 stale | 重跑上游 skill；不"凭旧的 checkpoint 继续" |
| 用户口径模糊 | 调用 `interview-me` skill 反向访谈 |
