---
name: simulate-irf
description: 基于已求解模型生成脉冲响应函数（IRF）及对应表与图。当用户说"跑 IRF"、"脉冲响应"、"impulse response"、"看一冲击下变量怎么动"时调用。前置必须已通过 solve-perturbation 或 solve-vfi。
type: simulator
---

# simulate-irf — 脉冲响应仿真

## 触发场景

- "跑 IRF"、"impulse response function"、"脉冲响应"
- "TFP 冲击下消费投资怎么走"
- "把每个冲击的 IRF 都画出来"
- "做一组对比 IRF（不同参数）"

## 输入契约

| 字段 | 类型 | 说明 |
|---|---|---|
| `model_name` | str | 必须已存在求解后的 `output/checkpoints/<model>_policy.json` |
| `shock_name` | str / list | 单个或多个外生冲击名（须出现在 spec.md 与 calibration） |
| `horizon` | int | IRF 期数，默认 40 |
| `shock_size` | float | 冲击大小，默认 1 个标准差 |
| `variables` | list[str] | 要画的内生变量；缺省 = spec 中所有内生变量 |
| `compare` | list[dict]? | 可选：多模型 / 多参数对比 |

## 前置条件

- [ ] `output/checkpoints/<model>_policy.json` 存在且 `validated == true`
- [ ] `model/01_setup/<model>/spec.md` 中 §9.3 IRF 形状先验已写
- [ ] `solve-perturbation` 或同等求解技能已通过

## 步骤清单

### Step 1. 加载政策矩阵 / 决策规则

读 `output/checkpoints/<model>_policy.json`，把政策矩阵 / 决策规则反序列化。

### Step 2. 构造冲击向量

- 一阶 / 二阶摄动：标准 IRF（脉冲在 t=0 给一个标准差冲击，之后冲击为 0）
- VFI / 全局解：用决策规则递推非线性 IRF
- Sequence-space：用雅可比矩阵直接计算

### Step 3. 递推路径

```
x_t = A * x_{t-1} + B * eps_t   (一阶)
x_t = A*x_{t-1} + (1/2)*C*kron(x,x) + B*eps + (1/2)*D  (二阶)
```

对每个目标变量在每期计算偏离稳态的百分比响应（实际取对数偏离与稳态值看变量类型）。

### Step 4. 形状诊断（关键）

把 IRF 与 `spec.md` §9.3 的形状先验对照：

- 持续性是否合理（半衰期）
- 符号是否符合机制叙述
- 峰值时点是否合理
- 长期是否回归 0

任一异常 → 在 `quality_reports/<model>_irf_diagnostics_<timestamp>.md` 中标记。严重异常 → 调用 `model-reviewer`。

### Step 5. 保存数据

`output/tables/<model>_irf_<shock>.csv`：

```csv
period,c,k,y,z
0,0.0,0.0,0.7,1.0
1,0.21,0.05,0.55,0.95
...
```

`output/checkpoints/<model>_irf_<shock>.json`：完整 IRF 数据 + 元信息（seed、求解器、shock 大小）。

### Step 6. 绘图

- 每个变量一张子图，组合成网格（推荐 2×3 或 3×3）
- 横轴 = 期数，纵轴 = 偏离稳态百分比
- 标题含 `<model> · <shock> · <date>`
- 同时导出 `.pdf` 与 `.png` 到 `output/figures/<model>_irf_<shock>.{pdf,png}`
- 多模型对比时使用不同线型 + 图例

### Step 7. 生成 LaTeX 段落

写 `output/latex/<model>/irf_<shock>.tex`：

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=0.9\textwidth]{<model>_irf_<shock>.pdf}
  \caption{冲击 \(\varepsilon_{<shock>}\) 下主要变量的脉冲响应（一标准差）。}
  \label{fig:<model>_irf_<shock>}
\end{figure}
```

并在 `output/latex/<model>/irf_<shock>_text.tex` 写 1-2 段方法描述与结果解读，由 LLM 草拟、人工核对。

### Step 8. 写日志与会话记录

## 输出契约

| 文件 | 必产 | 说明 |
|---|---|---|
| `output/tables/<model>_irf_<shock>.csv` | ✅ | 数值数据 |
| `output/checkpoints/<model>_irf_<shock>.json` | ✅ | 完整元信息 |
| `output/figures/<model>_irf_<shock>.{pdf,png}` | ✅ | 图 |
| `output/latex/<model>/irf_<shock>.tex` | ✅ | 论文用 LaTeX 片段 |
| `output/latex/<model>/irf_<shock>_text.tex` | ✅ | 方法 + 解读段落（草稿） |
| `quality_reports/<model>_irf_diagnostics_<timestamp>.md` | ✅ | 形状诊断 |
| `logs/<model>_irf_<timestamp>.log` | ✅ | 运行日志 |

## 不允许的操作

- 在 `validated == false` 的政策矩阵上跑 IRF
- 跳过形状诊断步骤直接产图
- 改变 `shock_size` 但不在文件名与图标题中标记
- 在 LaTeX 段落中陈述未经 `verifier` 核对的具体数字（峰值百分比等）

## 失败回退

| 症状 | 处理 |
|---|---|
| IRF 发散（不回稳态） | 检查 BK 条件 / 参数稳定区间；通常说明 spec 或校准有问题 |
| 符号反直觉 | 形状诊断标记 → `model-reviewer` 复核机制叙述 |
| 半衰期极长 | 检查持续性参数（rho）是否过大 |
| 多变量响应"全 0" | 冲击未真正进入对应方程；检查 spec 中冲击映射 |
| 二阶修正异常大 | 稳态远离非线性中心；考虑投影法或 sequence-space |
