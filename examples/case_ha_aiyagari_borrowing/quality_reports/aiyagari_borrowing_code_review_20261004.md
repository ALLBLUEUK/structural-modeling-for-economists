# 代码评议 · aiyagari_borrowing · 20261004

- reviewer = code-reviewer（strucmod v0.3 workflow, sub-agent）
- date = 2026-10-04
- 对象：`strucmod-v0.3/templates/master-ha-template.py`（模板）及其实例 `model/03_solve/aiyagari_borrowing/solve.py`。两者经 `diff` 核对，仅第 41 行 `MODEL_NAME` 不同，下文行号对两者通用。
- 依据：`agents/code-reviewer.md`、`rules/modeling-coding-conventions.md`、`spec.md`、`calibration.csv`、`scripts/check_steady_state.py`、`scripts/run_pipeline.sh`。
- 方法：通读代码，并在 scratchpad 里做数值复核（见各节"实测"）。复核脚本未改动项目代码。
- 说明：本评议只管代码惯例、可读性、错误处理和 I/O 契约。数值方法的深度评价（网格、截断、Tauchen 精度）归 `numerics-reviewer`。涉及这些的条目只作代码层提示。

## 副作用披露

我为验证 I/O 契约，对 baseline 检查点运行了 `scripts/check_steady_state.py`。该脚本会改写检查点：`validated_at` 被刷新为本次运行时间，`validated_tol` 被设为 1e-8。它还会生成 `quality_reports/aiyagari_borrowing_ss_*.md`。我已删除这份报告。检查点里的数值字段未变，`validated` 原为 True，仍为 True。如需保留原始时间戳，请重跑 baseline。

## 一、语言惯例

- 语言：Python（运行环境 3.13.3 / numpy 2.3.3 / scipy 1.16.2，运行时写入检查点 `env` 字段）。
- 顶部声明：**不通过**。文件头注释（L1-22）没有声明 Python / numpy / scipy 版本。`quality_score.py` 的 `header_decl` 项得 0/2。规则要求"语言版本在文件顶部声明"。运行时写 `env` 不能代替文件头声明。
- 块结构 / 模块划分：整体清晰。分为读入、Tauchen、价格与借贷下限、EGM、Young 分布、GE 与诊断、`run`、`main` 共 8 个部分，函数短，分隔注释统一，学生容易跟读。
- 可读性问题（建议项）：
  - L223 一行里塞了两个条件表达式，学生难读。
  - `run()`（L247-323）约 75 行，同时做装配、验证、写盘、写日志，宜拆成 `build_checkpoint` 和 `save`。
  - `tauchen` 的自相关用双重 Python 推导式（L91-92），可向量化为 `(logz-mean) @ (pi[:,None]*P) @ (logz-mean)`。
  - 注释以中文为主，符合规范。EGM 里 `Emu[i', z]` 的索引注释（L130）很好。
- 兼容性：**L243 用了 `np.trapezoid`，它只存在于 numpy ≥ 2.0**。学生机器若是 numpy 1.x，会直接 `AttributeError`，而且是在求解完之后、写检查点之前才崩，等于白算。这与文件头缺版本声明互相加重。应在文件头声明 `numpy>=2.0`，或改成手写梯形公式。

## 二、路径

- 相对路径：✅。`ROOT = Path(__file__).resolve().parents[3]`（L42）。我核对了层级：solve.py → `<model>` → `03_solve` → `model` → 项目根，正确。
- 硬编码盘符 / `/Users/`：无。
- 小问题：`load_params` 找不到 `calibration.csv` 时是裸 `FileNotFoundError`，未提示"请先完成 02_calibrate"。

## 三、日志

