# 复现核对报告 · aiyagari_borrowing · 20261003_184544

- 方法：复制项目到临时目录，删除待比对产物后重跑命令，与原产物逐项比较
- 容差：1e-06（replication-protocol）
- 结论：✅ 复现一致

## 命令

- `bash run_all.sh` → 退出码 0

## 产物比对

| 产物 | 最大绝对差 | 结果 | 说明 |
|---|---|---|---|
| `output/checkpoints/aiyagari_borrowing_baseline_ss.json` | 0.000e+00 | ✅ |  |
| `output/checkpoints/aiyagari_borrowing_b8_ss.json` | 0.000e+00 | ✅ |  |
| `output/tables/aiyagari_borrowing_comparative_statics.csv` | 0.000e+00 | ✅ |  |
| `output/tables/aiyagari_borrowing_robustness.csv` | 0.000e+00 | ✅ |  |
