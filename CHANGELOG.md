# 更新日志

## v0.3.0 · 2026-10-04

本版本补齐中期检查时列为“下一阶段”的异质主体与 CGE 两个方向，并新增自动复现与文稿数字核对工具。每项新功能都在 `结项/工作流验收/` 中按完整工作流跑过一个验收案例，评审记录、运行日志、复现报告均留档。

### 新增

- 异质主体通用求解模板 `templates/master-ha-template.py`（Python）
  - 内生网格法（EGM）求家庭问题；Young (2010) 彩票法构造转移矩阵并直接求平稳分布
  - Rouwenhorst（默认）与 Tauchen 两种收入离散化，并报告离散化质量
  - Brent 法求资本市场出清，按借贷下限 φ(r) 每步重建资产网格；30 点唯一性扫描
  - 检查点输出出清残差、资源约束残差、Euler 误差、网格上端质量、分布收敛状态；任何一项不达标即 `validated = false`
  - 验收案例：Aiyagari 借贷约束比较静态（`case_ha_aiyagari_borrowing`）
- 免 GAMS 授权的 CGE 通用求解模板 `templates/master-cge-template.py`（Python）
  - 多地区多部门 Armington 模型，Dekle–Eaton–Kortum 精确变化法；含税支出份额、关税收入回流、福利分解
  - 按 DEK (2008) 剔除基期赤字，使结果不依赖计价单位
  - 内置 11 项数值验证：剔赤字余额、零冲击（扰动初值）、Walras（全部出清方程）、计价单位中性、独立水平量求解器交叉核对、复合检验、就业加总、福利分解可加、双求根器一致
  - 输出与 `scripts/check_walras.py` 兼容
  - 验收案例：示意数据下的单边关税与对等报复（`case_cge_armington_tariff`）
- `scripts/replicate_compare.py`：把项目复制到临时目录、删除待比对产物后重跑，逐项数值比对，生成复现报告（verifier 的自动化部分）
- `scripts/check_claims.py`：按 `claims.csv` 逐条核对文稿中出现的数字能否由数据源复算得到（numerical-validation-protocol Gate 3）
  - 验收：对 v0.2 示范论文的核对发现两处数字错误（实际利率 0.522 应为 0.518；年化值 0.176 应为 0.178），已在勘误版中更正

### 修复

- `scripts/check_steady_state.py`：求解器已判 `validated = false` 时，不再仅凭残差改写为 true
- `scripts/check_walras.py`：报告文件名加入检查点名，避免同一秒内多个情形的报告互相覆盖

### 在验收中发现并修复的问题（留档于各案例 `quality_reports/` 与 `_superseded_*`）

- HA：平稳分布纯迭代在 β(1+r) 趋近 1 时 10 万次不收敛且未报错，改为线性方程组直接求解，并把收敛纳入 `validated`
- HA：7 点 Tauchen 离散使对数收入方差高估 37%，比较静态幅度被高估约 35%，默认改用 Rouwenhorst，离散化阈值纳入 `validated`
- HA：极限检验中 Brent 精度不足导致出清残差 1.2e-8，求根精度提高到 1e-15（未放宽容差）
- CGE：`hybr` 的 success 标记在接近机器精度时误报失败，改以方程残差判定
- CGE：原 ACR 解析检验在单部门、零赤字下为代数恒等式，不能检验求解器，降级为展示项，新增独立水平量实现交叉核对

### 已知局限

- HA 模板目前只求稳态，不含过渡路径与 sequence-space 雅可比；Julia 模板 `master-ha-template.jl` 仍为脚手架
- CGE 模板不含投入产出联系与多层嵌套；GTAP 数据需用户自行获得授权
- 中型 DSGE（Smets–Wouters 类）示范仍未完成

## v0.2.0 · 2026-05-11

- 首个公开版本：32 项功能模块、7 个 AI 评审专家、6 项科研规范；Claude Code 插件与 Codex CLI / Cursor / Aider / Windsurf / GitHub Copilot 适配；三方程新凯恩斯示范论文