- 日志开启：✅，`logging.basicConfig` 同时写 stdout 和 `logs/`（L335-338）。
- 关闭 / 等价：⚠️。`FileHandler` 从不显式关闭，靠解释器退出时 `logging.shutdown` 兜底，可接受，但应在 `main` 里用 `try/finally` 说清楚。
- 文件名：`logs/<model>_solve_<scenario>_<ts>.log` ✅。注意 `ts` 用 UTC（L334），而日志行内时间是本地时间（实测文件名 17:22，日志首行 01:22），学生会困惑。建议统一。
- **异常没有进日志文件**（L339 `run()` 无 try/except）。EGM 不收敛的 `RuntimeError`（L142）以及任何未捕获异常只打到 stderr 的 traceback，不进 `logs/`。规则第 9 条要求失败时给清晰信息，日志是事后追查的唯一凭据。应 `try: ... except Exception: log.exception(...); raise`。

## 四、检查点

- 字段：`model, scenario, params, steady_state, residuals, diagnostics, seed, env, git_sha, timestamp, validated`。比 agent 文档要求的"model, params, ss, validated, timestamp"丰富，但 **键名是 `steady_state` 而不是 `ss`**。`check_steady_state.py` 要求的是 `steady_state`（L52-53 的 `required`），所以代码与脚本是一致的。agent 文档里的 `ss` 与脚本不一致，属于文档问题，建议统一，不是这份代码的错。
- 实测：对 `aiyagari_borrowing_baseline_ss.json` 运行 `check_steady_state.py`，退出码 0，最大残差 4.08e-14。✅ 字段契约可用。
- **文件名偏离**：代码写 `<model>_<scenario>_ss.json`（L313），而 `scripts/run_pipeline.sh:65` 读取的是 `output/checkpoints/${MODEL_NAME}_ss.json`。baseline 场景的文件名对不上，管线会找不到。要么 baseline 额外写一份 `<model>_ss.json`，要么在管线里按场景参数化。规则文件里的命名示例是 `<model>_<artifact>.json`，scenario 段是模板自行加的。
- **`validated` 被外部脚本覆盖的漏洞**：`check_steady_state.py` 只看 `residuals` 里每一项是否小于容差，通过就无条件写 `validated=True`（脚本 L93-96）。模板里的 `validated`（L306-308）还包含 `mass_top < 1e-8`、`crossings == 1`、`dist_converged`、`egm_converged`，这些条件不在 `residuals` 里。因此，如果某次求解 `validated=False`（例如网格上端质量超标），再跑 `check_steady_state.py` 会把它改回 True。建议把 `mass_at_grid_top`、`egm_sup_diff`、`dist_sup_diff` 也放进 `residuals`，让脚本能看到。
- `residuals` 里的 `distribution_mass_minus_one` 命名与"每个方程名 → 残差"的契约一致，没问题。
- JSON 严格性：`euler_errors` 在无非约束点时返回 `-inf`（L223），`json.dumps` 会写出 `-Infinity`，这不是合法 JSON。只是边缘情形，可改为 `None`。
- `git_sha` 恒为 `"n/a"`（L298），没有真正读取，建议项。

## 五、种子

- 从 `model/_utils/seed.txt` 读取（L46、L249）：✅，无硬编码。
- 种子读到后只记录，不使用（算法完全确定性），没问题。
- 小问题：文件缺失时静默变为 `None`（L249），与规则"从 seed.txt 读"相比过于宽松。确定性求解可以接受，但应在日志里写一行 warning。

## 六、与 spec 对齐

逐项对账，结果如下。

- 参数名与 `calibration.csv`：✅。beta, mu, alpha, delta, rho, sigma, n_z, m, n_a, a_max, b, tol_ss 全部一致。`r_hi_eps`、`r_lo_eps` 不在 csv 里，由 `p.get` 提供默认值。它们是 spec §8 的端点常数，但在 csv 里没有登记，参数溯源有缺口，建议加入 csv。
- 方程对账：
  - (E1) Euler 与互补松弛：L130-136 ✅。
  - (E2) 预算：L127、L137 ✅。
  - (E3) 分布不动点：L148-185 ✅。
  - (E4)(E5) 价格：L101-105，`Kd = (α/(r+δ))^{1/(1-α)}`，`w = (1-α)Kd^α` ✅。
  - (E6) 市场出清：L202-204 ✅。
  - (E7) Y：L260 ✅。
