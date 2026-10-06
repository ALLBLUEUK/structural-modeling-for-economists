# 文稿数字核对报告 · nk_three_eq · 20261003_182218

- claims 文件：`claims.csv`
- 核对条数：15；不一致：2
- 结论：❌ 存在不一致，禁止对外发布（numerical-validation-protocol Gate 3）

| 编号 | 文稿 | 文稿数字 | 复算 | 结果 | 说明 |
|---|---|---|---|---|---|
| R01 | `paper/sections/05_results.tex` | 0.259 | 0.259 | ✅ PASS | 产出当期下降（%） |
| R02 | `paper/sections/05_results.tex` | 0.352 | 0.352 | ✅ PASS | 通胀当期下降（年化 pp） |
| R03 | `paper/sections/05_results.tex` | 0.342 | 0.342 | ✅ PASS | 名义利率当期上升（年化 pp） |
| R04 | `paper/sections/05_results.tex` | 0.522 | 0.518 | ❌ FAIL | 数据源复算为 0.5182，按文稿精度应为 0.518 |
| R05 | `paper/sections/05_results.tex` | 0.172 | 0.172 | ✅ PASS | 菲利普斯曲线斜率 κ |
| R06 | `paper/sections/05_results.tex` | 0.044 | 0.044 | ✅ PASS | κ·y（季度 %）；factor = κ |
| R07 | `paper/sections/05_results.tex` | 0.176 | 0.178 | ❌ FAIL | 数据源复算为 0.177915，按文稿精度应为 0.178 |
| A01 | `paper/main.tex` | 0.26 | 0.26 | ✅ PASS | 摘要：产出下降 |
| A02 | `paper/main.tex` | 0.35 | 0.35 | ✅ PASS | 摘要：通胀下降 |
| A03 | `paper/main.tex` | 0.52 | 0.52 | ✅ PASS | 摘要：实际利率上升 |
| K01 | `paper/sections/07_conclusion.tex` | 0.26 | 0.26 | ✅ PASS | 结论：产出下降 |
| K02 | `paper/sections/07_conclusion.tex` | 0.35 | 0.35 | ✅ PASS | 结论：通胀下降 |
| K03 | `paper/sections/07_conclusion.tex` | 0.52 | 0.52 | ✅ PASS | 结论：实际利率上升 |
| M01 | `paper/sections/03_calibration.tex` | 0.1717 | 0.1717 | ✅ PASS | 校准节：κ |
| M02 | `paper/appendix/A_proofs.tex` | 0.172 | 0.172 | ✅ PASS | 附录 A：κ |
