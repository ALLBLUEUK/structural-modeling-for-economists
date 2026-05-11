---
name: paper-structure
description: 给一个研究项目搭起完整的学术论文骨架（main.tex + sections/ + appendix/ + references.bib）。当用户说"建一个论文项目"、"起论文骨架"、"draft paper structure"、"set up paper directory"时调用。
type: paper-composition
---

# paper-structure — 搭学术论文骨架

## 触发场景

- "起一个 RBC / CGE / HA 论文项目，把骨架搭好"
- "我想开始写论文"
- "建 paper/ 目录"
- "set up the manuscript directory"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `project_root` | path | 用户研究项目根（默认 `pwd`） |
| `paper_title` | str | 论文工作标题（之后可改） |
| `authors` | list[dict] | 含 `name`、`affiliation`、`email` |
| `model_class` | enum | `dsge` / `cge` / `ha` / `dp` / `empirical` |

## 前置条件

- 项目根存在且可写
- 若用户已有 `paper/` 目录非空 → 询问是覆盖还是退出（避免破坏既有写作）

## 步骤清单

### Step 1. 建目录树

```
<project_root>/
└── paper/
    ├── main.tex
    ├── sections/
    │   ├── 01_introduction.tex
    │   ├── 02_model.tex
    │   ├── 03_calibration.tex
    │   ├── 04_solution.tex
    │   ├── 05_results.tex
    │   ├── 06_robustness.tex
    │   └── 07_conclusion.tex
    ├── appendix/
    │   ├── A_proofs.tex
    │   └── B_additional_results.tex
    ├── references.bib
    ├── figures/    (空，由 simulate-irf 等技能填)
    └── tables/     (空，由 build-tables 填)
```

### Step 2. 复制 `templates/paper/` 模板

从 plugin 的 `templates/paper/` 目录把骨架文件复制到 `<project_root>/paper/`。每个 `sections/0X_*.tex` 是带占位 prompt 的空段。

### Step 3. 填实 main.tex 的元信息

把用户给的 `paper_title`、`authors`、`model_class` 插入到 `main.tex` 的 `\title{}`、`\author{}` 中。设置 `\documentclass[11pt]{article}`、合理的 packages、`\graphicspath{{../results/figures/}}`、`bibliographystyle`、`hyperref`。

### Step 4. 初始化 references.bib

把模板 `references.bib` 复制过去——它已经包含按 `model_class` 预选的 3–5 个**必引**经典文献的 BibTeX 条目（如 DSGE 必引 Kydland-Prescott 1982、King-Rebelo 1999；CGE 必引 Hertel 1997；HA 必引 Aiyagari 1994）。用户后续用 `manage-bibliography` skill 补加自有引用。

### Step 5. 写入会话日志

记录"已在 `<project_root>/paper/` 建立论文骨架，等待 `write-introduction` 等技能开始填实"。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `paper/main.tex` | ✅ | 根文档 |
| `paper/sections/0[1-7]_*.tex` | ✅ | 7 个 section 占位 |
| `paper/appendix/{A,B}_*.tex` | ✅ | 2 个 appendix 占位 |
| `paper/references.bib` | ✅ | 必引文献已预填 |
| `paper/figures/`、`paper/tables/` | ✅ | 空目录 |

## 不允许的操作

- 直接往 `sections/*.tex` 写实质内容（那是 `write-*` skill 的活）
- 跳过 `main.tex` 元信息直接用占位 "Title TBD"
- 选错 documentclass（用 beamer / article 以外的）
- 在骨架阶段就插入 `\input{}` 不存在的 section

## 失败回退

| 症状 | 处理 |
|---|---|
| paper/ 已存在非空 | 询问用户：覆盖（带备份）/ 跳过 / 退出 |
| 用户未提供 authors | 用 placeholder 但显式标注 TODO 并提示用户补 |
| 用户给 model_class 不在预定义列表 | 询问，不要默认 dsge |
