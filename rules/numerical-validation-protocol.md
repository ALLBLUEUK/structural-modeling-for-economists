# Numerical Validation Protocol — 数值验证协议

## 三道闸门

任何对外报告的数值结果必须依次通过下列三道闸门：

### Gate 1. 稳态残差

- 工具：`validate-steady-state` skill
- 容差：`1e-8`（默认；CGE 可放宽到 `1e-6`）
- 落地：`quality_reports/<model>_ss_<timestamp>.md` + checkpoint 中的 `validated: true`
- 失败：停止流水线，交 `math-reviewer`

### Gate 2. 数值稳定

- 工具：`numerics-reviewer` 子 agent + 求解器自带诊断
- 检查：BK 条件、特征值、政策矩阵秩、收敛曲线、迭代次数
- 落地：`quality_reports/<model>_numerics_review_<timestamp>.md`
- 失败：停止流水线，回到 spec 或求解配置

### Gate 3. 复现核对

- 工具：`verifier` 子 agent
- 检查：claim list 中每个数字均能被独立重跑得出
- 容差：稳态 1e-12 / 数值稳态 1e-8 / IRF 1e-6 / 蒙特卡洛矩 1e-3
- 落地：`quality_reports/<model>_verify_<timestamp>.md`
- 失败：禁止把数字写入对外材料

## CGE / 一般均衡专项

CGE 模型还须额外通过：

- **Walras 律校验**：脚本 `scripts/check_walras.py`，剩余方程残差 `< 1e-6`
- **SAM 平衡**：社会账户矩阵行和 = 列和（容差 `1e-9`）

## 不允许

- 提高容差仅为了让模型"通过"。容差由本协议决定，需在 PR / commit 中显式记录调整理由。
- 把 Gate 1 / 2 / 3 任意一道当作"以后再做"。
- 在 Gate 3 失败时先发表后修。

## 例外

唯一可申请放宽容差的场景：

1. 高维异质主体 + 一般均衡：稳态可放宽到 `1e-6`
2. 三阶摄动：政策矩阵元素差异容差 `1e-5`

申请方式：在 `spec.md` 的"求解方法"段显式声明，并在 `quality_reports/` 中记录理由。
