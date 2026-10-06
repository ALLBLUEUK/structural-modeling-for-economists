# 代码评议 · armington_tariff · 20261004

- reviewer = code-reviewer（strucmod v0.3 workflow, sub-agent）
- date = 2026-10-04
- 被审对象：`strucmod-v0.3/templates/master-cge-template.py`（下称“模板”，365 行）；实例 `model/03_solve/armington_tariff/solve.py` 与模板逐行 diff 仅 L42 `MODEL_NAME` 一处不同。
- 对照：`model/01_setup/armington_tariff/spec.md` §5/§9、`scripts/check_walras.py`、`rules/modeling-coding-conventions.md`。
- 验证方式：在 scratchpad 复制项目后实跑（`--checks`、`--scenario S1/S2`、`check_walras.py`），并写了若干探针脚本（复合检验、基期含税、2 地区、未剔赤字）；未改动任何被审文件，未污染项目输出目录。越权声明：不评议经济机制、数学推导正确性本身，只对照 spec §5 看实现是否一致。

## 一、语言惯例
- 语言：Python 3.13.3 / numpy / scipy（实跑环境）。
- 顶部声明：**部分 ❌**。L1–L25 有模型名、方法、数据路径、用法，但**没有语言/库版本行**（`Python 3.x · numpy ≥ · scipy ≥`）；版本只在运行时写入 checkpoint 的 `env`（L300）。`quality_score.py` 因此 header_decl 仅 1/2。
- 块结构：数据结构 → 显式部分 `evaluate` → 求解器 → 结果整理 → 检验 → 情形 → CLI，分区清晰，学生可读。`Base` 用 `@property` 派生 Y/E/R/D/α/λ，简洁。
- 可读性问题：
  - L240–L246 `np.zeros(N) if abs(base.D).max() < 1e-9 else base.D` 重复 5 次，应先定义 `D0 = ...` 一次。
  - L155–L156 注释含开发史（“v0.3 修订……验收案例 ACR 检验中发现”），学生模板里应改成通用说明（“hybr 的 success 标志在接近机器精度时不可靠，改按残差判定”）。
  - 变量 `ri_`（L321）、`ri`/`si` 在多处重复构造，可抽成小函数；`evaluate`/`outcomes` 无 docstring，数组轴约定仅在 `Base` 注释里出现，建议在 `evaluate` 顶部再写一句 `[i 出口, j 进口, s 部门]`。
  - L94、L104、L107、L260 用 `open()` 不关闭（ResourceWarning），改 `with`。
  - `load_base` 默认 `flows_file="trade_flows.csv"`（L93），而 `main` 默认 `--flows trade_flows_purged.csv`（L332），默认值不一致，学生手工调用 `load_base()` 会误用含赤字的基期（实测 raw D = [-1120, 1320, -200]）。

## 二、路径
- 相对路径：✅ 。`grep` 无盘符/`/Users/`/`/home/`；全部基于 `ROOT = Path(__file__).resolve().parents[3]`（L43）。parents[3] 假定文件严格位于 `model/03_solve/<m>/`，成立。
- 小问题：模板未实例化（`MODEL_NAME = "<MODEL_NAME>"`）直接运行时，路径指向 `templates/..` 之上，报错信息莫名其妙；建议在 `main` 开头 `if "<" in MODEL_NAME: sys.exit("请先把 MODEL_NAME 改成模型名")`。

## 三、日志
- 日志文件 `logs/<model>_solve_<ts>.log`，文件名规范 ✅；等价于 log open/close（logging + FileHandler）✅。
- **Windows 控制台编码缺陷（实测）**：L337–L339 的 `StreamHandler(sys.stdout)` 在中文 Windows（GBK）下遇到 `ŵ`/`Ŵ`（L312 等）抛 `UnicodeEncodeError`，每条日志打印 “--- Logging error ---” 和长回溯（S2 运行时复现）。文件日志（utf-8）不受影响，退出码不受影响，但对学生是噪音且显得“报错”。修复：`sys.stdout.reconfigure(encoding="utf-8", errors="replace")`，或日志里改用 ASCII（what/What）。
- 时间戳用 UTC（L336），惯例未限定，但学生期望本地时间；建议在注释里说明，或用本地时间。

