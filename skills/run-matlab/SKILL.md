---
name: run-matlab
description: 包装 MATLAB 调用：执行非 Dynare 类 MATLAB 脚本并解读输出。当用户说"跑 MATLAB"、"run main.m"、"MATLAB 求解"时调用。Dynare 用 run-dynare 不要用本技能。
type: solver
---

# run-matlab — MATLAB 求解调用包装

## 触发场景

- "跑 model/03_solve/<model>/main.m"
- "MATLAB 实现的非 Dynare 模型"（如 Reiter 法、自写线性 RE 求解、扰动包 dynare 之外的实现）
- "MATLAB 报错看不懂"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `m_file` | path | `model/03_solve/<model>/main.m` |
| `nodisplay` | bool | 默认 true（CLI 模式） |
| `extra_paths` | list[path]? | 额外 addpath 目录 |

## 步骤清单

1. 调用 `matlab -nodisplay -nosplash -r "try; run('<m_file>'); catch ME; disp(ME.message); exit(1); end; exit;" 2>&1 | tee logs/<model>_matlab_<ts>.log`。
2. 解析输出：警告、错误、关键变量。
3. 后处理产物保存到 `output/checkpoints/<model>_*.json`（用 `jsonencode`）。
4. 失败时摘录 `ME.identifier` 与 `ME.message`。
5. 调用 `numerics-reviewer` 子 agent。

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `logs/<model>_matlab_<ts>.log` | ✅ | |
| `output/checkpoints/<model>_*.json` | ✅ | |

## 不允许的操作

- 在 `.m` 文件中硬编码盘符路径（用 `fullfile(fileparts(mfilename('fullpath')), ...)`）
- 把求解结果用 `.mat` 提交版本控制（`.gitignore` 已忽略）
- 把 MATLAB 警告当成成功（必须扫描 `Warning:`）

## 失败回退

| 症状 | 处理 |
|---|---|
| `License Manager Error` | 检查 `matlab` 在 PATH 中且 license 有效 |
| `Undefined function` | 检查 `addpath`；可能缺工具箱 |
| 数值不稳定 | 检查矩阵条件数、尝试 SVD 替代直接求逆 |
