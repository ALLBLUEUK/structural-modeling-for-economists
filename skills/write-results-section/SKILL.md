---
name: write-results-section
description: 写论文 Results section：IRF / 反事实 / 福利分析 + 经济解读（不光列数字）。当用户说"写结果这一节"、"draft Section 5"、"分析 IRF"时调用。
type: paper-composition
---

# write-results-section — 结果章节

## 触发场景

- "写 Results"、"draft Section 5"
- 在 IRF 跑完后；反事实跑完后

## 输入契约

| 字段 | 说明 |
|---|---|
| `paper_dir` | 论文目录 |
| `irf_checkpoint` | `results/checkpoints/<model>_irf_*.json` |
| `cf_checkpoints` | （可选）反事实 checkpoint 列表 |
| `irf_figure_path` | `results/figures/<model>_irf_*.pdf` |

## 前置条件

- IRF 通过 `simulate-irf` 全部 8 项形态诊断
- `verifier` 通过

## 步骤清单

### Step 1. 子小节结构

1. **5.1 Impulse Responses**：每个外生冲击一段，配图 + 经济解读
2. **5.2 Counterfactual / Policy Experiment**（若做了）：baseline vs scenario
3. **5.3 Welfare Analysis**（若做了）：CEV / lifetime utility 对比
4. **5.4 Comparison with Empirical Evidence / Literature**：把模型数字与文献对照

### Step 2. 关键：经济解读不能省

每给一个数字，必须接一句 / 一段**为什么**：

❌ 不够好：
> Output rises 0.7% on impact and decays at rate $\rho_z$.

✅ 应该写：
> Output rises by 0.7\% on impact, mirroring the size of the underlying TFP innovation
> (since the production function is Cobb--Douglas with technology entering log-linearly).
> The response then decays geometrically at rate $\rho_z = 0.95$, with a half-life of
> approximately fourteen quarters. Investment overshoots output by a factor of roughly
> three, consistent with the standard RBC result that the agent uses the temporary
> productivity boost to accumulate capital rather than smooth consumption, given that
> consumption smoothing is already largely achieved through the capital margin (cf.\
> \citealp{KingRebelo1999}, Section~3.2).

### Step 3. 写法示例（IRF 段）

```latex
\section{Results}
\label{sec:results}

\subsection{Impulse Responses to a TFP Shock}

\begin{figure}[t]
  \centering
  \includegraphics[width=0.95\textwidth]{<model>_irf_eps_z.pdf}
  \caption{Impulse responses to a positive one-standard-deviation TFP innovation.
    Each panel shows the percentage deviation of the variable from its
    deterministic steady state at quarterly frequency.  The shock follows an
    AR(1) process with persistence $\rho_z = 0.95$ and innovation standard
    deviation $\sigma_z = 0.007$.}
  \label{fig:irf}
\end{figure}

Figure~\ref{fig:irf} reports the impulse responses to a one-standard-deviation
positive TFP innovation.  Four features are worth highlighting.

\emph{First}, output rises by 0.70\% on impact and decays smoothly thereafter.
The on-impact response equals exactly $\sigma_z$ because, with capital
predetermined, output equals $e^{z_t} k_t^\alpha$, and the elasticity of
output with respect to log TFP is one.

\emph{Second}, investment overshoots output by a factor of approximately three
\dots

\emph{Third}, consumption rises gradually rather than on impact, peaking at
quarter sixteen at 0.37\% above steady state. \dots

\emph{Fourth}, capital accumulates slowly, peaking at quarter twenty-two at
0.48\% \dots
```

### Step 4. 图表交叉引用

每个图必有 `\label{fig:xxx}`，每次提到必用 `Figure~\ref{fig:xxx}`。表同理。

### Step 5. 写入 sections/05_results.tex + 评审

paper-reviewer：
- 每段是否有经济解读？
- 数字与 IRF JSON 一致？
- 与文献对照是否合理？
- 引用是否在 .bib 中？

verifier：
- 抽样数字（峰值、半衰期）—— 是否能从 checkpoint 复现？

## 输出契约

- `paper/sections/05_results.tex` (约 1500–3000 词，**最长 section**)
- `paper/figures/<model>_irf_*.pdf` 已复制到 paper/figures/（或 `\graphicspath` 指向 `../results/figures/`）
- 评审报告

## 不允许

- 列数字不解释（让读者自己琢磨）
- 用 "as expected" / "as is well-known"（懒得给理由）
- 写 "the simulation shows"（→ "the model implies"）
- 写"see `results/checkpoints/...`"

## 失败回退

| 症状 | 处理 |
|---|---|
| IRF 形态异常 | 阻断；回 `simulate-irf` 诊断 |
| 数字与 checkpoint 不符 | 强制从 checkpoint 重读 |
| 经济解读乏力 | 调 `devils-advocate` 子 agent 拷问，倒逼补内容 |