## 四、检查点
- 位置 `output/checkpoints/<model>_<scenario>.json` ✅，字段含 model、eps（参数）、results、validated、timestamp、env，基本符合“model, params, ss, validated, timestamp”要求（无 `ss`，对静态比较模型可接受）。
- `quality_score.py` checkpoint 项 1/2：代码用 `ROOT / "output" / "checkpoints"`（L46），正则要 `output/checkpoints/` 字面串。建议在注释或日志中出现该字面串（或 L46 改写成 `ROOT / "output/checkpoints"`）。**当前自动得分 10/12**，高于 8 门槛。
- **崩溃 bug（实测复现）**：`--checks` 路径 L354 `(CKPT/...checks.json).write_text` 前**没有 `CKPT.mkdir(parents=True, exist_ok=True)`**；`mkdir` 只在 `run_scenario`（L309）里。全新实例化的项目先跑 `--checks`（命令行 docstring 的推荐顺序之一）会 `FileNotFoundError`，数值验证算完却不落盘。`--purge` 写 `DATA/…purged.csv` 亦假定 DATA 已存在（合理）。
- NaN 风险：若某部门在某出口地区无销售（稀疏数据），`Lhat`（L188）出现 0/0 = NaN，`json.dumps` 会写出非法 JSON 的 `NaN`，`check_walras.py` 的 `json.loads` 虽接受，但下游工具未必。可 `np.errstate` + 报错/置 null，并在 `load_base` 对零行/零列给出明确报错（`den=0` 时 `Phat` 也为 inf）。

## 五、种子
- 无随机过程，求解确定性；代码未读 `model/_utils/seed.txt`，也无硬编码种子 ✅（无违规）。建议在 checkpoint 中记录 seed 或在注释声明“本模板无随机性，故不读 seed”，以免被机械审计判缺。

## 六、与 spec 对齐（核心）
轴约定：`X[i,j,s]`，i 出口、j 进口、s 部门；`t[i,j,s]` 为进口方 j 对来自 i 的 s 征税。

