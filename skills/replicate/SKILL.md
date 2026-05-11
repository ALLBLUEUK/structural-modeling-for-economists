---
name: replicate
description: 用保存的种子、设定与代码版本复现历史结果。当用户说"复现"、"再跑一遍上次的"、"reproduce"、"对照昨天的结果"时调用。
type: validator
---

# replicate — 历史结果复现

## 触发场景

- "复现上次跑的结果"
- "把 working paper 里那张表的数字重算"
- "为什么这次跟昨天对不上"
- 投稿前的最后一道复现关

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str | |
| `target_artifact` | str | 要复现的产物路径，如 `output/tables/rbc_irf.csv` |
| `reference_seed` | int? | 默认从 `output/checkpoints/<model>_*.json` 中提取 |

## 步骤清单

### Step 1. 锁定 reference

定位历史产物：

- 检查 git 历史 / 时间戳 / SHA
- 提取当时的：seed、参数、求解器版本、spec.md 内容

写一份 `quality_reports/<model>_replicate_<timestamp>_ref.md` 把上述信息固化。

### Step 2. 重置仓库到对应状态

可选两种策略：
- A. `git checkout <commit>` 到当时版本，跑流水线
- B. 把当时的 spec/calibration 临时覆盖到当前版本

推荐 A，更干净。

### Step 3. 跑流水线

调用 `run-pipeline` skill，固定 seed = `reference_seed`。

### Step 4. 数值比对

对每个目标产物：

- 数值差异 `max|x_new - x_ref|`
- 相对差异 `max|x_new - x_ref| / max|x_ref|`

容差：
- 解析稳态：`1e-12`
- 数值稳态：`1e-8`
- IRF / 仿真：`1e-6`
- 蒙特卡洛矩：放宽到 `1e-3` 但需相同 seed

### Step 5. 报告

`quality_reports/<model>_replicate_<timestamp>.md`：

```markdown
# 复现报告 · <model> · <timestamp>

## 参考
- commit: <sha>
- seed: <int>
- date: <ref date>

## 比对
| 产物 | max abs diff | max rel diff | 通过 |
|---|---|---|---|
| `output/tables/rbc_irf.csv` | 3.2e-9 | 1.1e-8 | ✅ |

## 结论
完全复现 / 数值漂移可接受 / 失败（详见……）
```

## 输出契约

- `quality_reports/<model>_replicate_<timestamp>.md`（必产）
- 比对详细数据 → `quality_reports/<model>_replicate_<timestamp>_diff.csv`

## 不允许

- 在比对失败时悄悄调整容差使其通过
- 用不同 seed 比对然后声称复现成功
- 跳过 git 状态记录

## 失败处理

差异超出容差 → 不要立刻怀疑代码错。先排查：
1. 求解器版本是否一致？
2. 浮点数库版本？（OpenBLAS / MKL）
3. 操作系统数学库？
4. 第三方包版本？

把上述都对齐之后还差异，才进入代码层 diff。