- φ(r)：L108-113，与 spec §3.1 一致。r ≤ 0 取 b，r > 0 取 min{b, w z_min/r}。✅
- Tauchen：网格 ±m·σ_无条件，转移概率按 σ_ε，归一化 E[z]=1（L68-95）与 spec §5 一致 ✅。
- 网格幂次 2、`a_max`、`n_a` 与 spec §8 一致 ✅。
- r 端点 `[-δ+0.02, 1/β-1-1e-4]`（L254-255）✅。唯一性 15 点扫描（L226）✅。
- 验证项 9.10 的 Euler 误差已实现，口径见第七节。
- **残差含义需要写清楚**：基准解的 `capital_market_rel = 4.08e-14`（见检查点）。这只说明 Brent 把同一个确定性函数解到了机器精度，**并不反映分布离散化误差**。spec §8 放宽到 1e-6 的理由是"分布离散化误差"，但代码里的残差度量不到这种误差：`household_side(r_star)` 重算的就是 Brent 内部用的同一个函数。放宽理由与度量对象不一致，建议在 spec 或报告里改写，避免读者以为 4e-14 代表模型精度。
- Tauchen 质量：基准下 `var_logz = 0.0548`，目标 0.04，偏高 37%；自相关 0.9016，目标 0.9（见检查点）。spec §9.6 要求报告偏差，代码做到了。方差偏高是 7 点、±3σ 网格的已知特性。这属于数值方法范畴，请 `numerics-reviewer` 评估。

## 七、核心算法的正确性核对

### 7.1 EGM（L123-142）

- Euler 反解：`Emu = (c**(-mu)) @ P.T`（L130）。我核对了索引：`Emu[i,z] = Σ_z' c[i,z']^{-μ} P[z,z']` ✅。`c_endo`、`a_endo` 公式（L131-132）正确。
- 借贷约束：`np.interp(a, a_endo[:,j], a)` 之后，对 `a < a_endo[0,j]` 的点令 `a'=a[0]`（L135-136）✅。注意 `np.interp` 左端本来就返回 `fp[0]=a[0]`，所以 L136 在功能上是冗余的。它有教学价值（明示约束），建议在注释里这样说明，否则学生以为 L136 是必需的。
- `a_endo` 严格递增：因为 `c_endo` 随 a' 递增，所以插值合法 ✅。
- 上端截断：对 `a > a_endo[-1,j]`，`np.interp` 右端钳位为 `a_max`。实测在 `a=a_max, z=z_max` 处策略被钉在 `a'=200`（`a_pol - a = 0`）。这是网格上端的人为产物。代码用 `mass_top` 来监控，思路正确，但见 7.4。
- **借贷下限等于自然上限时的退化（实测）**：当 φ 取到自然上限 `w z_min/r`，`c(a[0], z_min) = w z_min − rφ = 0`（舍入后可能为微小负数）。此时 `c**(-mu)` 溢出，随后 `(β R Emu)**(-1/μ)` 产生 NaN。我用 `b=30, r=0.0416` 复现：先报 `RuntimeWarning: invalid value encountered in power`，然后**空转满 5000 次迭代**才抛 `RuntimeError(diff=nan)`。实验设定 `b ≤ 8` 没有触发，因为 b=8 时 r_hi 处自然上限约 15.1 > 8，已核对。所以这不影响本案例，但模板要给学生任意复制，学生把 `b` 设大一些就会撞上。建议：每次迭代检测 `np.isfinite(diff)`，不是有限数就立即报错并写明"φ 已触及自然借贷上限"。
- 收敛判据 `diff < tol`（L140）用消费的绝对误差，`maxit` 耗尽时抛异常（L142）✅。这是正确的 fail-loud。
- 没有热启动（`c_init` 永远为 None）：GE 中每个 r 都从头迭代，baseline 要 576 次、b=8 在上端 r 要 532 次。可以把上一个 r 的 `c` 传入。这是效率建议，不影响正确性。

### 7.2 Young 彩票转移（L148-185）

