# 复现核对报告 · nk_three_eq · 20261006_072905

- 方法：复制项目到临时目录，删除待比对产物后重跑命令，与原产物逐项比较
- 容差：1e-06（replication-protocol）
- 结论：✅ 复现一致

## 命令

- `python code/nk_three_eq/nk_solve.py` → 退出码 0
- `python code/nk_three_eq/nk_simulate.py` → 退出码 0

## 产物比对

| 产物 | 最大绝对差 | 结果 | 说明 |
|---|---|---|---|
| `results/checkpoints/nk_policy.json` | 0.000e+00 | ✅ |  |
| `results/checkpoints/nk_ss.json` | 0.000e+00 | ✅ |  |
| `results/checkpoints/nk_irf_eps_m.json` | 0.000e+00 | ✅ |  |
| `results/tables/nk_irf_eps_m.csv` | 0.000e+00 | ✅ |  |
