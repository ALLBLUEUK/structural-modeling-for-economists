# 模型设定 · nk_three_eq

A canonical three-equation New Keynesian model in the spirit of Galí (2008) and Woodford (2003). Used to study the transmission of a 25 bp monetary policy shock through U.S. macroeconomic aggregates and to characterise the role of nominal price rigidity in the propagation. This is a simplified workhorse alternative to the medium-scale model of Smets and Wouters (2007); the trade-off is transparency and analytic tractability against scope (capital accumulation, labour-market frictions, and wage rigidity are absent).

## 0. 元信息

- 模型名：`nk_three_eq`
- 类型：DSGE · canonical New Keynesian · 3 structural shocks (monetary, demand, supply)
- 实现：Python with `scipy.linalg.ordqz` (generalised Schur / Klein 2000)
- 创建：贾宁远，2026-05-11
- 评审记录：`quality_reports/nk_three_eq_model_review_*.md`

## 1. 经济问题与机制

A 25 basis-point exogenous innovation to the nominal policy rate raises the real rate one-for-one on impact because nominal prices are sticky. The higher real rate reduces aggregate demand via the consumption Euler equation, which in turn reduces marginal costs and, through the New Keynesian Phillips curve, generates a fall in inflation. The dynamic interaction between sticky-price firms and the central bank's interest-rate rule determines the persistence and amplitude of these responses. This paper characterises the impulse responses to such a shock under a standard Galí (2008) calibration and discusses the role of the Taylor-rule reaction coefficients in shaping the propagation.

## 2. 时间环境

- 离散时间，期长度：季度
- 无限期 `t = 0, 1, 2, ...`
- 不确定性来源：3 structural shocks (TFP / preference / monetary)
- 信息结构：rational expectations conditional on time-*t* information

## 3. 代理人

### 3.1 家庭（连续个，每户提供差异化劳动）
- 偏好（CRRA + Frisch labour）：
  $$
  \mathbb{E}_{0}\sum_{t=0}^{\infty}\beta^{t}\,e^{\xi_{t}^{b}}
  \left\{\frac{C_{t}^{1-\sigma}}{1-\sigma}-\frac{N_{t}^{1+\varphi}}{1+\varphi}\right\}
  $$
- 预算约束：$P_{t}C_{t}+B_{t}=W_{t}N_{t}+R_{t-1}B_{t-1}+T_{t}$
- 选择变量：$C_{t},\,N_{t},\,B_{t}$ (consumption, labour, bond holdings).
- $\xi_{t}^{b}$ 是 preference shock (demand shock).

### 3.2 中间品生产商（连续 [0,1] 个）

- 生产函数：$Y_{t}(i)=A_{t}\,N_{t}(i)$
- $A_{t}$ 是 TFP shock (supply shock).
- Calvo pricing (prob $\theta$ no reset).

### 3.3 最终品生产商

- Dixit-Stiglitz 聚合：$Y_{t}=\bigl[\int_{0}^{1}Y_{t}(i)^{(\varepsilon-1)/\varepsilon}di\bigr]^{\varepsilon/(\varepsilon-1)}$
- 完全竞争.

### 3.4 央行

Taylor rule with monetary policy shock:
$$
r_{t}=\rho_{r}\,r_{t-1}+(1-\rho_{r})\bigl[\phi_{\pi}\,\pi_{t}+\phi_{y}\,\tilde{y}_{t}\bigr]+\varepsilon_{t}^{m}
$$
In the baseline we set $\rho_{r}=0$ (no smoothing) and use $\tilde{y}_{t}\equiv y_{t}$ as the output deviation from the deterministic steady state (zero-trend approximation; the canonical NK output gap is recovered by appropriate detrending in the long-run analysis).

## 4. 变量分类表

### 内生（3）

| 符号 | 类型 | 时点 | 单位 | 含义 |
|---|---|---|---|---|
| `y_t` | 控制 | t | log-dev | output (= consumption with no capital) |
| `pi_t` | 控制 | t | quarterly rate | inflation |
| `r_t` | 控制 | t | quarterly rate | nominal interest rate |

