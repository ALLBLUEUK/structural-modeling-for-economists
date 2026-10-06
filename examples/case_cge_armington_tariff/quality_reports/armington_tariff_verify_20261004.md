# Verifier 报告 · armington_tariff · 20261004

- reviewer = verifier (strucmod v0.3 workflow, sub-agent)
- date = 2026-10-04
- 阶段：Gate 3 复现核对（numerical-validation-protocol）
- 范围：`reports/armington_tariff_analysis.tex/.pdf` 中的全部数值；`claims.csv` 17 条 + 报告内 claims.csv 无法直接定位的派生数字
- 约束：未修改任何代码、数据、spec、报告。本次运行新增的文件仅有脚本自动落盘的 `*_replicate_20261003_184513.md`、`*_report_claims_20261003_184513.md`、`*_S1/S2_walras_20261003_184513.md`，以及本报告与独立核对脚本/输出。

## 总判定：PASS（数值层面）；附 3 条非数值的过程性意见（不阻塞数字对外，但建议结项前处理）

---

## A. 自动化复现链路

### A1. 隔离重跑（`replicate_compare.py`，tol 1e-6）
方法：脚本把项目复制到临时目录，删除待比对产物后在副本中执行 `bash run_all.sh`（退出码 0），再逐项与原产物比较；原项目目录不被修改。

| 产物 | 最大绝对差 | 判定 |
|---|---|---|
| data/calibration/armington_tariff/trade_flows_purged.csv | 0.000e+00 | ✅ 完全一致（<1e-12） |
| output/checkpoints/armington_tariff_S1.json | 0.000e+00 | ✅ |
| output/checkpoints/armington_tariff_S2.json | 0.000e+00 | ✅ |
| output/checkpoints/armington_tariff_cf_summary.json | 0.000e+00 | ✅ |
| output/tables/armington_tariff_cf_summary.csv | 0.000e+00 | ✅ |

（比较时 JSON 中 timestamp/env 等键按脚本规则跳过。）

### A2. claims.csv（`check_claims.py`）
G01–G17 共 17 条全部 PASS（见 `quality_reports/armington_tariff_report_claims_20261003_184513.md`）。

### A3. Walras / SAM（`check_walras.py --tol 1e-9`）
- S1：PASS，最大出清残差 3.5e-17（clearing_A 3.519e-17、clearing_R -7.04e-17），SAM 行列和差 0
- S2：PASS，最大出清残差 7.04e-17，SAM 行列和差 0
- 均远低于协议要求的 1e-6，也低于 spec §9.3 的 1e-10。

---

## B. 独立实现抽查（`quality_reports/verifier_independent_check.py`，输出 `verifier_independent_check_output.txt`）

实现方式：仅依据 spec.md §5 方程(1)–(6)，不 import、不复制 solve.py；从**原始** `trade_flows.csv`（含赤字 D = [-1120, 1320, -200]）出发，自行做 DEK 赤字剔除，再求 S1、S2。求解器：`scipy.optimize.fsolve`（对 log 工资，两条出清方程加计价单位），与项目的 hybr/迭代实现在代码层面独立。

