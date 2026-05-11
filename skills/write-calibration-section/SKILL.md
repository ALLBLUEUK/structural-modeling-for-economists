---
name: write-calibration-section
description: 写论文 Calibration / Data section：参数表（带来源） + 稳态矩 + 数据矩对照。遵守 academic-writing-style。当用户说"写校准这一节"、"draft Section 3"、"写参数表"时调用。
type: paper-composition
---

# write-calibration-section — 校准章节

## 触发场景

- "写 Calibration section"、"draft Section 3"
- 校准表完成后

## 输入契约

| 字段 | 说明 |
|---|---|
| `paper_dir` | 论文目录 |
| `calibration_csv` | `code/<model>/calibration.csv`（每参数有来源） |
| `ss_checkpoint` | `results/checkpoints/<model>_ss.json` |
| `target_moments` | 来自 `spec.md` §9.1 的目标矩 |

## 前置条件

- 校准表通过 `calibrate-from-moments` + `math-reviewer`
- 稳态通过 `validate-steady-state`

## 步骤清单

### Step 1. 子小节结构

1. **3.1 Parameter Calibration**：分组（preferences / technology / shocks），每组一个 LaTeX 表（`booktabs`），列出参数符号、取值、含义、来源。
2. **3.2 Steady-State Properties**：K/Y、C/Y、I/Y 等关键稳态比率，与数据对照。
3. **3.3 Data**（若适用）：若涉及微观或时间序列数据，描述来源、覆盖期、清洗步骤。否则跳过。

### Step 2. 构造 LaTeX 参数表

直接从 `calibration.csv` 构造：

```latex
\begin{table}[t]
  \centering
  \caption{Calibrated parameters (quarterly).}
  \label{tab:calibration}
  \begin{tabular}{lcll}
    \toprule
    Parameter & Value & Description & Source \\
    \midrule
    $\beta$    & 0.99  & discount factor          & \citet{KingRebelo1999} \\
    $\alpha$   & 0.33  & capital share            & NIPA, 1990--2019 avg. \\
    $\delta$   & 0.025 & quarterly depreciation   & 10\% annual rate \\
    $\rho_z$   & 0.95  & TFP persistence          & \citet{KingRebelo1999} baseline \\
    $\sigma_z$ & 0.007 & TFP innovation std.\     & post-war US Solow residual \\
    \bottomrule
  \end{tabular}
\end{table}
```

引用 key 必须存在于 `references.bib`，否则调 `manage-bibliography` 补加。

### Step 3. 写稳态对照

```latex
\subsection{Steady-State Properties}
At the calibrated parameters the model implies $K/Y = 9.40$ at quarterly frequency
(equivalently $2.35$ at annual frequency), $C/Y = 0.77$, and $I/Y = 0.23$.
These ratios match standard quarterly US business-cycle moments (see, e.g.,
\citealp{KingRebelo1999}, Table~1).
```

数字必须来自 checkpoint，不是手写。

### Step 4. 写 sections/03_calibration.tex

```latex
\section{Calibration}
\label{sec:calibration}

\subsection{Parameter Values and Sources}
...

\subsection{Steady-State Properties}
...

\subsection{Data}  % 若适用
...
```

### Step 5. 评审

paper-reviewer 检查：每个参数表行都有 source 列；引用 key 全部解析；数字与 checkpoint 一致。

## 输出契约

- `paper/sections/03_calibration.tex`
- `paper/tables/<model>_calibration.tex`（可被 main.tex `\input{}` 的独立表）
- 评审报告

## 不允许

- 列参数但 Source 列写 "calibrated to literature"（含混）— 必须具体到 `\citet{}` 或 "X data, period Y"
- 数字与 checkpoint 不一致（手抄错）— 必须脚本化提取
- 写 "see calibration.csv"（暴露文件路径）

## 失败回退

| 症状 | 处理 |
|---|---|
| 参数无 source | 阻断，先调 `calibrate-from-moments` 补来源 |
| 数据期与文献频率不符 | 在 §3.3 显式说明，并由 `model-reviewer` 重审 |
