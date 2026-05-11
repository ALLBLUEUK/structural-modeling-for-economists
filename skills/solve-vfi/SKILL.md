---
name: solve-vfi
description: 调用值函数迭代 / 策略迭代 / 投影法求解动态规划。当用户说"VFI"、"PFI"、"值函数迭代"、"projection"、"全局解"、"非线性求解"时调用。
type: solver
---

# solve-vfi — 值函数迭代 / 策略迭代 / 投影

## 触发场景

- "跑 VFI 求消费-储蓄问题"
- "用策略迭代加速收敛"
- "跑投影法（Chebyshev / spline）做全局非线性求解"
- "比较 VFI 与 EGM 的收敛速度"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str | 已通过 `model-reviewer` |
| `method` | enum | `vfi` / `pfi` / `egm` / `chebyshev` / `spline` |
| `tol` | float | 默认 `1e-6`（值函数）/ `1e-8`（策略） |
| `max_iter` | int | 默认 2000 |

## 步骤清单

1. 读 `output/checkpoints/<model>_ss.json`（或确定性边界值）作为初值。
2. 构造资产 / 状态网格（依 spec.md §8）。
3. 调用对应方法的求解器（Julia QuantEcon / Python interpolation.py）。
4. 记录每轮残差、迭代次数、收敛曲线。
5. 保存策略函数与值函数到 `output/checkpoints/<model>_policy.json`。
6. 调用 `numerics-reviewer` 检查收敛诊断。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `output/checkpoints/<model>_policy.json` | ✅ | 含策略 / 值函数 |
| `logs/<model>_vfi_<ts>.log` | ✅ | 迭代日志 |
| `quality_reports/<model>_numerics_review_<ts>.md` | ✅ |  |

## 不允许的操作

- 在网格未充分细化的情况下声称收敛
- 用过宽容差换收敛速度
- 跳过 `numerics-reviewer` 直接进入 IRF

## 失败回退

| 症状 | 处理 |
|---|---|
| 必备前置未满足 | 报错并指出缺什么；不绕过 |
| 上游产物 stale | 重跑上游 skill；不"凭旧的 checkpoint 继续" |
| 用户口径模糊 | 调用 `interview-me` skill 反向访谈 |