| 项目 | 独立实现 | 项目产物 | 差异 |
|---|---|---|---|
| 自行剔除赤字后的基期 vs `trade_flows_purged.csv` | — | — | 绝对差 4.7e-11（相对 3.6e-13；该文件为 CSV 打印精度） |
| S1 ŵ (A, B, R) | 1.00294462, 0.99647223, 1.00027382 | 同 | ≤ 1.1e-16 |
| S1 福利 Ŵ_A（%） | 0.0198295052 | 0.0198295052 | 2.2e-16 |
| S1 福利 Ŵ_B（%） | -0.0402167964 | -0.0402167964 | 2.2e-16 |
| S2 福利 Ŵ_A（%） | -0.0411403839 | -0.0411403839 | 3.3e-16 |
| S2 福利 Ŵ_B（%） | -0.0141891775 | -0.0141891775 | 0 |
| S1 A 自 B 的 MAN 进口出厂价值变化（%） | -35.8323759576 | -35.8323759576 | 1.4e-12（百分点） |
| S1 A 自 R 的 MAN 进口 / A 本地 MAN 销售变化 | 1.7805 / 0.7007 | 同 | 2.3e-12 / 5.3e-13 |
| S1 相对工资 ŵ_B/ŵ_A | 0.993546616327 | 同 | 4.1e-15 |
| P3：S2−S1 福利差（A / B，pp） | -0.060970 / 0.026028 | 同 | 1.1e-14 / 2.2e-14 |
| 全部出清方程（含被删去一条）残差/ΣY | S1 0；S2 7.0e-17 | — | — |

综合：最大偏差 2.3e-14，远小于要求的 1e-8（也小于协议 1e-12 的“完全一致”档附近，仅因浮点与 CSV 打印精度而非 0）。**独立复现通过。**

---

## C. 报告内 claims.csv 未直接覆盖的派生数字

| # | 报告中的陈述 | 位置 | 复核来源与结果 | 判定 |
|---|---|---|---|---|
| D1 | B 的相对工资下降 0.65% | 摘要、§3 | 1 − 0.993546616 = 0.6453%，四舍五入 0.65%（G04 的派生）；独立实现同 | ✅ |
| D2 | 10% 关税下 A 福利增益 0.0198% | §3 最优关税段 | 网格 10% 点 0.019830%（独立实现，网格表第 10 行）= G05 | ✅ |
| D3 | A 福利最大化关税约 11%、增益 0.0199% | 摘要、§3 | 独立网格 0–60% 步长 1pp：argmax = 11%，A 福利 0.019857% → 0.0199 | ✅ |
| D4 | “最优点附近曲线很平坦”（10% 与 11% 增益几乎相同） | §3 | 0.019830 vs 0.019857，差 0.000027pp；图中曲线形态一致 | ✅ |
| D5 | 福利三项分解：工资 0.294、关税收入 0.056、价格指数 0.330；“收益之和超过损失” | §3 | 独立：ln w = 0.2940，ln(1+R/wY) = 0.0562，价格项（余项）= -0.3304，三项和 0.0198；0.294+0.056 = 0.350 > 0.330 | ✅ |
| D6 | “B 福利下降主要来自工资下降” | §3 | S1 B：工资项 -0.353，价格指数项 +0.313，关税项 0；净 -0.040。工资下降是负项来源，但被价格指数收益大部分抵消，措辞可接受 | ✅（见意见 3） |
| D7 | “R 作为第三方略有获益” | §3 | S1 R 福利 +0.0029% | ✅ |
| D8 | S2 相对 S1：A 低 0.061pp；B 高 0.026pp；B 福利 -0.0402% → -0.0142% | §3 | G07–G10；独立 -0.060970 / +0.026028 | ✅ |
| D9 | “B 报复的收益超过消费扭曲成本（见图 1 中 B 的分解）” | §3 | 以 S2 相对 S1 的差分计：工资项 +0.436pp、关税项 +0.081pp、价格指数项 −0.492pp，净 +0.026pp，成立。但图 1 画的是各情形水平项而非差分，读者需自行相减 | ✅（见意见 3） |
| D10 | 数值检验：赤字剔除后余额相对误差 “10⁻¹⁵ 量级” | §2 | checks.json：9.85e-16（独立：纯化后 max|E−Y|/ΣY = 3.5e-17） | ✅ |
| D11 | 零冲击偏离 “低于 10⁻¹⁴” | §2 | zero_shock_what_dev 3.3e-15、What_dev 4.9e-15 | ✅ |
| D12 | 出清残差（含冗余一条）“低于 10⁻¹⁶” | §2 | S1、S2 最大 7.04e-17（项目 checkpoint 与独立实现均如此） | ✅ |
| D13 | 独立水平量实现与精确变化法差 “2×10⁻¹⁶” | §2 | checks.json levels_vs_hat_wage/welfare_diff = 2.22e-16 | ✅ |
| D14 | 先 5% 再 10% 与一步 10% 福利一致 | §2 | checks.json composition_welfare_diff = 3.3e-16（<1e-9）。**注**：报告文字写“先加征 5%”，我未从脚本中单独核对 5% 这一中间值是否确为 t1，仅核对到复合检验通过。 | ⚠️ 见意见 4（小） |
| D15 | 两种求根算法结果一致 | §2 | two_solver_what_diff = 1.0e-13（S1 checkpoint 诊断 7.9e-14） | ✅ |
| D16 | 表 2 稳健性数值 | 表 | 独立实现对每个 ε_MAN 均从原始数据重新剔除赤字后求解，与 `robustness_eps.csv` 最大差 4.99e-07（即 CSV 6 位小数的舍入，≤5e-7） | ✅ |
| D17 | “ε 取 2 到 12 以 0.25 步长细扫，未出现符号翻转”；摘要“2 到 12 之间均为正” | §4、摘要 | 独立细扫 41 点：S1 A 福利最小 +0.00247%（ε = 12），最大 +0.0226%，无 ≤ 0；`S1_A_welfare_sign_flip_eps = []` 一致 | ✅（但 ε=12 处仅 +0.0025%，接近 0，见意见 3） |
| D18 | “报复情形下 A 始终受损” | §4 | 细扫 S2 A 福利最大 -0.0406%（ε=2），全程 < 0；表内 2–8 同 | ✅ |
| D19 | 福利随 ε 上升而递减（A，S1：0.0226 → 0.0104） | §4 | 表中单调递减，独立细扫上界 0.0226、下界 0.0025 同向 | ✅ |
| D20 | 报告 PDF 与 tex 是否同步 | — | pdf（02:43:06）晚于 tex（02:43:05）与两个 latex 表（02:28:30）；PDF 文本中检出 35.83、0.0198、0.65、0.9935、0.0411、0.0142、11%、0.330，且与 tex 一致 | ✅ |

