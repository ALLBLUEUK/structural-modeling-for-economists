---
name: counterfactual-run
description: 跑反事实 / 过渡路径 / 政策实验，对比 baseline。当用户说"反事实"、"counterfactual"、"政策实验"、"transition path"、"如果……会怎样"时调用。
type: simulator
---

# counterfactual-run — 反事实 / 过渡路径 / 政策实验

## 触发场景

- "把关税从 5% 提到 25% 看 GDP 路径"
- "比较两种货币政策规则"
- "做福利分析（CEV）"
- "跑过渡路径（从一个稳态到另一个稳态）"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str | 已求解 baseline |
| `scenarios` | list[dict] | 每个含 `name`、`param_overrides`、`shock_path` |
| `horizon` | int | 默认 200（过渡路径长） |
| `welfare_metric` | enum | `cev` / `lump_sum` / `none` |

## 步骤清单

1. 加载 baseline 检查点。
2. 对每个 scenario：覆盖参数 / 注入冲击路径，求新稳态或过渡路径。
3. 把 baseline vs scenario 的关键变量保存到 `output/tables/<model>_cf_<scenario>.csv`。
4. 若 welfare 评估，计算 CEV 并报告。
5. 调用 `verifier` 重跑核对。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `output/tables/<model>_cf_<scenario>.csv` | ✅ |  |
| `output/checkpoints/<model>_cf_<scenario>.json` | ✅ |  |
| `output/figures/<model>_cf_<scenario>.{pdf,png}` | ✅ |  |

## 不允许的操作

- 用同 seed 但混用 baseline / scenario 的 shock 序列做对比（必须显式声明）
- 在没有 baseline `validated == true` 的情况下做反事实
- 把 welfare 数字写进报告但未经 `verifier`

## 失败回退

| 症状 | 处理 |
|---|---|
| 必备前置未满足 | 报错并指出缺什么；不绕过 |
| 上游产物 stale | 重跑上游 skill；不"凭旧的 checkpoint 继续" |
| 用户口径模糊 | 调用 `interview-me` skill 反向访谈 |