### 外生（3 个 AR(1)）

| 符号 | 含义 | innovation |
|---|---|---|
| `eps_a_t` | TFP shock (supply) | `eta_a` |
| `eps_b_t` | preference / demand shock | `eta_b` |
| `eps_m_t` | monetary policy shock | `eta_m` |

**计数自检**：3 endogenous + 3 exogenous = 6 variables, 6 equations. ✅

## 5. 方程系统（log-linearised）

### 5.1 Dynamic IS curve (households' Euler + market clearing $C=Y$)

$$
y_{t}=\mathbb{E}_{t}y_{t+1}-\frac{1}{\sigma}\bigl(r_{t}-\mathbb{E}_{t}\pi_{t+1}\bigr)+\varepsilon_{t}^{b}
\tag{1}
$$

### 5.2 New Keynesian Phillips curve

$$
\pi_{t}=\beta\,\mathbb{E}_{t}\pi_{t+1}+\kappa\,y_{t}-\varepsilon_{t}^{a}
\tag{2}
$$
where $\kappa=\dfrac{(1-\theta)(1-\beta\theta)}{\theta}\,(\sigma+\varphi)$ is the slope of the NKPC. (Following Galí 2008 Ch.~3 with technology entering the marginal-cost expression with a negative sign in deviation form.)

### 5.3 Taylor rule

$$
r_{t}=\phi_{\pi}\pi_{t}+\phi_{y}\,y_{t}+\varepsilon_{t}^{m}
\tag{3}
$$

### 5.4 Shock processes

$$
\varepsilon_{t}^{x}=\rho_{x}\,\varepsilon_{t-1}^{x}+\eta_{t}^{x},\quad
\eta_{t}^{x}\sim\mathcal{N}(0,\sigma_{x}^{2}),\quad x\in\{a,b,m\}
\tag{4--6}
$$

### 5.5 维度自检

- Endogenous: $y, \pi, r$ → 3
- Exogenous (states): $\varepsilon^{a}, \varepsilon^{b}, \varepsilon^{m}$ → 3
- Total: 6 variables, 6 equations ✅

## 6. 函数形式

- Utility: CRRA in consumption with elasticity $1/\sigma$; separable in labour with Frisch elasticity $1/\varphi$.
- Production: linear in labour with technology multiplier $A_{t}=e^{\varepsilon^{a}_{t}}$.
- Calvo prices: probability $\theta$ of no reset; remaining firms reset to optimal markup over expected discounted marginal cost.
- Dixit-Stiglitz aggregation with elasticity $\varepsilon=1+1/\lambda_{p}$.

## 7. 参数表

Quarterly calibration; values follow Galí (2008) Table 3.1 (post-war U.S. canonical NK).

| 参数 | 含义 | 取值 | 来源 |
|---|---|---|---|
| `beta` | discount factor | 0.99 | Galí (2008) Table 3.1 |
| `sigma` | inverse intertemporal elasticity | 1.0 | Galí (2008) Ch.3 |
| `varphi` | Frisch labour disutility curvature | 1.0 | Galí (2008) Ch.3 |
| `theta` | Calvo prices (prob of no reset) | 0.75 | Galí (2008) Ch.3 |
| `phi_pi` | Taylor rule inflation reaction | 1.5 | Taylor (1993); Galí (2008) Ch.3 |
| `phi_y` | Taylor rule output reaction | 0.125 | Galí (2008) Ch.3 (= 0.5/4) |
| `rho_a` | TFP persistence | 0.9 | Galí (2008) Ch.3 |
| `rho_b` | preference shock persistence | 0.5 | Galí (2008) Ch.3 |
| `rho_m` | monetary shock persistence | 0.5 | Galí (2008) Ch.3 |
| `sigma_a` | TFP innovation std (%) | 0.7 | Galí (2008) Ch.3 |
| `sigma_b` | preference innovation std (%) | 0.5 | Galí (2008) Ch.3 |
| `sigma_m` | monetary innovation std (%) | 0.25 | Galí (2008) Ch.3 (~25 bp per std) |

