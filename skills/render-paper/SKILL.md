---
name: render-paper
description: 编译 paper/main.tex 到 paper/paper.pdf。pdflatex + bibtex 两遍循环，处理引用与交叉引用。前置：所有 sections/ 已写、references.bib 通过 audit。当用户说"编译论文"、"render paper"、"出 PDF"时调用。
type: paper-composition
---

# render-paper — 论文编译

## 触发场景

- "编译论文出 PDF"
- "render paper"
- 完成所有 section 写作 + 评议后

## 输入契约

| 字段 | 说明 |
|---|---|
| `paper_dir` | 默认 `<project_root>/paper/` |
| `main_tex` | 默认 `main.tex` |
| `engine` | `pdflatex`（默认）/ `xelatex` / `lualatex` |

## 前置条件

- 所有 `sections/*.tex` 与 `appendix/*.tex` 内容齐备
- `references.bib` 通过 `manage-bibliography` audit
- 所有图存在于 `paper/figures/` 或 `\graphicspath` 指向位置
- **`paper-reviewer` 已逐 section 评审通过**

## 步骤清单

### Step 1. 预编译检查

- `paper/main.tex` 顶部声明 `\documentclass`、必备 packages（`amsmath, amssymb, graphicx, booktabs, natbib, hyperref, geometry`）
- `\bibliographystyle{...}` 与 BibTeX style 一致（推荐 `aer`、`econometrica`、或 `plainnat`）
- `\graphicspath{}` 正确指向 figure 位置

### Step 2. 两轮编译

```bash
cd <paper_dir>
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

第二、三遍是为了解决 `\ref{}` / `\cite{}` 的前向引用。

### Step 3. 解析 `.log` 文件，列出：

- 严重错误（`! ...`）→ 阻断
- 未解析引用（`Reference XYZ undefined`）→ 阻断，调 `manage-bibliography`
- 未解析交叉引用（`?` 在 PDF 上）→ 阻断
- 过满 hbox / underfull → 警告但不阻断

### Step 4. 重命名输出

`main.pdf` → `paper.pdf`（标准化输出名）

### Step 5. 清理副产物

删 `*.aux`、`*.log`、`*.bbl`、`*.blg`、`*.toc`、`*.out`、`*.fls`、`*.fdb_latexmk`（这些不入 git）。

### Step 6. 最终 PDF 提交 paper-reviewer

paper-reviewer 看：
- 物理外观（边距、字体、行距、页码）
- 章节结构（必备 7 节齐全）
- 无 `??` 未解析符号
- 无机器路径 / 流水线泄露
- 引用规范

通过 → 完成；不通过 → 阻断 + 报错位置。

### Step 7. 写日志

`logs/<project>_render_<ts>.log` 含完整 pdflatex stdout + bibtex stdout + 最终 PDF 大小与页数。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `paper/paper.pdf` | ✅ | 最终论文 |
| `logs/<project>_render_<ts>.log` | ✅ | 编译日志 |
| `quality_reports/<project>_paper_review_<ts>.md` | ✅ | paper-reviewer 终审 |

## 不允许

- 在未通过 paper-reviewer 的状态下发布 PDF
- 跳过 bibtex 让 `[?]` 出现在最终 PDF
- 把编译副产物（aux / log）提交 git

## 失败回退

| 症状 | 处理 |
|---|---|
| pdflatex 报严重错 | 抓 log 中的 `! ` 段，定位到 `.tex` 行，提示用户修 |
| `Reference ... undefined` | 调 `manage-bibliography` audit |
| 图找不到 | 检查 `\graphicspath` 与 `results/figures/` |
