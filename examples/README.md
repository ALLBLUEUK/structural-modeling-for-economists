# strucmod v0.3 工作流验收总览

> 日期：2026-10-04（2026-10-06 更新）｜ 项目：AI多工具协同赋能研究生结构建模与动态模拟的研究与实践（AI+科研）｜ 负责人：贾宁远

本目录是 strucmod v0.3 新功能的验收记录。每项新开发的功能都用一个案例按工作流完整跑一遍，每道闸门都由插件内置的 AI 评审专家独立把关；评审意见、失败记录、被取代的旧结果（`_superseded_*`）全部保留，没有删改。

## 一、三个验收案例

| 案例 | 验收的 v0.3 功能 | 研究问题 | 结论 |
|---|---|---|---|
| `case_ha_aiyagari_borrowing/` | 异质主体求解模板 `master-ha-template.py` | Aiyagari 模型中借贷限额松紧对均衡利率与储蓄率的影响 | 全部闸门通过 |
| `case_cge_armington_tariff/` | 免 GAMS 授权 CGE 模板 `master-cge-template.py` | 单边 10% 关税与对等报复的贸易与福利效应（示意数据） | 全部闸门通过 |
| `case_nk_replicate/` | 复现脚本 `replicate_compare.py`、数字核对脚本 `check_claims.py` | 对中期示范论文的复现核对 | 结果可复现；发现并更正正文两处数字错误 |

## 二、每个案例走过的闸门

| 闸门 | 执行者 | 异质主体 | CGE | 新凯恩斯 |
|---|---|---|---|---|
| 设定评审（经济逻辑） | model-reviewer | 修改后通过，复核通过 | 修改后通过，复核通过 | — |
| 设定评审（数学一致性） | math-reviewer | 修改后通过，复核通过 | 修改后通过，复核通过 | — |
| 数值稳定性 | numerics-reviewer | 修改后通过，复核通过 | 修改后通过，复核通过 | — |
| 代码质量 | code-reviewer | 修改后通过，复核通过 | 修改后通过，复核通过 | — |
| 一键复现比对 | `replicate_compare.py` | 8 个产物差 0 | 8 个产物差 0 | 4 个产物差 0 |
| 文稿数字核对 | `check_claims.py` | 19 条全部一致 | 25 条全部一致 | 15 条：首轮 2 条不一致，更正后全部一致 |
| 复现核对（含独立实现） | verifier | 通过（独立实现利率差约 1e-5） | 通过（独立实现差 ≤ 2.3e-14） | 通过（待定系数法独立求解） |
| 写作规范 | paper-reviewer | 需修改，复核通过 | 需修改，两轮复核通过 | — |

## 三、工作流在验收中发现并纠正的问题（举要）

这些问题都是在流程中被 AI 评审专家或自动检查发现的，修正过程和原始失败结果都有留档：

1. 设定阶段：评审指出 CGE 设定中“报复后两国福利都下降”的先验不是定理；运行结果证实报复反而改善了报复方的福利。若不经评审，正确的代码会被误判为错误。
2. 数值阶段：
   - 异质主体的财富分布在收入风险趋于零时 10 万次迭代仍未收敛，而旧代码没有报错。分布没收敛时，“受约束家庭比例”被算成 6.3%，正确值是 0.24%。
   - 7 点 Tauchen 离散使收入方差高估 37%，比较静态幅度被高估约 35%。
3. 代码阶段：发现插件原有脚本 `check_steady_state.py` 会把求解器判为失败的结果改写为通过；`check_walras.py` 在同一秒内生成的多份报告会互相覆盖。两处均已修复。
4. 验证设计：评审指出原 ACR 解析检验是代数恒等式，即使工资不是均衡解也成立，因此检验不到求解器。已改为独立实现交叉核对。
5. 成文阶段：
   - 中期示范论文正文有两处数字错误（0.522 应为 0.518；0.176 应为 0.178），v0.3 的数字核对工具首次运行即发现。
   - 写作评审在两份新报告中共提出 25 项修改意见，包括过度推论、无依据论断、图表不自含等，均已修订。

## 四、目录结构（以异质主体案例为例）

```
case_ha_aiyagari_borrowing/
├── model/01_setup/…/spec.md、equations.tex      模型设定（含评审修订记录，v1 至 v3）
├── model/02_calibrate/…/calibration.csv          参数与来源
├── model/03_solve/…/solve.py 等                  求解、表图、LaTeX 表
├── output/checkpoints、tables、figures、latex     结果（_superseded_v* 为被取代的旧结果）
├── quality_reports/                              全部评审报告、复现与数字核对报告、独立实现脚本
├── logs/                                         运行日志；logs/sessions/ 为工作流运行记录
├── reports/…_analysis.pdf                        分析报告
├── claims.csv                                    报告数字核对清单
└── run_all.sh                                    一键复现入口
```

## 五、如何复现

在任一案例目录下运行 `bash run_all.sh`（需 Python 3.10+、numpy、scipy、matplotlib）；或用插件脚本自动比对：

```bash
python ../../strucmod-v0.3/scripts/replicate_compare.py --cmd "bash run_all.sh" --compare <产物路径> ...
python ../../strucmod-v0.3/scripts/check_claims.py claims.csv
```

## 六、说明

- 工作流由 Claude Code 统一调度，各评审专家为按插件角色定义独立运行的 AI 评审程序。评审意见均由评审专家独立给出，并已原样保留。
- CGE 案例使用示意数据，结论仅为机制示范。
- 本目录连同插件 v0.3 已于 2026 年 10 月 6 日在 GitHub 发布（https://github.com/ALLBLUEUK/structural-modeling-for-economists/releases/tag/v0.3.0），在仓库中位于 examples 目录，对应提交 1dbf09c。各检查点本身没有记录提交号，复现以该发布版本为准。
- 2026 年 10 月 6 日按最终状态重新运行了三个案例的复现比对，全部一致。
