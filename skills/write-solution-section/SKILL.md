---
name: write-solution-section
description: 写论文 Solution Method section：线性化策略、Blanchard-Kahn 条件、政策矩阵、求解器精度。当用户说"写解法这一节"、"draft Section 4"时调用。
type: paper-composition
---

# write-solution-section — 解法章节

## 触发场景

- "写 Solution Method"、"draft Section 4"

## 输入契约

| 字段 | 说明 |
|---|---|
| `paper_dir` | 论文目录 |
| `policy_checkpoint` | `results/checkpoints/<model>_policy.json` |
| `numerics_review` | `quality_reports/<model>_numerics_review_*.md` |

## 前置条件

- 政策矩阵 checkpoint `validated == true`
- `numerics-reviewer` 通过

## 步骤清单

### Step 1. 子小节结构

1. **4.1 Linearisation / Perturbation Order**：解释解法 — 一阶摄动 vs 二阶 vs 投影 vs SSJ。说明为什么选这个（"the model is approximately linear within ±2σ of the steady state"）。
2. **4.2 Stability**：Blanchard-Kahn 条件叙述、特征值列出（从 checkpoint 提取）、为什么稳定。
3. **4.3 Implementation Notes**（简短一段）：使用的求解器（Dynare / Julia SSJ / 自写 Klein 等），但**不**贴代码 / 命令。

### Step 2. 写法示例

```latex
\section{Solution Method}
\label{sec:solution}

The system of equilibrium conditions in Section~\ref{sec:model} is linearised
around the deterministic steady state characterised in
Section~\ref{sec:calibration}. Letting $\hat{x}_t = \log x_t - \log x^\ast$
denote log-deviations from the steady state, the system reduces to a linear
expectational difference equation in the state vector
$(\hat{k}_t, \hat{z}_t)$ and the control $\hat{c}_t$.

The two eigenvalues of the resulting transition matrix are
$\{0.9621,\ 0.9500\}$, both strictly inside the unit circle. The
Blanchard--Kahn condition is therefore satisfied, and the rational-expectations
solution is unique \citep{BlanchardKahn1980}. The policy function for
consumption takes the linear form
\[
  \hat{c}_t = 0.5904\, \hat{k}_t + 0.3228\, \hat{z}_t,
\]
and capital follows
\[
  \hat{k}_{t+1} = 0.9621\, \hat{k}_t + 0.0801\, \hat{z}_t.
\]

The system is solved analytically by the method of undetermined coefficients
\citep{Uhlig1999}, which yields the closed-form policy functions reported
above.  We have verified the analytical solution by independently solving the
generalised Schur form of the system; the two methods agree to machine
precision.
```

### Step 3. 写入 sections/04_solution.tex

### Step 4. 评审

paper-reviewer + numerics-reviewer 双审：写作 + 数字一致。

## 输出契约

- `paper/sections/04_solution.tex`（约 400–700 词）
- 评审报告

## 不允许

- 贴代码 / shell 命令（"Run \texttt{python solve\_rbc.py}"——不可）
- 写"the pipeline computes" / "the solver returns"——直接陈述结果
- 暴露 checkpoint 文件名

## 失败回退

| 症状 | 处理 |
|---|---|
| BK 条件不满足 | 阻断，先回到 spec / 校准 |
| 数字与 checkpoint 不符 | 自动从 checkpoint 重读，禁止手抄 |
