---
name: write-conclusion
description: 写论文 Conclusion section：核心发现 + 政策 / 理论涵义 + 局限 + 未来方向。一页以内。当用户说"写结论"、"draft conclusion"、"Section 7"时调用。
type: paper-composition
---

# write-conclusion — 结论章节

## 触发场景

- "写 Conclusion"、"draft Section 7"
- 全文其他 section 完成后

## 输入契约

| 字段 | 说明 |
|---|---|
| `paper_dir` | 论文目录 |
| `key_findings` | 来自 Section 5 的核心 2–4 个发现 |
| `policy_implications` | （可选）政策涵义 |
| `limitations` | 已知模型 / 数据 / 识别局限 |

## 步骤清单

### Step 1. 结构（四段法，每段 1–2 句话）

1. **Recap**：一句话再叙研究问题。
2. **Findings**：本文核心 2–4 个数字 / 定性发现。
3. **Implications**：理论 / 政策涵义。
4. **Limitations & Future Work**：诚实承认局限 + 提 2–3 个有趣的扩展。

### Step 2. 写法示例

```latex
\section{Conclusion}
\label{sec:conclusion}

This paper has examined how technology shocks propagate through a standard
real business cycle economy.  Using a calibrated model solved by the method
of undetermined coefficients, we have shown that a one-standard-deviation
positive TFP innovation generates an on-impact output response of 0.70\%, an
investment overshoot of roughly three times the output response, and a
gradual consumption build-up that peaks sixteen quarters after the shock.

These responses are quantitatively in line with empirical evidence on
post-war US business cycles \citep{KingRebelo1999} and underscore the
classical RBC mechanism in which agents use temporary productivity gains to
accumulate capital rather than to smooth consumption immediately.

The model abstracts from several features that matter in practice—most
notably an endogenous labour-supply margin, nominal rigidities, and
financial frictions.  Adding these features would likely dampen the
investment overshoot and accelerate the consumption response.  We view the
quantitative dissection of these channels in a unified framework as a
promising avenue for further work.
```

总长度约 250–400 词。**不要**写第五段，**不要**列每个变量数字（那已经在 Section 5 里）。

### Step 3. 写入 sections/07_conclusion.tex + 评审

## 输出契约

- `paper/sections/07_conclusion.tex` (约 250–400 词)
- 评审报告

## 不允许

- 引入新数字（结论不该出现 Section 5 没出现过的数字）
- 写"future work might include AI tools"（不上学术 conclusion）
- 把 limitations 写成自夸（"despite the simplicity, our model captures..."）
- 超过 1 页

## 失败回退

| 症状 | 处理 |
|---|---|
| 找不到 key_findings | 阻断；先把 results section 完成 |
| 局限性空 | 调 `devils-advocate` 拷问倒逼内容 |
