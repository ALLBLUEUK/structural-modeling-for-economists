# Replication Protocol — 复现协议

## 三件套

每个模型的每次"对外发布"（论文版本、教学讲义、汇报材料）必须保存：

1. **代码版本**：`git rev-parse HEAD` 写入 checkpoint
2. **种子**：从 `model/_utils/seed.txt` 读取，写入 checkpoint
3. **环境**：求解器版本、语言版本、关键包版本，写入 checkpoint

具体字段：

```json
{
  "model": "<model_name>",
  "git_sha": "abc1234",
  "seed": 20250613,
  "env": {
    "os": "Windows 10",
    "language": "MATLAB R2023a",
    "solver": "Dynare 6.1",
    "blas": "MKL 2023.2"
  },
  "timestamp": "2026-05-11T15:30:00Z"
}
```

## seed 管理

- 项目级单一种子：`model/_utils/seed.txt`，整型，**不**入代码硬编码。
- 模型级覆盖：仅在 `spec.md` 的"求解方法"段显式声明，并附理由。
- 蒙特卡洛子任务：在 `spec.md` 中登记派生 seed 的算法（如 `seed_i = base + i`）。

## 复现入口

- 用户角度：`bash scripts/run_pipeline.sh <model_name>`
- agent 角度：`replicate` skill

## 容差

| 产物 | 容差 |
|---|---|
| 解析稳态 | 1e-12 |
| 数值稳态 | 1e-8 |
| 政策矩阵 | 1e-10 |
| IRF / 仿真 | 1e-6 |
| 蒙特卡洛矩 | 1e-3（同 seed） |
| 蒙特卡洛矩 | 由 `spec.md` 声明（不同 seed） |

## 失败定位顺序

发现差异时，按下列顺序排查：

1. git 状态：是否在同一 commit
2. 种子：是否一致
3. 求解器版本
4. 浮点库（OpenBLAS / MKL）
5. 操作系统数学库
6. 第三方包版本
7. 编译器优化等级
8. 才是代码 bug

## 不允许

- 在 git 工作区有未提交修改的状态下发布数字
- 把 seed 写死在脚本中
- 用不同 seed 比对然后声称"基本一致"
- 把"无法复现"包装成"数值漂移可接受"
