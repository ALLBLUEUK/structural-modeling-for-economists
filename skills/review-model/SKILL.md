---
name: review-model
description: 对模型设定与代码做一次轻量综合评议，并把重活分派给 model-reviewer / math-reviewer / code-reviewer / numerics-reviewer / pedagogy-reviewer 子 agent。当用户说"看看这个模型对不对"、"评议一下"、"reviewer 走一遍"时调用。
type: reviewer
---

# review-model — 综合模型评议

## 触发场景

- "看看这个模型对不对"、"做一轮评议"、"reviewer 走一遍"
- 完成 spec.md 后正式进入校准 / 求解前
- 投稿前的最后审查
- 中期 / 结项把项目"打包前"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str | 必须存在 `model/01_setup/<model>/spec.md` |
| `scope` | enum | `spec_only` / `code_only` / `full`（默认 `full`） |
| `urgency` | enum | `quick`（轻量自评） / `thorough`（调全部子 agent） |

## 步骤清单

### Step 1. 自检清单（轻量）

读 `spec.md`、`equations.tex`、`calibration.csv`，对下列问题给"是 / 否 / 不确定"：

- [ ] 研究问题用一句话能否清晰说明？
- [ ] 内生变量数 = 方程数？
- [ ] 每个参数都有 `source` 字段非空？
- [ ] 每个外生冲击都进入至少一条方程？
- [ ] spec.md §9.3 IRF 形状先验是否填实？
- [ ] 是否有解析稳态或数值稳态求解策略？
- [ ] 求解方法（摄动 / VFI / SSJ / GAMS）与模型类匹配？
- [ ] 时点约定（k_t 期初 / 期末）一致？

任一"否"或"不确定" → 进入 Step 2 详细评议。

### Step 2. 分派子 agent（thorough 模式）

按职责分派：

| 维度 | 子 agent |
|---|---|
| 经济机制 / 代理人完整 / 闭合 | `model-reviewer` |
| 维度 / 方程数 / FOC / 稳态残差 | `math-reviewer` |
| 求解器选择 / BK / 网格 / 收敛 | `numerics-reviewer` |
| 语言惯例 / 路径 / 注释 / 与 spec 对齐 | `code-reviewer` |
| 可读性 / 文献连接 / 复现路径 | `pedagogy-reviewer` |

每个子 agent 独立写报告到 `quality_reports/<model>_<reviewer>_<timestamp>.md`。

### Step 3. 汇总

把所有子 agent 报告的"综合"行汇总到 `quality_reports/<model>_review_summary_<timestamp>.md`：

```markdown
# 综合评议汇总 · <model> · <timestamp>

| 维度 | 子 agent 判断 | 报告 |
|---|---|---|
| 经济机制 | 通过 | quality_reports/<model>_model_review_<ts>.md |
| 数学 | 修改后通过 | quality_reports/<model>_math_review_<ts>.md |
| 数值方法 | 通过 | quality_reports/<model>_numerics_review_<ts>.md |
| 代码 | 通过 | quality_reports/<model>_code_review_<ts>.md |
| 教学 | 修改后通过 | quality_reports/<model>_pedagogy_review_<ts>.md |

## 必改清单（合并去重）
- [ ] ...
- [ ] ...

## 建议进度门
- 进入校准 / 求解：✅ / ❌（修改后）
- 进入对外报告：⏸️（依赖 verifier）
```

### Step 4. 决策门

- 全部"通过"或"修改后通过且必改项已 tick" → 允许进入下一阶段（校准 → 求解 → 仿真）
- 任一"不通过" → 阻断流水线，必须先修

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `quality_reports/<model>_review_summary_<timestamp>.md` | ✅ | 汇总 |
| `quality_reports/<model>_<reviewer>_<timestamp>.md` × 5 | thorough 模式必产 | 各子 agent 报告 |

`quick` 模式可只产汇总，不调子 agent。

## 不允许的操作

- 在 thorough 模式下跳过任一子 agent
- 在某子 agent 给出"不通过"的状态下放行进入求解
- 把 `review-model` 当成 `model-reviewer` 的同义词（前者是分派器，后者是经济逻辑专家）
- 在没有 spec.md 的情况下声称"评议通过"

## 失败回退

| 症状 | 处理 |
|---|---|
| 子 agent 之间结论冲突 | 在汇总报告中显式记录冲突，由人工裁决 |
| 学生 spec 写得太粗糙无法评议 | 调 `interview-me` skill 反向访谈 |
| reviewer 自己不确定 | 不要硬给"通过"，写"不确定 + 需要更多信息" |
