---
name: strucmod
description: 父技能 / 入口索引。任何与结构建模、动态模拟、DSGE、CGE、异质主体、动态规划相关的任务，先读本技能再分派到原子技能。
type: orchestrator
---

# strucmod — 结构建模与动态模拟工作流父技能

本技能是 `structural-modeling-for-economists` 工作流的总入口。任何涉及结构经济模型构建、求解、仿真、反事实、表达的任务，agent 都应先读本文件，依据任务关键字与产物形态，分派到下方原子技能。

## 触发关键字

中文：DSGE、动态随机一般均衡、CGE、可计算一般均衡、GTAP、异质主体、Aiyagari、Bewley、Krusell-Smith、动态规划、值函数迭代、政策函数、稳态、脉冲响应、反事实、过渡路径、校准、矩匹配、福利分析、摄动、投影、sequence-space。

English: DSGE, CGE, GTAP, heterogeneous-agent, Aiyagari, Bewley, dynamic programming, value function iteration, policy function, steady state, IRF, impulse response, counterfactual, transition path, calibration, moment matching, welfare, perturbation, projection, sequence-space.

## 任务分类与分派

| 任务类型 | 触发示意 | 调用 skill | 后置 skill |
|---|---|---|---|
| 新模型立项 | "我想建一个 XXX 模型来研究 YYY" | `setup-<class>` | `model-reviewer` 子 agent |
| 已有设定 → 代码 | "spec 写好了，生成 Dynare 代码" | `setup-<class>` 的 codegen 段 | `code-reviewer` |
| 校准参数 | "把这个模型校准到中国 2010-2020 数据" | `calibrate-from-moments` | `math-reviewer` |
| 求稳态 | "为什么稳态求不出来" | `validate-steady-state` | `numerics-reviewer` |
| 跑 IRF | "跑一阶摄动 + IRF" | `solve-perturbation` → `simulate-irf` | `verifier` |
| 跑反事实 | "把关税从 5% 提到 25% 看 GDP 路径" | `counterfactual-run` | `verifier` |
| 写论文段落 | "把方法节写出来" | `render-report` + `build-tables` | `proofread` |
| 复现 | "上次跑的那个结果再来一遍" | `replicate` | `verifier` |
| 完整流水线 | "从头到尾跑一遍" | `run-pipeline` | `verifier` |

## 原子技能清单

### A. 设定（Setup）

- [`setup-dsge`](../setup-dsge/SKILL.md) — DSGE 设定与 Dynare/Julia 脚手架
- [`setup-cge-gtap`](../setup-cge-gtap/SKILL.md) — CGE / GTAP 设定与 GAMS 脚手架
- [`setup-ha-bewley`](../setup-ha-bewley/SKILL.md) — 异质主体（Aiyagari/Bewley/Krusell-Smith）

### B. 校准（Calibrate）

- [`calibrate-from-moments`](../calibrate-from-moments/SKILL.md) — 从数据 / 文献 / 矩条件组装校准

### C. 求解（Solve）

- [`solve-perturbation`](../solve-perturbation/SKILL.md) — 一/二/三阶摄动
- [`solve-vfi`](../solve-vfi/SKILL.md) — 值函数迭代 / 策略迭代 / 投影

### D. 仿真与反事实（Simulate）

- [`simulate-irf`](../simulate-irf/SKILL.md) — 脉冲响应函数
- [`counterfactual-run`](../counterfactual-run/SKILL.md) — 反事实 / 过渡路径 / 政策实验

### E. 验证（Validate）

- [`validate-steady-state`](../validate-steady-state/SKILL.md) — 数值化稳态校验（必经环节）

### F. 执行（Run）

- [`run-dynare`](../run-dynare/SKILL.md)
- [`run-julia`](../run-julia/SKILL.md)
- [`run-matlab`](../run-matlab/SKILL.md)
- [`run-pipeline`](../run-pipeline/SKILL.md) — 端到端

### G. 表达（Express）

- [`build-tables`](../build-tables/SKILL.md) — 校准表 / 矩比对表 / IRF 表
- [`render-report`](../render-report/SKILL.md) — Quarto / LaTeX 报告

### H. 复现（Reproduce）

- [`replicate`](../replicate/SKILL.md) — 用保存的种子与设定重跑

### I. 评议（Review）

- [`review-model`](../review-model/SKILL.md) — 经济逻辑与机制评议
- [`devils-advocate`](../devils-advocate/SKILL.md) — 反方拷问

### J. 学术辅助（Academic）

- [`lit-review`](../lit-review/SKILL.md)
- [`proofread`](../proofread/SKILL.md)
- [`interview-me`](../interview-me/SKILL.md) — 让 agent 反向访谈研究生以厘清机制

### K. 工程（Engineering）

- [`commit`](../commit/SKILL.md)

## 入口决策树

```
用户请求
  │
  ├─ 提到具体模型类（DSGE/CGE/HA/DP）但未写 spec.md？
  │     → setup-<class>
  │
  ├─ spec.md 已存在但未通过 model-reviewer？
  │     → 调用 model-reviewer 子 agent
  │
  ├─ 已通过 review，要校准参数？
  │     → calibrate-from-moments
  │
  ├─ 校准完毕，要求解？
  │     → solve-<method>（先 validate-steady-state）
  │
  ├─ 求解完毕，要看冲击 / 反事实？
  │     → simulate-irf 或 counterfactual-run
  │
  ├─ 要写论文 / 报告？
  │     → build-tables + render-report
  │
  └─ 想复现历史？
        → replicate
```

## 必经检查点（Mandatory Checkpoints）

无论从哪个 skill 入手，下列 checkpoint 不可绕过：

1. **设定评审**：任何模型代码动手前，`model-reviewer` 必须批准 `spec.md`。
2. **维度检查**：方程系统首次落入代码前，`math-reviewer` 必须确认方程数 = 未知数、变量分类无矛盾、单位一致。
3. **稳态校验**：`validate-steady-state` 残差必须低于 `tol = 1e-8`（默认）方可进入仿真。
4. **复现核对**：任何对外报告的数字，必须由 `verifier` 重跑一次并核对。

## 输入 / 输出契约

每个原子技能都遵循统一契约：

**输入**：
- `model_name`：字符串，对应 `model/01_setup/<model_name>/`
- `language`：`dynare` / `julia` / `matlab` / `gams` / `python`
- `task_payload`：依技能而定（见各技能 `SKILL.md`）
- `seed`：整数（默认从 `model/_utils/seed.txt` 读取）

**输出**：
- 产物文件落入 `output/<subdir>/`
- 日志写入 `logs/<model>_<step>_<timestamp>.log`
- 检查点写入 `output/checkpoints/<model>_<artifact>.json`
- 在 `templates/session-log.md` 副本中追加一行运行记录

## 常见失败与回退

详见 `AGENTS.md` 中的"失败回退"表。
