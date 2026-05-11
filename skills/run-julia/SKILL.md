---
name: run-julia
description: 包装 Julia 调用：执行 model/03_solve/<model>/run.jl 并解读输出。当用户说"跑 Julia"、"run.jl"、"SequenceJacobian"、"求 HA 模型"时调用。
type: solver
---

# run-julia — Julia 求解调用包装

## 触发场景

- "跑 model/03_solve/<model>/run.jl"
- "用 Julia + SequenceJacobian 求 HA 模型"
- "测试某个 Julia 求解脚本"
- "Julia 报错看不懂"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `jl_file` | path | `model/03_solve/<model>/run.jl` |
| `project` | path? | 默认仓库根 `Project.toml` |
| `precompile` | bool | 默认 true（首次跑） |

## 步骤清单

1. 跑 `bash scripts/run_julia.sh <jl_file>`。
2. 把控制台输出实时镜像到 `logs/<model>_julia_<ts>.log`。
3. 解析输出：策略函数、稳态分布、雅可比、IRF。
4. 失败时摘录关键 Stacktrace 并定位到 `.jl` 行号。
5. 后处理产物保存到 `output/checkpoints/<model>_*.json`（用 `JSON3.write`）。
6. 调用 `numerics-reviewer` 子 agent。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `logs/<model>_julia_<ts>.log` | ✅ | |
| `output/checkpoints/<model>_*.json` | ✅ | 检查点 |

## 不允许的操作

- 在 `run.jl` 中硬编码绝对路径（用 `joinpath(@__DIR__, ...)` 或读 `model/_utils/setup_paths.jl`）
- 跳过 `Pkg.activate()` 导致依赖漂移
- 把 `Float64` 与 `Float32` 混用而不显式转换

## 失败回退

| 症状 | 处理 |
|---|---|
| 包版本不匹配 | `Pkg.instantiate()`；commit `Manifest.toml`（如 spec 要求） |
| OOM | 减小网格或在 `_utils/setup_paths.jl` 调高内存上限 |
| 雅可比缓存与稳态不同步 | 强制重算雅可比并清缓存 |
