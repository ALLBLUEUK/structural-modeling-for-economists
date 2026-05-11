# 求解器速查表 / Solver Cheatsheet

按"模型类别 × 解法类别"给出推荐工具与注意事项。

## DSGE / 中等规模新凯恩斯类

| 解法 | 工具 | 适用 | 注意 |
|---|---|---|---|
| 一阶摄动 | Dynare 6.x | 局部分析、IRF、估计 | 需 Blanchard-Kahn 条件 |
| 二/三阶摄动 | Dynare `order=2/3` | 风险溢价、福利 | 修正项数值稳定性 |
| 投影法 | Julia `Dolo.jl` | 大冲击 / 非线性 | 维度灾难 |
| Sequence-space | Julia `SequenceJacobian.jl` | 完美预见 / 外生冲击 | 限于线性化邻域 |

## 异质主体（HA）

| 解法 | 工具 | 适用 | 注意 |
|---|---|---|---|
| Aiyagari 稳态 | Julia + EGM (`QuantEcon.jl`) | 不完全市场稳态 | 资产网格细化 |
| Krusell-Smith | Julia + 仿真 | 总量随机 + 异质 | 学习收敛慢 |
| Sequence-space | Julia `SSJ` (Auclert et al.) | HA-DSGE | 雅可比缓存 |
| Reiter | MATLAB | 频率域分析 | 过时但仍有人用 |

## 动态规划（DP）

| 解法 | 工具 | 适用 | 注意 |
|---|---|---|---|
| VFI | Julia / Python (`quantecon`) | 简单状态空间 | 慢但稳 |
| PFI | 同上 | 平滑策略 | 收敛快 |
| EGM | 同上 | 凸消费-储蓄类 | 推导特殊化 |
| Chebyshev 投影 | Julia | 平滑值函数 | 选基函数 |

## CGE / GTAP

| 解法 | 工具 | 适用 | 注意 |
|---|---|---|---|
| 静态 CGE | GAMS / GTAP-RunGTAP | 比较静态 | SAM 平衡 |
| 动态 CGE | GAMS recursive | 时间路径 | 投资闭合规则 |
| GTAP-E | GAMS | 能源 / 排放 | 嵌套 CES 阶 |

## 一般原则

- **能用线性求解就别用非线性**：除非模型机制依赖非线性（大冲击、约束临界、风险）。
- **解法对应文献惯例**：DSGE 默认摄动；HA-DSGE 默认 SSJ；CGE 默认 GAMS；DP 默认 VFI/EGM。
- **跨方法验证**：高阶结论建议至少两种解法对照（线性 vs 非线性、本地 vs 全局）。
- **报错优先看维度**：90% 的"求不出稳态"都是变量计数或单位错误。