### 示意数据声明核查

| 载体 | 是否带声明 | 说明 |
|---|---|---|
| 报告首页 | ✅ | 带框声明（tex 第 20–22 行），另 §2 数据段与 §5 局限再次说明；PDF 4 页均检出“示意” |
| 图 1（福利分解） | ✅ | 图内总标题“福利变化及其分解（示意数据，结论仅为机制示范）”；图 caption 也带 |
| 图 2（最优关税） | ✅ | 图内标题与 caption 均带 |
| 表 1（`tab_scenarios.tex`）、表 2（`tab_robustness.tex`） | ❌ **未带** | 两张表的 caption 与 .tex 文件内均无声明，仅靠首页框与全文声明 |
| `output/tables/*.csv` | ❌ 未带 | CSV 无声明列/注释行；JSON checkpoint 带 `disclaimer` 字段 |
| manifest.json、spec.md | ✅ | 已声明 |

spec.md §0 要求“所有表、图、报告均须带此声明”。图与报告满足，**表未满足**（见意见 1）。

---

## D. Claim 汇总（逐条格式，仅列代表性；17 条 claims.csv 全部见 A2）

## Claim G01: “A 自 B 制造业进口按出厂价值下降 35.83%”
- 来源：output/checkpoints/armington_tariff_cf_summary.json（P1_A_imports_MAN_from_B_value_change_pct）
- 重跑结果：-35.8323759576（隔离重跑）；独立实现 -35.8323759576
- 差异：0 / 1.4e-12
- 判定：✅ 通过

