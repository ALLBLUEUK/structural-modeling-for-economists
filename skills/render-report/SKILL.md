---
name: render-report
description: 基于 output/ 中的产物渲染 Quarto / LaTeX 报告。当用户说"出报告"、"render report"、"compile"、"渲染论文"时调用。
type: utility
---

# render-report — Quarto / LaTeX 报告渲染

## 触发场景

- "渲染 Quarto 报告"
- "编译 LaTeX 论文"
- "出 PDF / HTML 给老板"
- "出投稿用稿件"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str |  |
| `format` | enum | `pdf` / `html` / `docx` |
| `template` | path? | 默认 `templates/analysis-report.qmd` |

## 步骤清单

1. 确认 `reports/<model>_analysis.qmd` 存在；若无，从模板复制。
2. 确认 `output/tables/`、`output/figures/`、`output/latex/<model>/` 已齐。
3. 运行 `quarto render reports/<model>_analysis.qmd` 或 `latexmk`。
4. 校核 PDF：图表存在、引用解析、无 \?? 警告。
5. 把渲染产物（不是源）放 `reports/_rendered/`。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `reports/_rendered/<model>_analysis.{pdf,html}` | ✅ |  |
| `logs/<model>_render_<ts>.log` | ✅ |  |

## 不允许的操作

- 在数字未通过 verifier 时声称报告 ready
- 在报告里手写公式（必须 \input{output/latex/<model>/...}）

## 失败回退

| 症状 | 处理 |
|---|---|
| 必备前置未满足 | 报错并指出缺什么；不绕过 |
| 上游产物 stale | 重跑上游 skill；不"凭旧的 checkpoint 继续" |
| 用户口径模糊 | 调用 `interview-me` skill 反向访谈 |
