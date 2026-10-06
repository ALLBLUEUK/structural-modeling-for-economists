# Verifier 报告 · aiyagari_borrowing · 20261004

- reviewer = verifier (strucmod v0.3 workflow, sub-agent)
- date = 2026-10-04
- 模式：full（重跑整条流水线）；Gate 3 复现核对
- 局限声明（按 verifier.md「不允许」条款如实记录）：
  1. 项目目录不是 git 仓库，无法记录 commit SHA、也无法建 worktree 隔离环境；重跑在原目录就地进行（run_all.sh 会覆盖 output/）。因此「新旧一致」成立的前提是重跑前产物即为上次流水线产物；数字由「固定参数 + 无随机成分（EGM、Brent、Young 彩票法均为确定性算法）」保证可复现，seed 无影响。
  2. 复现脚本落盘的时间戳（20261003_18xxxx）来自本机系统时钟，与任务日期 2026-10-04 差一天，不影响数值结论。
  3. 环境：Windows 10，Python 3.13（C:\Python313），本次 vs 上次同机同环境，未做跨平台比对。

## A. 流水线重跑（replicate_compare.py，tol = 1e-6）

| 对象 | max abs diff | 判定 |
|---|---|---|
| output/checkpoints/aiyagari_borrowing_baseline_ss.json | 0.000e+00 | ✅ 完全一致 |
| output/checkpoints/aiyagari_borrowing_b8_ss.json | 0.000e+00 | ✅ 完全一致 |
| output/tables/aiyagari_borrowing_comparative_statics.csv | 0.000e+00 | ✅ 完全一致 |
| output/tables/aiyagari_borrowing_robustness.csv | 0.000e+00 | ✅ 完全一致 |

复现记录：quality_reports/aiyagari_borrowing_replicate_20261003_184544.md

## B. claims.csv 核对（check_claims.py）

H01-H18 共 18 条，全部 PASS（报告值与 output/tables 对应单元格在给定舍入下一致）。记录：quality_reports/aiyagari_borrowing_report_claims_20261003_184544.md

备注：H18（Euler 误差 log10 均值，文中 -7.56）在 claims.csv 以 7.56 对绝对值、abs 容差 = 1 比较；该容差偏松（真实值 -7.5622，取整后 7.56 吻合，但容差本身不严）。建议后续收紧为 0.005。这不影响本次结论（实际差 0.002）。

## C. 独立复现（不 import / 不复制 solve.py）

脚本：quality_reports/verifier_independent_check.py；输出：quality_reports/verifier_independent_check_output.txt

实现：自写 Rouwenhorst（n_z=7）、自写 EGM（n_a=250、幂次 3 网格、a_max=80，与原版 400 点/幂次 2/a_max=100 刻意不同）、自写 Young 彩票法 + 幂迭代求平稳分布、brentq 解出清；φ(r)=min{b, w z_min/r}（r≤0 时为 b）。

| 情形 | 量 | 独立实现 | solve.py（表） | 绝对差 |
|---|---|---|---|---|
| b = 0 | r | 3.5786% | 3.5796% | 1.0e-5（即 1.0e-4 个百分点） |
| b = 0 | 储蓄率 | 24.873% | 24.871% | 0.002 个百分点 |
| b = 0 | K/Y | 3.1092 | 3.1089 | 3e-4 |
| b = 8 | r | 3.8004% | 3.8018% | 1.4e-5 |
| b = 8 | 储蓄率 | 24.406% | 24.403% | 0.003 个百分点 |
| b = 8 | K/Y | 3.0507 | 3.0504 | 3e-4 |

判定：✅ 通过。r 的差异约 1e-5，远小于 1e-3 门槛。差异来源：资产网格密度/幂次/上界不同，EGM 线性插值误差（粗网格 250 点）；两侧差异方向一致，b=0 与 b=8 的 r 差（0.2218 个百分点）与表中 0.2222 吻合，说明比较静态不依赖网格。
过程说明：独立脚本第一版在 b=8 时网格起点写成 0 而非 −φ（我方 bug，b=0 时恰好无影响），b=8 出现 Brent 同号报错；修正为 a ∈ [−φ, a_max] 后得到上表，不涉及被核对的代码。

## D. 报告中 claims.csv 未直接覆盖的派生数字

数据源：output/tables/aiyagari_borrowing_comparative_statics.csv、aiyagari_borrowing_robustness.csv（逐项由本人重新计算）

| 报告表述（位置） | 重算 | 判定 |
|---|---|---|
| 「利率上升 0.222 个百分点」(b: 0→8) | 3.801825 − 3.579629 = 0.222196 | ✅ |
| 「储蓄率下降 0.47 个百分点」 | 24.403005 − 24.871263 = −0.468258 → 0.47 | ✅ |
| 「K/Y 从 3.109 降至 3.050」 | 3.108908 → 3.050376 | ✅ |
| 「且关系单调」 | b=0,0.5,1,2,4,8 上 r 严格上升、s 与 K/Y 严格下降 | ✅ |
| 「受约束比例 2.97→0.26」「Gini 0.474→0.889」 | 与表一致（且随 b 单调） | ✅ |
| 「Tauchen 下利率低估约 0.21 个百分点」 | 3.371430 − 3.579629 = −0.208199 → 0.21 | ✅ |
| 「Tauchen 夸大比较静态幅度」 | Tauchen 下 b:0→8 的 r 变动 0.2964 > Rouwenhorst 0.2222；储蓄率变动 −0.643 vs −0.468 | ✅ |
| 「n_z 7→15，利率变化不超过 0.002 个百分点」 | b=0/2/8 分别 0.00167/0.00158/0.00146，最大 0.00167 ≤ 0.002 | ✅ |
| 「储蓄率变化不超过 0.004 个百分点」 | 分别 0.00358/0.00334/0.00301，最大 0.00358 ≤ 0.004 | ✅ |
| 极限检验 r=4.167%、s=23.67% | r − 4.1667 = −7.0e-5 个百分点（阈值 1e-4 为 r 的绝对量，即 0.01 个百分点）；s − 23.667 = +1.4e-4 个百分点（阈值 0.1） | ✅ |

小提示（非错误）：「0.002/0.004」是上界且余量较小（最大值 0.00167/0.00358），措辞「不超过」成立；若后续改动网格需复核。

## 综合

- 总 claim 数：18（claims.csv）+ 10（派生项）+ 6（独立复现）= 34
- 通过：34；漂移可接受：0；失败：0
- 流水线重跑 max|diff| = 0（完全一致，优于 1e-12 档）
- 结论：**PASS**，报告数字均有产物背书且可独立复现；可对外。
- 待办（不阻塞）：(1) 项目纳入 git 并记录 SHA，以满足 replication-protocol 三件套；(2) H18 容差收紧；(3) 复现脚本时间戳与系统时钟对齐。