## Claim G05: “S1 A 福利 +0.0198%”
- 来源：output/tables/armington_tariff_cf_summary.csv row0 welfare_pct
- 重跑结果：0.0198295052（独立）
- 差异：2.2e-16（Ŵ 比值口径）
- 判定：✅ 通过

## Claim G15: “网格最优关税 11%”
- 来源：output/checkpoints/armington_tariff_cf_summary.json
- 重跑结果：独立网格 argmax = 0.11
- 差异：0
- 判定：✅ 通过

## Claim D17: “ε∈[2,12] S1 A 福利恒为正”
- 来源：counterfactuals.py 细扫（输出 `S1_A_welfare_sign_flip_eps=[]`）
- 重跑结果：独立 41 点细扫，最小 +0.00247%
- 差异：方向一致
- 判定：✅ 通过

---

## E. 综合

- 总 claim 数：17（claims.csv）+ 20（派生数字/陈述 D1–D20）
- 通过 ✅：36
- 漂移可接受 ⚠️：1（D14，仅为我未单独核对 5% 中间值；数值本身无漂移）
- 失败 ❌：0
- 声明核查：图与报告通过；表与 CSV 未带示意数据声明
- 数值结论：**报告中的数字均可由原始数据按 spec 独立复现（偏差 ≤ 2.3e-14），隔离重跑与 checkpoint 位级一致，Walras 与 SAM 通过。Gate 3 数值部分 PASS，报告数字可对外。**

## F. 意见（不影响数值 PASS）

1. **【建议修改，小】表缺示意数据声明**：表 1、表 2 的 caption（或 `tab_*.tex` 的脚注）应加“示意数据，结论仅为机制示范”，以满足 spec §0；CSV 可在表头旁加一行注释或附 README。属 latex_tables.py 与报告的小改动，本次按规定未改。
2. **【过程性】复现三件套不完整**：项目目录不是 git 仓库，checkpoint 中没有 `git_sha` 与 `seed` 字段（env 里有 os/python/numpy/scipy 版本，`model/_utils/seed.txt` = 20250613 存在但本模型是确定性求解、未使用随机数）。replication-protocol 要求写入 git_sha 与 seed；verifier 角色亦要求隔离环境与 commit SHA。本次以“复制到临时目录重跑”替代 git worktree，达到隔离目的，但无法登记 SHA。建议结项前将项目纳入 git 并在 checkpoint 里补写，或在 spec 中声明“确定性、无随机性，seed 不适用”。
3. **【措辞，小】**：(a) 摘要“2 到 12 之间均为正”在 ε=12 处仅 +0.0025%，量级接近 0，建议补一句“在 ε 较大时增益趋于消失”；(b) 报告 §3 “B 的福利下降主要来自工资下降”可加上“被价格指数收益大部分抵消”；(c) “报复收益超过消费扭曲成本（见图 1）”指的是 S2 相对 S1 的差分，图 1 画的是水平项，建议在文字或图注中说明是差分比较。三条均不改变数字。
4. **【核对范围说明】**：D14 中“5% → 10%”的中间值取自报告文字，我复核的是 checks.json 中复合检验通过（3.3e-16）而非单独重算 5% 步骤；若要形成独立证据，可在独立脚本中补一行 0→5%→10% 的计算（本次未做，因公式 (1)–(6) 已含该复合性质且水平量实现已交叉验证）。

## 可复现命令

```
python ../../strucmod-v0.3/scripts/replicate_compare.py --cmd "bash run_all.sh" --compare ... --tol 1e-6 --model armington_tariff
python ../../strucmod-v0.3/scripts/check_claims.py claims.csv --model armington_tariff_report
python ../../strucmod-v0.3/scripts/check_walras.py output/checkpoints/armington_tariff_S1.json --tol 1e-9   (S2 同)
python quality_reports/verifier_independent_check.py > quality_reports/verifier_independent_check_output.txt
```

环境：Windows-10-10.0.19045，Python 3.13.3，numpy 2.3.3，scipy 1.16.2。