- 下标：`idx = searchsorted(a, a_pol, 'right') − 1`，并钳到 `[0, na−2]`；`wt_hi = (a' − a[idx])/(a[idx+1] − a[idx])`，并钳到 `[0,1]`（L150-151）✅。当 `a' = a[-1]` 时 `idx=na−2`、权重为 1，没有越界。
- 状态编号：`s = i + j·na`（L157），列侧 `idx + jp·na`（L159）。这是"z 为慢变量、a 为快变量"的编号，与 `D = d.reshape(nz, na).T`（L184）互相一致，所以 `D[i,j]` 对应资产 a_i、状态 z_j ✅。
- 实测：`D` 按 z 的边际分布与 Tauchen 的 π 相差 1.9e-15；`E[a'] = Σ a'·D` 与 `Ks = Σ a·D` 相差约 1e-14。这两项分别证明了彩票法保持均值、转移矩阵与 D 的布局一致 ✅。
- `P[j,jp]==0` 跳过（L155）在 Tauchen 下永不触发，无害。
- 彩票法不依赖 `a_pol ≥ a[0]`，但 `a_pol < a[0]`（舍入）时 `wt_hi` 被钳到 0，处理正确。

### 7.3 平稳分布的线性解（L165-185）

- 数学：方程 `(T' − I)d = 0` 的所有行之和为零，所以任意一行是冗余的。把最后一行换成 `Σd=1`（L168-170）是合法的。后面用 `TT @ d` 迭代打磨，基准下只需 1 步，`diff=2e-17`，✅。
- **`except` 分支实际上永远不会触发（实测）**：`scipy.sparse.linalg.spsolve` 遇奇异矩阵不抛异常，只发 `MatrixRankWarning` 并返回全 NaN（我用零矩阵复现）。于是 L175-176 的"奇异时退回均匀初值"形同虚设。NaN 会通过 `np.maximum`（NaN 保持为 NaN）流入后面的迭代，空转 100000 次后 `dist_converged=False`。结果虽然不会被报告为 validated，但耗时长且原因不明。应在 L172 后加 `if not np.all(np.isfinite(d))` 的判断。
- `A.tolil()` 后整行赋值（L167-168）对 n=2800 没问题。若学生把 `n_a*n_z` 放大到几万，稠密末行会引起 LU 填充，可在注释里提一句。
- 迭代循环结束后 `d` 未重新归一化，质量偏差由 `distribution_mass_minus_one` 报告，可接受。

### 7.4 Euler 误差（L210-223）

- 公式：下一期消费用 `np.interp(a_pol[:,j], a, c[:,jp])` 在 a' 处取值，再 `rhs = βR (c_next^{-μ}) @ P[j]`，误差 `|1 − rhs^{-1/μ}/c|`。索引和量纲都正确 ✅。非约束点判据（L218）合理。
- **`euler_error_log10_max` 被网格上端伪影主导（实测）**：基准的最大误差 −2.32，即 0.47%。我定位到它在 `a=a_max=200, z=z_max`，该处质量为 0，正是 7.1 所说的钳位产物。真正有分布质量的点上，按分布加权的平均误差在 1e-6 至 1e-9 量级。所以这个 `max` 对学生会造成误读，以为模型精度差。建议只统计 `D > 1e-12`（或排除最后几个网格点）的点，或同时报告"加权均值"。
- 命名：`euler_error_log10_mean` 实际是 `log10(mean(|误差|))`，不是 `mean(log10|误差|)`。两者在文献里都出现，spec §9.10 的措辞对应前者，代码一致。但变量名容易误解，建议在注释里写明。
- `e = e[e > 0]`（L222）会删掉恰为 0 的点，使均值略偏大，影响可忽略，但学生未必明白用意。

### 7.5 Gini（L234-244）

