---
name: write-model-section
description: 写论文的 Model section：environment → agents → equilibrium → FOC。遵守 academic-writing-style 规则。当用户说"写模型这一节"、"draft section 2"、"把模型部分写出来"时调用。
type: paper-composition
---

# write-model-section — 模型章节

## 触发场景

- "写 Model section"、"draft Section 2"
- 在 `Introduction` 写完后自然推进
- 用户改了模型 spec 之后重写本节

## 输入契约

| 字段 | 说明 |
|---|---|
| `paper_dir` | 论文目录 |
| `spec_path` | `code/<model>/spec.md`，已通过 `model-reviewer` |
| `equations_path` | `code/<model>/equations.tex`，方程 LaTeX |

## 前置条件

- `spec.md` 通过 `model-reviewer` 与 `math-reviewer` 评审
- 已读 `rules/academic-writing-style.md`

## 步骤清单

### Step 1. 模型 section 的标准结构（按子小节）

1. **2.1 Environment**：时间、不确定性来源、信息结构、人口 / 部门 / 区域规模
2. **2.2 Households**：偏好、预算约束、选择变量
3. **2.3 Firms / Producers**：生产技术、利润最大化
4. **2.4 Government / Central Bank**（如适用）：政策规则、预算
5. **2.5 Foreign Sector**（如开放经济）
6. **2.6 Equilibrium**：定义市场出清条件、competitive equilibrium 定义
7. **2.7 First-Order Conditions**：用 `\input{../code/<model>/equations.tex}` 引入正式方程，附自然语言注释

### Step 2. 写子小节

每个 subsection 一段叙述 + 必要的公式 / 方程编号。
- 用正式数学语言："The representative household chooses $\{c_t, k_{t+1}\}_{t \ge 0}$ to maximise"
- 不要写 "we use a standard household"——具体写出来什么 standard
- 方程系统集中放 2.7，正文段落只用方程编号引用（如 "the Euler equation~\eqref{eq:euler}"）

### Step 3. 写入 sections/02_model.tex

```latex
\section{Model}
\label{sec:model}

\subsection{Environment}
...

\subsection{Households}
...

\subsection{Firms}
...

\subsection{Equilibrium}
...

\subsection{First-Order Conditions}
\input{../code/<model>/equations.tex}
...
```

### Step 4. 维度自检

确认 section 中提到的所有变量与 spec.md §4 的变量分类表一致。方程数与 spec.md §5.5 一致。

### Step 5. 提交 paper-reviewer + math-reviewer

paper-reviewer 看写作；math-reviewer 看本节与 spec 是否一致。

## 输出契约

- `paper/sections/02_model.tex` (约 1500–2500 词)
- 评审报告

## 不允许

- 在 Model section 写校准数字（那属于 Section 3）
- 在 Model section 写解法（那属于 Section 4）
- 写"我们用 Cobb-Douglas 因为它简单"——给经济学理由（returns to scale、tractability under specific aggregation）

## 失败回退

| 症状 | 处理 |
|---|---|
| spec.md 未通过评审 | 阻断，先修 spec |
| 变量在 section 中 vs spec.md 命名不一致 | 以 spec.md 为准，回头改 section |
