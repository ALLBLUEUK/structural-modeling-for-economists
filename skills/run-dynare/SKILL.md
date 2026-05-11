---
name: run-dynare
description: 包装 Dynare 调用：在 MATLAB / Octave 中执行 .mod 文件并解读输出。当用户说"跑 Dynare"、"run mod"、"stoch_simul"、"steady; check;"时调用。
type: solver
---

# run-dynare — Dynare 调用包装

## 触发场景

- "跑 Dynare 把这个 .mod 文件跑一下"
- "stoch_simul 出 IRF"
- "steady; check; 看 BK 条件"
- "Dynare 报错看不懂"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `mod_file` | path | `model/03_solve/<model>/<model>.mod` |
| `engine` | enum | `matlab`（默认）/ `octave` |
| `extra_options` | str? | 透传给 `dynare` 命令的额外选项 |

## 步骤清单

1. 跑 `bash scripts/run_dynare.sh <mod_file>` 让包装脚本处理路径与日志重定向。
2. 把控制台输出实时镜像到 `logs/<model>_dynare_<ts>.log`。
3. 解析输出：BK 条件、稳态向量、`oo_.steady_state`、`oo_.dr.ghx`、IRF。
4. 失败时摘录关键错误段落并定位到 `.mod` 行号。
5. 把后处理产物（policy、IRF）转写为 `output/checkpoints/<model>_*.json`。
6. 调用 `numerics-reviewer` 子 agent 查看诊断。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `logs/<model>_dynare_<ts>.log` | ✅ | 完整日志 |
| `output/checkpoints/<model>_policy.json` | ✅ | 政策矩阵转写 |
| `output/checkpoints/<model>_ss.json` | ✅ | 稳态 |

## 不允许的操作

- 在 `.mod` 注释里包含 `/*`（Dynare 会把它当块注释起点而吞内容）
- 跳过 `steady; check;` 直接 `stoch_simul`
- 把 `oo_` 中的数字直接写报告而不转写检查点

## 失败回退

| 症状 | 处理 |
|---|---|
| `BK condition fails` | 检查 `var` 与 `predetermined_variables`；交 `numerics-reviewer` |
| `Steady state not found` | 写 `steady_state_model` 块或检查 calibration |
| MATLAB 与 Octave 行为差异 | 在 `.mod` 顶部固定 `dynare_version` 并切换到主流引擎 |