- 实测：我用成对绝对差公式 `Σ|x_i−x_j|p_i p_j/(2μ)` 独立重算。基准下两者为 0.47833059 与 0.47833059，一致；b=2（r=0.03，含负资产）下为 0.95299074 与 0.95299074，一致。**负资产时 Lorenz 曲线先为负再上升，梯形面积公式仍然给出正确的广义 Gini** ✅。
- **缺保护**：当均值 `total = cv[-1] ≤ 0` 时（净资产总和为零或为负），除法无意义，函数会静默返回一个无意义的数字。Aiyagari 均衡中 K>0，不会触发，但应加 `assert total > 0`。
- **解释风险**：负资产下的广义 Gini 可以大于 1，且当均值接近 0 时对均值极度敏感（b=2 的非均衡点算出 0.95）。报告 b>0 的各场景时必须注明"净资产 Gini，含负值"，不宜与 b=0 的结果直接比较。这只是提醒，函数本身对。
- `np.trapezoid` 的版本问题见第一节。
- `wealth` 构造 `a[:,None]*np.ones_like(D)`（L263）可以直接用 `np.repeat`，只是风格问题。

### 7.6 一般均衡与 Brent（L226-231、L254-256）

- 区间：`[r_lo, r_hi] = [−δ+0.02, 1/β−1−1e-4]`（L254-255），实测在 b=8 下端点符号为负、上端点为正（−1.09 → +25.8）✅。
- **没有显式检查括号符号**：L229 已经算好了 `scan_ex`，却不检查 `scan_ex[0] < 0 < scan_ex[-1]`，直接把区间交给 `brentq`。我实测，当区间无符号变化时报出 `ValueError: f(a) and f(b) must have different signs`，学生看不懂该改什么。应在 L229 之后加显式检查，并给出"请调整 `r_lo_eps` / `r_hi_eps` 或扩大 `a_max`"的提示。
- `brentq` 参数 `xtol=1e-12, rtol=1e-12`（L230）合法（`rtol ≥ 4·eps`）。
- 穿越计数（L229）：`np.sign` 在恰为 0 时会把 "0→+" 也算作穿越，极端情形，可忽略。
- `validated` 要求 `crossings == 1`（L307）：15 点只能排除粗粒度多重穿越，spec §9.7 已承认。
- 每个 `r` 重建 `a` 网格（L193-194），与 spec §8 一致。这意味着 `excess(r)` 带有网格变动引起的微小非光滑，但本案例 φ 在均衡附近恒等于 b，网格不变，影响为零。

### 7.7 Tauchen（L68-95）

- 区间概率与端点处理正确，每行和为 1（实测 4.4e-16）。平稳分布取最接近 1 的特征向量并除以和，已同时修正符号 ✅。
- 无参数保护：`rho=1` 时 `sig_e=0` 会除零。csv 的 bounds 限制 ρ ≤ 0.95，覆盖了本案例，但 `--set rho=1` 不会被拦截。

## 八、错误处理与参数覆盖

- **`--set` 的未知键被静默接受**（L59、L331）。`--set B=2`（大小写写错）或 `--set beta_=0.9` 都不会报错，只会往 `p` 里多塞一个无用键，然后以基准参数照常求解，并把它标成新的 scenario。这是学生最容易踩的坑，且不会有任何警告。应在 `load_params` 里：
  - 覆盖键必须在 csv 里，或在白名单 `{r_hi_eps, r_lo_eps}` 里；
  - 否则 `raise KeyError` 并列出可用键。
- `load_params` 缺参数时抛裸 `KeyError`（L61、L250 附近），没有"缺 xxx，请检查 calibration.csv"的信息。
- `scenario` 名与实际覆盖参数没有关联检查（例如 `--scenario b2` 却没传 `--set b=2`），可在检查点里记录覆盖项。`params` 字段已经含最终参数，所以事后可查，只是没有显式的 `overrides` 字段。
- 重复硬编码的容差：L302-303 的 `1e-12` 与 `1e-10` 重复了函数默认值（L148、L123）。以后改了一处，另一处不会跟着变。应当由 `run` 统一传入。
- `if not dist_converged: log.error(...)`（L309-310）只写日志，不中断。但 `validated` 已为 False 且退出码为 2，足够，可接受。

## 九、quality_score.py 打分

实测（对实例 `solve.py`）：**10/12**。