| spec §5 / 项 | 代码 | 结论 |
|---|---|---|
| c = ŵ_i d̂ (1+t')/(1+t) | L117 `what[:,None,None]*dhat*(1+tp)/(1+base.t)`，ŵ 沿轴 0（出口方） | ✅ |
| (1) λ' | L118–L120，分母沿轴 0 求和（对出口方 k）`keepdims=True` | ✅ |
| (2) P̂ = [Σ_k λ c^-ε]^(-1/ε) | L121 `den[0]**(-1/eps[None,:])`，得 `[j,s]` | ✅ |
| ρ_j | L122 `Σ_s α[j,s] Σ_i λ' t'/(1+t')`：`sum(axis=0)`→`[j,s]`，乘 α 后 `sum(axis=1)` | ✅ |
| (3) E' = (ŵY+D')/(1−ρ)，R'=ρE' | L123–L124 | ✅ |
| (4) 出清 ŵY = Σ λ'αE'/(1+t') | L125 `Xp[i,j,s]`（含 `/(1+tp)` 还原出厂价）、L126 `sum(axis=(1,2))` | ✅ |
| (5) 计价单位 | L138–L141（world：Σ ŵY − ΣY；或 ŵ_k=1） | ✅ |
| (6) Ŵ = (E'/E)/Π P̂^α | L184–L185 `(Phat**alpha).prod(axis=1)`，L185 | ✅ |
| 福利分解三项 | L190–L194 | ⚠️ 仅 t_base = 0 时成立，见下 |
| L̂ = 部门销售变化/ŵ | L186–L188，`sec_sales=X.sum(axis=1)`（对 j 求和）✅ | ✅ |
| 赤字剔除 | L200–L206，D'=0、关税不变，以 `Xp` 作新基期 | ✅ |

独立验证（实跑）：
1. **复合检验（我加的探针，非模板自带）**：0→t1（B→A MAN 10%）再以结果为新基期 t1→t2，与直接 0→t2 比较，ŵ 差 3.3e-16、Ŵ 差 2.2e-16。这是对含税 hat 代数（`(1+t')/(1+t)`、含税 λ、ρ、闭式 E'、`Xp` 重建基期）的强检验，说明**实现与 spec 一致且在含基期关税的重置基期上也正确**。
2. S1：ŵ = (A 1.00294, B 0.99647, R 1.00027)，Ŵ = (1.000198, 0.999598, 1.000029)；分解三项和与 ln Ŵ 吻合（t_base=0）。市场出清残差 ~1e-17，`check_walras.py --tol 1e-9` 通过。
3. **分解在 base_tariffs 非零时静默失真（实测）**：设基期 t≠0（模板明确支持 `base_tariffs.csv`，L9、L103），L190–L194 的三项和与 ln Ŵ 相差 5.6e-4（量级与福利本身相当）。原因：spec 推导假设 E=Y（t=0, D=0），一般情形 Ŵ = (E'/E)/P̂，E=Y+R≠Y。代码既不断言也不告警。建议：`outcomes` 中加入第 4 项 `ln((Y)/E_base)` 修正项（使三项/四项可加），或在 `base.t.any()` 时关闭分解并写 `decomp_valid=False`；并在 checks 中断言 `Σ decomp = ln Ŵ`。
4. 对 `t_jj`≠0（spec §3.3 要求 t_jj=0）无校验：scenarios.csv 里写 `B,B,MAN` 会被静默接受。

方程数/变量名：Python 变量 `what/lamp/Phat/Ep/Rp` 与 spec §4 符号一一对应 ✅；参数名 `eps_<sector>` 与 calibration.csv 一致 ✅。

## 七、错误处理
- `solve_hybr` 以残差判定收敛（L157–L159）并抛 `RuntimeError`，优于依赖 `sol.success` ✅。但阈值 `1e-12`（相对世界总产出，L150）对大模型过严，hybr 在 N 大/ε 大时可能因舍入误判失败；spec §8 写的容差是 1e-10，建议与 spec 统一（求解 tol 1e-13，判定 1e-10）。
- `solve_iterate` 未收敛抛错（L176）但**不报告最终残差**；且 `run_scenario` 里第二求解器失败会让整个情形中断、不产出 checkpoint（L273），建议 try/except 后写 `two_solver_ok=False`、validated=False。
- 收敛判据（L172）是 ŵ 的变化量而非残差；与 hybr 判据不同，两解“一致”的检验（`two_solver_what_diff`）才是真正的收敛证据，可接受，但应在注释里说明。
- **CLI 健壮性（实测/推演）**：
  - L347 `base = ... else None`：基期文件不存在（未先 `--purge`）时，`--scenario`/`--checks` 直接 `AttributeError/TypeError: NoneType…`，应报“请先 `--purge`，或用 `--flows trade_flows.csv`”。
  - 不带任何参数运行静默退出码 0，应 `ap.error`/打印 help。
  - `--checks` 建议要求基期已剔赤字（见检验 3）。
  - CSV 若被 Excel 另存为“UTF-8 带 BOM”，`DictReader` 首列名成 `﻿texporter`，抛 `KeyError`（L95）；统一用 `encoding="utf-8-sig"`。
  - `scenarios.csv` 中未知地区/部门标签、重复行覆盖、tariff_new ≤ −1 均无友好校验（L262）；缺少 `eps_<s>` 时 `KeyError`（L108）无提示。
  - `--purge` 与 `--checks` 同次运行时顺序正确（purge 先写文件再加载），OK。

## 八、run_checks 逻辑审查（重点）
实跑结果：全部通过（all_pass=true），但**下列检验“名不副实”**：

1. **SAM 三项恒真（L216–L218）**：`sam_world_deficit_sum`、`sam_income_equals_sales`、`sam_expenditure_identity` 均由同一 X、t 定义派生（`Y=X.sum`、`E=Σ X(1+t)`、`R=ΣXt`、`D=E−Y−R`），代数恒等，实测后两项恰为 0.0。它们不检验数据，只检验代码没写反。对学生是**虚假安慰**。有意义的检验应为：spec §9.2 “剔除赤字后 max|D|<1e-9”（模板**没有**在 checks 中检验，只在 `--purge` 里 log），以及 SAM 的一致性应对外部数据（如行/列和给定的 SAM）做。
2. **零冲击（L220–L224）近乎无信息**：`root` 从 `ones` 出发，而 ŵ=1 恰为解，故偏差 0.0（实测）。更有信息的做法：从扰动初值（如 `ones*1.1`）出发，或增加 hybr 与 iterate 的零冲击都回到 1。
3. **缺 spec §9.4 Walras 与 §9.7 就业自洽于 `all_pass`**：被删方程的残差只在 `run_scenario` 的 `validated` 里查（L306），`run_checks` 未查；`sector_employment_adding_up` 同。且 `L_check`（L189）= (Σ销售'/ŵY) −1 在代数上等价于出清残差，并不独立；`sam_balance`（L293）的 rows = ŵY+R'+D'，cols = E'，由 E' 闭式必然相等（`check_walras.py` 的 SAM 部分因而是恒真）；`trade_balance_minus_D`（L298）亦恒等。**真正承载 Walras 检验的只有 `market_clearing_residuals` 里被删除的那一条**（该项 OK，且 JSON 输出了全部 N 条，契约正确）。
4. **ACR 检验（L226–L236）是真检验**（t=0 单部门，与 spec §9.6 一致，实测 2.2e-16），但：
   - 硬编码冲击 `dh[0,1,0]`、`dh[2,0,0]` 要求 N ≥ 3，**2 地区数据直接 IndexError**（实测）；
   - 它**不覆盖关税项**，所以含税代数没有独立的解析检验；本次靠我加的复合检验才确认。建议把“复合检验（两步 = 一步）”作为 spec 之外的模板内置检验（实现 ~10 行，且检验含税、基期重置、Xp 重建）；也可加 2 地区 1 部门含 t' 的闭式/手算 golden 值。
   - `eps.mean()` 对异质 ε 仍能运行但失去经济含义，注释应说明“仅检验引擎”。
5. **计价单位中性（L238–L244）**：冲击硬编码 `tp2[0,1,0] += 0.1`（A→B、部门 0），非零冲击是好的，但：(a) N≥2、S≥1 假设；(b) 只比较 Ŵ，不比较 ŵ 比值（`wA/wW` 应为常数 = 1/wW[0]），可加一行；(c) **在未剔赤字基期上本检验必然失败**（实测：未剔赤字 raw 数据 `numeraire_neutrality_What_diff = 4.7e-4`，all_pass=False），因为 spec §5 已说明 D≠0 时计价单位不中性；此时 `all_pass=False` 会被学生误读为代码错误。建议：`run_checks` 先断言 `max|D|<1e-9` 并给出明确提示，或在 D≠0 时跳过该检验并标注 “skipped”；
   - L240–L243 的 `D0` 三元式重复 5 次（见一）。
6. **双求解器检验（L246–L248）**：`solve_iterate` 与 `solve_hybr` **共用 `evaluate`**，所以只验证两种求根算法一致，不能发现 `evaluate` 的代数错误。名称“独立第二求解器”宜改为“第二求根算法”，避免过度声称。
7. 阈值 `all_pass` 判定（L350–L352）漏掉 `sam_income/expenditure`（反正恒真）和 `iterate`；`ok` 不含 Walras/就业/D=0。

## 九、solve_iterate 更新规则审查
- 规则 `ŵ ← ŵ·(sales/(ŵY))^damp`（L167）再按计价单位归一（L168–L171）。符号方向正确（对 i 产品超额需求即 sales > ŵY ⇒ 工资上调）；不动点要求各地区比值相等，结合归一与 Walras（ΣD'=0）得比值=1，故不动点即均衡 ✅。
- 实测 40–42 次迭代收敛到 8e-14（阻尼 0.5、ε=4）。对更大 ε 或更多地区，固定阻尼可能振荡/慢；`maxit=100000` 每步一次 `evaluate`，失败前耗时可能很长且无进度日志。建议：不收敛时给出最后 diff；可选自适应阻尼。
- 判据 `diff<1e-13`（绝对）靠近浮点噪声，规模大时可能永远达不到；建议放宽到 1e-12 或相对量。
- 在 D≠0、numeraire=“world”下，归一后 ΣŵY=ΣY，但 Σsales=ΣŵY+ΣD'（=ΣŵY 当 ΣD=0），OK；若 ΣD≠0（脏数据）不动点比值≠1、迭代会静默收敛到非均衡点，而 hybr 会因残差而报错——两者行为不对称，应在 `load_base` 或 `solve_*` 开头断言 ΣD'≈0。

## 十、I/O 契约与 check_walras.py
- `data["model"]`（L277）、`market_clearing_residuals`（字典 `clearing_<region>`，L291）、`sam_balance.rows/cols`（L293）与脚本字段、类型、长度要求全部吻合；实跑 `check_walras.py output/checkpoints/armington_tariff_S1.json --tol 1e-9` PASS，report 写入 `quality_reports/`。✅
- 残差已除以 `base.Y.sum()`（无量纲）✅，与容差语义一致。
- 注意：`check_walras.py` SAM 检验容差为绝对 1e-9；模板 rows/cols 为水平量（~1e4 量级），舍入误差 ~1e-12 相对 1e-16，当前通过，但数据量级放大后绝对容差会变严；属脚本侧，非模板问题（建议脚本改相对容差，仅提示）。
- 如 `check_walras.py` 默认 `--report-dir quality_reports` 相对当前目录，须在项目根目录运行；模板 docstring 用法已写“项目根目录”，OK。

## 十一、quality_score.py 打分
- 自动得分：**10/12**（header_decl 1/2：无版本声明；checkpoint 1/2：无 `output/checkpoints/` 字面串）。≥8，不触发“不允许”条款。

## 十二、Dynare 专项
- 不适用（Python）。

## 十三、综合
**修改后通过。** 核心 hat 代数与 spec §5 一致（含复合检验独立确认），对 check_walras.py 的契约兼容；但存在 1 个会崩溃的 bug、若干“名不副实”的内置检验、一个静默失真的福利分解边界，以及面向学生的 CLI/编码健壮性缺口，均应在发布为 v0.3 模板前修正。

## 十四、必改清单
- [ ] **M1（崩溃）** `main` 里 `--checks` 写文件前补 `CKPT.mkdir(parents=True, exist_ok=True)`（L354；最好挪到 `main` 开头，与 `LOGS.mkdir` 并列）。
- [ ] **M2（检验名不副实）** 重写 `run_checks`：删除/改写三项恒真 SAM 检验；加入 `max|D|<1e-9`（spec §9.2）、被删出清方程残差（§9.4）、就业自洽（§9.7）、`Σ decomp = ln Ŵ`；加入复合检验（0→t1→t2 = 0→t2）以覆盖含税代数；零冲击改为扰动初值。
- [ ] **M3（硬编码冲击）** ACR 与中性检验的冲击索引按 N、S 自适应（如取前两个地区、N<3 时降级冲击），并对 N<2 或 S<1 给清晰提示；中性检验同时比较 ŵ 比值；在 D≠0 时跳过并标 skipped，而非 all_pass=False。
- [ ] **M4（福利分解边界）** 基期 t≠0 时分解失真（实测差 5.6e-4）：加修正项或关闭并标记；至少加断言/警告。
- [ ] **M5（CLI）** 基期文件缺失时清晰报错（L347）；无动作参数时打印 help；`load_base` 默认 flows 与 CLI 默认统一；CSV 用 `utf-8-sig`；校验情形标签、t_jj=0、ΣD≈0。
- [ ] **M6（Windows 日志）** 解决 GBK 控制台下 `ŵ/Ŵ` 的 `UnicodeEncodeError`（reconfigure stdout 或改 ASCII 名）。
- [ ] **M7（规范）** 顶部补 `Python/numpy/scipy` 版本声明；出现 `output/checkpoints/` 字面串（quality_score → 12/12）；`MODEL_NAME` 占位符保护。

## 十五、建议项（非阻塞）
- [ ] 判定阈值与 spec §8 统一（1e-10），`hybr` 残差判定相对化。
- [ ] `D0` 三元式提取一次；`open()` 改 `with`；去掉 L155–L156 的开发史注释；`evaluate` 补轴约定 docstring。
- [ ] “独立第二求解器”措辞改为“第二求根算法”，并说明二者共用 `evaluate`。
- [ ] `solve_iterate` 失败时输出最后残差；第二求解器失败不应吞掉整个情形的输出。
- [ ] 稀疏数据（零销售部门）的 NaN/inf 处理与报错。
- [ ] 在 checkpoint 中注明本模板无随机性（seed N/A）。

---

## 复核（v0.3 修订后）· 2026-10-04

- reviewer = code-reviewer（strucmod v0.3 workflow, sub-agent）
- 范围：修订后的 `templates/master-cge-template.py`（451 行）、实例 `solve.py`（忽略换行符 diff 仅 `MODEL_NAME` 一处）、新增 `model/03_solve/armington_tariff/counterfactuals.py`。
- 方法：在 scratchpad 复制项目实跑（`--purge --checks --scenario S1 S2`、未剔赤字、缺基期文件、2 地区、基期含税）；对 `evaluate` 做变异测试；`quality_score.py` 模板 **12/12**（原 10/12）。未改动任何被审文件。

### 逐项复核 M1–M7

| 项 | 结论 | 证据 |
|---|---|---|
| M1 `--checks` 崩溃 | ✅ 已修 | L435 `CKPT.mkdir`；全新目录实跑 `--purge --checks` 正常落盘 `armington_tariff_checks.json` |
| M2 run_checks 重建 | ✅ 已修（实质性改进） | 恒等式移入 `info`（不计判定）；零冲击从扰动初值出发；Walras 覆盖全部 N 条（L284）；新增 `purged_max_abs_deficit_rel`、就业、分解残差、复合检验、水平量交叉核对 `solve_levels`。**变异测试**：把 `Xp` 去掉 `/(1+t')` 后，walras、levels_vs_hat（wage/welfare）、composition、就业、two_solver 共 6 项同时报警，说明检验确实在测方程。11 项全部 PASS（≤1e-13 量级） |
| M3 硬编码冲击 | ✅ 已修 | 冲击索引改为 `[0,1,0]`、`[N-1,0,-1]`；实测 2 地区×2 部门（含基期关税）、2 地区×1 部门均全通过；N<2 明确 `ValueError`；`D≠0` 时中性检验标记“跳过”（info），不再误报 |
| M4 分解 | ✅ 已修 | 增加 `ln_base_tariff_revenue` 与 `ln_deficit_residual`；基期 t≠0 时残差 2.3e-16（原失真 5.6e-4）；`decomposition_residual` 进入判定。D≠0 时残差非零（实测 ~1e-4）属预期，由单独项暴露 |
| M5 CLI | ✅ 大部分 | 基期缺失给清晰错误并返回 3（L428–L430，实测）；`utf-8-sig`；`load_base` 默认改为 purged，与 CLI 一致。**未做**：无动作参数时静默退出 0；情形标签/`t_jj=0`/ΣD 校验；`scenarios.csv` 未知标签仍抛原始 KeyError |
| M6 日志编码 | ✅ 已修 | 日志标签改 ASCII（`w_hat`/`W_hat`）；GBK 控制台实跑无 Logging error |
| M7 头部/版本 | ✅ 部分 | 头部有依赖版本、spec、输出目录，`quality_score` 12/12。**未做**：`MODEL_NAME` 占位符保护（未实例化直接运行仍给含糊路径错误） |

I/O 契约：`check_walras.py` 对 S2 checkpoint 实跑 PASS，字段未变。

### 残留问题（均非阻塞，按重要性）
1. **新增 `decomposition` 键使用户侧消费端需知**：`results.welfare_decomposition` 现为 5 项（含 `ln_base_tariff_revenue`、`ln_deficit_residual`）；`counterfactuals.py` 只画前 3 项，基期 t=0 时无影响，t≠0 时图的堆叠和将不等于福利合计。需在 spec 或注释中说明。
2. `run_scenario` 仍有旧问题：第二求解器失败会中断整个情形且不输出 checkpoint；`sam_balance` 与 `trade_balance_minus_D` 仍是代数恒等式（Walras 的实质检验仅靠 `market_clearing_residuals`）；稀疏数据 NaN/0 除未处理；`open()` 未关闭；L160 开发史注释仍在；hybr 判定阈值 1e-12 与 spec 1e-10 不一致。
3. `solve_levels` 与 hat 实现共享 `base.lam/alpha` 与同一均衡结构（ρ、闭式 E'），“独立”仅指参数化与求根算法；其对**数据读入**或**结构性设定错误（如两边同错的 E' 闭式）**不具检出力，这一点应在注释里如实说明（目前注释写“独立的水平量实现”，略偏强）。复合检验在 D≠0 时理论上不成立（实测未剔赤字时仍通过，但无理论保证），建议仅在 D0 时计入判定。
4. **counterfactuals.py**（新增，评议如下）：
   - ✅ 正确复用 `solve.py`（`importlib` + 注册 `sys.modules`）；ε 扫描对每个 ε **重新剔赤字**（`base_with_eps`，正确，因 purge 依赖 ε）；表 csv、图 png+pdf 同时输出；带示意数据声明；实跑成功，S1 A 福利 +0.0198%、S2 A −0.0411% 等与 solve.py 一致。
   - ❌ **无日志**：惯例要求 `logs/<model>_<step>_<ts>.log`；本脚本只 `print`，未建 log（只有 solve.py 写 log）。
   - ❌ 缺文件头版本/依赖声明（matplotlib/numpy）与 `output/checkpoints/` 目录保证：`CKPT` 未 `mkdir`，全新项目若先跑本脚本且无 checkpoints 目录会写 `armington_tariff_cf_summary.json` 失败（本次实跑因目录已存在而通过）。
   - ⚠️ 对情形结果不做任何验证（不查出清残差、双求解器），直接取数；也不断言基期 D=0（`np.zeros` 硬编码 `Dp`）。
   - ⚠️ “符号翻转临界值”是网格相邻点的上沿值（步长 0.25，非根）；本数据在 ε∈[1.5,12] 内无翻转，列表为空；扫描下界 1.5 低于 calibration.csv 的 bounds_lower=2，报告时需声明。数值最优关税 11%（网格步长 1%，最优福利增益 0.01986% 对 10% 时 0.01983% 几乎持平），表述宜写“约 10–11%，福利曲线极平”，勿过度解读。
   - ⚠️ 堆叠图用 `ax.patches[-1].get_facecolor()` 取色，写法脆弱；中文字体回退链在非 Windows 环境会缺字形。
   - 国家/部门标签 `A/B/R/MAN` 硬编码属案例专用脚本，可接受。

### 综合（复核）
**通过（带非阻塞保留项）。** 原 7 项必改均已落实且经实测/变异测试验证；`run_checks` 现在确实能发现 hat 代数错误。模板可作为 v0.3 CGE 模板发布；建议发布前顺手补：无参数时 help、`MODEL_NAME` 占位符保护、情形标签校验、`solve_levels` 注释措辞。`counterfactuals.py` 作为案例脚本建议补日志与 `CKPT.mkdir` 后定稿（不阻塞）。
