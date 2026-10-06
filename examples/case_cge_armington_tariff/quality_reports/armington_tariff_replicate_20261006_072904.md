# 复现核对报告 · armington_tariff · 20261006_072904

- 方法：复制项目到临时目录，删除待比对产物后重跑命令，与原产物逐项比较
- 容差：1e-06（replication-protocol）
- 结论：✅ 复现一致

## 命令

- `bash run_all.sh` → 退出码 0

## 产物比对

| 产物 | 最大绝对差 | 结果 | 说明 |
|---|---|---|---|
| `data/calibration/armington_tariff/trade_flows_purged.csv` | 0.000e+00 | ✅ |  |
| `output/checkpoints/armington_tariff_checks.json` | 0.000e+00 | ✅ |  |
| `output/checkpoints/armington_tariff_S1.json` | 0.000e+00 | ✅ |  |
| `output/checkpoints/armington_tariff_S2.json` | 0.000e+00 | ✅ |  |
| `output/checkpoints/armington_tariff_cf_summary.json` | 0.000e+00 | ✅ |  |
| `output/tables/armington_tariff_cf_summary.csv` | 0.000e+00 | ✅ |  |
| `output/tables/armington_tariff_robustness_eps.csv` | 0.000e+00 | ✅ |  |
| `output/tables/armington_tariff_optimal_tariff_grid.csv` | 0.000e+00 | ✅ |  |