| 维度 | 得分 |
|---|---|
| header_decl | 0/2 |
| relative_paths | 2/2 |
| logging | 2/2 |
| checkpoint | 2/2 |
| chinese_comments | 2/2 |
| data_protection | 2/2 |

失分只在文件头版本声明。≥ 8，满足"不允许给通过判断但得分 < 8"的约束。

## 十、综合

**修改后通过。** 核心数值内核（EGM、Young 彩票、D[i,j] 布局、线性解、Euler 误差、含负资产的 Gini、Brent 区间）经独立实测均正确，I/O 契约可被 `check_steady_state.py` 读取。需要修改的主要是模板作为"给学生复制的通用件"所缺的护栏：版本声明、异常进日志、括号检查、NaN 守卫、未知参数键校验。

## 十一、必改清单

必改（模板分发前）：

- [ ] 1. 文件头补充版本声明（Python ≥ 3.9、numpy ≥ 2.0、scipy 版本），修复 `quality_score` 的 `header_decl` 0/2（L1-22）。
- [ ] 2. L243 的 `np.trapezoid` 要么声明 `numpy>=2.0`，要么改成手写梯形，避免 numpy 1.x 在求解后才崩。
- [ ] 3. `--set` / `load_params` 校验覆盖键，未知键直接报错并列出可选键（L54-62、L331）。
- [ ] 4. `run()` 外层 `try/except` 并 `log.exception`，使 EGM 失败等异常进入 `logs/*.log`（L339）。
- [ ] 5. `solve_ge` 在调用 `brentq` 前显式检查括号符号，给出可操作的错误信息（L226-231）。
- [ ] 6. EGM 每次迭代检查 `np.isfinite(diff)`，非有限时立即报错，提示 φ 触及自然借贷上限（L137-142）。
- [ ] 7. `spsolve` 之后检查 `np.isfinite(d)`，替代永不触发的 `try/except`（L171-176）。
- [ ] 8. 检查点命名与 `run_pipeline.sh:65` 对齐：baseline 额外写 `<model>_ss.json`，或改管线（L313）。
- [ ] 9. 把 `mass_at_grid_top`、`egm_sup_diff`、`dist_sup_diff` 并入 `residuals`，防止 `check_steady_state.py` 把 `validated=False` 改成 True（L281-285）。
- [ ] 10. `euler_error_log10_max` 只统计有分布质量的非约束点（或排除网格上端），并在注释中说明 `log10(mean|e|)` 的口径（L210-223）。

建议（不阻塞）：

- [ ] 11. `gini` 加 `total > 0` 断言，并在报告中注明含负资产的广义 Gini 可超过 1。
- [ ] 12. 容差由 `run` 统一传入，去掉 L302-303 的重复硬编码。
- [ ] 13. 日志文件名与行内时间统一时区；种子文件缺失时写 warning。
- [ ] 14. `r_hi_eps`、`r_lo_eps` 登记到 `calibration.csv`。
- [ ] 15. L136 加注释说明它与 `np.interp` 左端钳位重叠。
- [ ] 16. `tauchen` 自相关向量化，`run()` 拆分，EGM 加热启动。
- [ ] 17. spec §8 放宽 1e-6 的理由改写（残差度量的是求根精度，而非离散化误差）。
- [ ] 18. 上端 Euler 误差与 Tauchen 方差偏高（0.0548 vs 0.04）转交 `numerics-reviewer`。
- [ ] 19. 文档层：agent 文档里的检查点字段 `ss` 与 `check_steady_state.py` 要求的 `steady_state` 不一致，请统一。

## 复核（v0.3 修订后）· 2026-10-04

复核对象：`strucmod-v0.3/templates/master-ha-template.py`（修订版）与 `scripts/check_steady_state.py`。我读了修订后的全文，并做了数值复核。复核时未改代码。注意：实例 `solve.py` 尚未同步，仍是旧版。

### 逐项核对（原必改 1-10）