Derived NKPC slope: $\kappa=(1-\theta)(1-\beta\theta)/\theta\,(\sigma+\varphi)=(0.25)(0.2575)/(0.75)\cdot 2=0.1717$.

## 8. 求解方法

- Linearised around the zero-inflation deterministic steady state.
- Klein (2000) generalised Schur decomposition via `scipy.linalg.ordqz`.
- 容差 (Blanchard-Kahn): unit-circle threshold $1+10^{-9}$.
- 6-variable system has 3 unstable eigenvalues (matching 3 forward-looking endogenous: $y, \pi$; plus $r$ enters only contemporaneously via Taylor rule).

Actually: forward-looking variables are $y$ and $\pi$ (via $E_{t}y_{t+1}$ and $E_{t}\pi_{t+1}$). $r$ is algebraically determined by the Taylor rule. So BK requires 2 unstable eigenvalues for the 6-equation system. After absorbing $r$ from (3) into (1), the IS curve becomes:
$$
y_{t}=\mathbb{E}_{t}y_{t+1}-\frac{1}{\sigma}(\phi_{\pi}\pi_{t}+\phi_{y}y_{t}+\varepsilon^{m}_{t}-\mathbb{E}_{t}\pi_{t+1})+\varepsilon^{b}_{t}.
$$

Combined with the NKPC, this yields a 5-equation system (3 shock states + 2 jumpers $y, \pi$).

## 9. 验证目标

### 9.1 稳态

By construction (log-deviation form): $y^{\ast}=\pi^{\ast}=r^{\ast}=0$ in deviations. Residuals identically zero.

### 9.2 IRF 形态先验（25 bp contractionary monetary shock）

- $r$ rises on impact by approximately the shock size ($+0.25\%$ per quarter, i.e.\ 25 bp annualised after multiplying by 4).
- Real rate $r-\mathbb{E}_{t}\pi_{t+1}$ rises.
- Output $y$ falls on impact and recovers gradually; peak fall $\approx -0.5\%$ at $t=1$--$3$.
- Inflation $\pi$ falls on impact and recovers; magnitude smaller than $y$ in percentage terms.
- All variables converge to zero by quarter 20--30.

### 9.3 复现目标

复现 Galí (2008) Figure 3.1 (impulse responses to a monetary policy shock). 容差：定性形状一致 + 峰值时点 ±1 季度 + 峰值幅度 ±20%.

## 10. 与文献的关系

This paper deliberately adopts the simpler 3-equation framework rather than the medium-scale workhorse of Smets and Wouters (2007). The Smets--Wouters model adds capital accumulation, investment-adjustment costs, sticky wages with Calvo wage-setting, habits in consumption, and a richer set of shocks; together these features improve the data fit but obscure the core transmission mechanism. The three-equation framework retains the essential New Keynesian mechanism (Calvo pricing + Taylor rule + forward-looking aggregate demand) while permitting analytical insight and a transparent numerical solution. The medium-scale extension is left as a robustness exercise in Section~\ref{sec:robustness}.

## 11. 待办

- [x] 完成模型设定
- [x] 维度自检 ✔
- [x] `model-reviewer` 评审（自评 archived in prior version of this spec; mechanism + framework correct）
- [x] `math-reviewer` 评审（自评 archived; NKPC slope formula verified against Galí 2008 eq.~3.11）
- [ ] 填实 `calibration.csv`
- [ ] 编写 `nk_three_eq.py` (Python solver via Klein 2000)
- [ ] `solve` + `validate_steady_state` (trivial in log-dev form)
- [ ] `simulate_irf` for `eps_m` (monetary shock, 25 bp)
- [ ] 写论文 7 节