| # | 项目 | 结果 | 依据 |
|---|---|---|---|
| 1 | 版本声明 | 部分通过 | L3-4 已写 "v0.3.0" 和依赖 "Python ≥ 3.10，numpy ≥ 1.24，scipy ≥ 1.10"。但 `quality_score.py` 的正则（L36）匹配的是 `version`、`Python\s+3\.`、`版本`，写法 "Python ≥ 3.10" 不匹配。头部也没有 spec.md 引用（L38 的第二分）。**复测 `header_decl` 仍为 0/2，总分仍为 10/12。** 内容上满足规则，打分器看不到。 |
| 2 | `np.trapezoid` | 通过 | L299 `getattr(np, "trapezoid", None) or np.trapz`，与头部声明的 numpy ≥ 1.24 一致。 |
| 3 | `--set` 未知键 | 通过 | L61-64 白名单加 `KeyError`，错误信息列出未知键。 |
| 4 | 异常进日志 | 通过 | L401-405 `log.exception` 并返回 3。 |
| 5 | brentq 括号检查 | 通过 | L283-285 两端同号时给出可操作的错误信息。 |
| 6 | EGM 非有限守卫 | 通过 | L186-187 检查有限性与 `c<=0`，立即抛 `FloatingPointError`，不再空转。 |
| 7 | spsolve 有限性 | 通过 | L223-224 加 L227-229 带 `log.warning` 的回退。 |
| 8 | 检查点命名 | 通过 | L374-376 baseline 额外写 `<model>_ss.json`，与 `run_pipeline.sh:65` 对上。 |
| 9 | validated 被外部覆盖 | 通过（换了方式） | 没有把条件并入 `residuals`，而是在脚本里改：`check_steady_state.py` 现在遇到求解器写的 `validated=False` 会维持不通过并返回 2。我实读了脚本，逻辑正确。 |
| 10 | Euler 误差口径 | 通过 | L271 加 `D>1e-12` 过滤，上端零质量点不再主导 `max`。 |

### 新增内容核对

- **Rouwenhorst（L104-143）**：实测 n=7、ρ=0.9、σ=0.2 下，方差 0.0400（相对误差 3e-16），自相关 0.9（误差 0），行和误差 2e-16，E[z]=1。算法正确。Tauchen 回退路径仍可用（方差偏高 37%，已被量化指标捕捉）。
- **离散化阈值（L361）**：`var_rel_error < 5%` 且 `autocorr_abs_error < 1%` 并入 `validated`，设计合理。这也意味着旧的 Tauchen 默认设定在该阈值下会得到 `validated=False`，这是有意为之，但需要在 spec 里写明。
- **30 点扫描、`brentq` 的 `xtol/rtol=1e-15`（L279、L286）**：参数合法（`rtol ≥ 4·eps`，`maxiter=500`）。

### 遗留问题（均不阻塞）

1. `header_decl` 打分器仍为 0/2。建议把头部改写成 "Python 3.10+ …" 或 "版本：…"，并加一行 `spec：model/01_setup/<MODEL_NAME>/spec.md`。成本很低，可以拿到 12/12。
2. L393 的 `--set` 解析在 `try` 之外。写成 `--set b` 而没有 `=` 会产生裸 `ValueError`，不进日志。
3. `gini`（L295）仍无 `total > 0` 保护；`euler_errors` 无点时仍返回 `-inf`（L276），写入 JSON 会成为非法的 `-Infinity`。
4. 容差硬编码（L359-360）、无热启动、日志时区不一致、`r_hi_eps` 等未登记 csv，均与初评的"建议项"相同，未处理。
5. 实例 `solve.py` 仍是旧版：验收案例要同步新模板并重跑，否则案例结果与模板不一致，且 baseline 的 `<model>_ss.json` 不存在。
6. 旧版检查点里 `validated` 字段由求解器写出，所以新脚本对其有效；若检查点缺 `validated` 字段（`None`），脚本仍会写 True。属于向后兼容的合理行为，仅提示。

### 最终结论

**通过（模板）。** 原 10 项必改全部落实，除第 1 项在打分器层面未得分外，均已核实通过。上述遗留项为建议级。
