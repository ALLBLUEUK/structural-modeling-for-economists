# =====================================================================
# model/03_solve/<MODEL_NAME>/solve.py
# strucmod v0.3.0 · CGE 通用求解模板（多地区多部门 Armington，精确变化法）· Python
# 依赖：Python 3.10+，numpy 1.24+，scipy 1.10+
# spec：model/01_setup/<MODEL_NAME>/spec.md
# 输出目录：output/checkpoints/（检查点含 market_clearing_residuals 与 sam_balance，供 scripts/check_walras.py 读取）
#
# 无需 GAMS 授权。复制到 model/03_solve/<MODEL_NAME>/solve.py 后修改 MODEL_NAME 即可。
#
# 数据（登记于 data/calibration/<MODEL>/manifest.json）：
#   data/calibration/<MODEL>/trade_flows.csv   exporter,importer,sector,value（出厂价）
#   data/calibration/<MODEL>/base_tariffs.csv  可选：exporter,importer,sector,tariff（缺省为 0）
# 参数：model/02_calibrate/<MODEL>/calibration.csv   需含 eps_<sector>
# 情形：model/02_calibrate/<MODEL>/scenarios.csv     scenario,exporter,importer,sector,tariff_new
#
# 方法：Dekle, Eaton and Kortum (2008) 精确变化；Costinot and Rodríguez-Clare (2014) 多部门版本
#   c_ij^s  = ŵ_i d̂_ij^s (1+t'_ij^s)/(1+t_ij^s)
#   λ'_ij^s = λ_ij^s (c_ij^s)^(−ε_s) / Σ_k λ_kj^s (c_kj^s)^(−ε_s)        （λ 为含税支出份额）
#   P̂_j^s   = [Σ_k λ_kj^s (c_kj^s)^(−ε_s)]^(−1/ε_s)
#   E'_j    = (ŵ_j Y_j + D'_j)/(1 − ρ_j)，ρ_j = Σ_s α_j^s Σ_i t'/(1+t') λ'_ij^s，R'_j = ρ_j E'_j
#   出清    ŵ_i Y_i = Σ_j Σ_s λ'_ij^s α_j^s E'_j /(1+t'_ij^s)，计价单位 Σ ŵ_i Y_i = Σ Y_i
#   福利    Ŵ_j = (E'_j/E_j) / Π_s (P̂_j^s)^(α_j^s)
#
# 用法（项目根目录）：
#   python model/03_solve/<MODEL>/solve.py --purge            # 剔除基期赤字，写出新基期
#   python model/03_solve/<MODEL>/solve.py --scenario S1      # 跑 scenarios.csv 中的情形
#   python model/03_solve/<MODEL>/solve.py --checks           # 跑全部数值验证（零冲击/ACR/计价单位/双求解器）
# =====================================================================
from __future__ import annotations

import argparse
import csv
import json
import logging
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import root

MODEL_NAME = "armington_tariff"
ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "calibration" / MODEL_NAME
CALIB = ROOT / "model" / "02_calibrate" / MODEL_NAME
CKPT = ROOT / "output" / "checkpoints"
TABLES = ROOT / "output" / "tables"
LOGS = ROOT / "logs"

log = logging.getLogger(MODEL_NAME)


# ---------------------------------------------------------------------
# 0. 数据结构
# ---------------------------------------------------------------------
@dataclass
class Base:
    regions: list[str]
    sectors: list[str]
    X: np.ndarray      # X[i, j, s] 出厂价贸易流，i 出口方，j 进口方
    t: np.ndarray      # t[i, j, s] 基期关税（进口方 j 对来自 i 的 s）
    eps: np.ndarray    # eps[s]

    @property
    def Y(self):       # 产值 = 出厂销售
        return self.X.sum(axis=(1, 2))

    @property
    def gross(self):   # 含税支出流
        return self.X * (1.0 + self.t)

    @property
    def E(self):
        return self.gross.sum(axis=(0, 2))

    @property
    def R(self):
        return (self.X * self.t).sum(axis=(0, 2))

    @property
    def D(self):       # 赤字（正为赤字）
        return self.E - self.Y - self.R

    @property
    def alpha(self):   # alpha[j, s]
        return self.gross.sum(axis=0) / self.E[:, None]

    @property
    def lam(self):     # lam[i, j, s] 含税支出份额
        return self.gross / self.gross.sum(axis=0, keepdims=True)


def load_base(tariff_file: str | None = "base_tariffs.csv", flows_file: str = "trade_flows_purged.csv") -> Base:
    if not (DATA / flows_file).exists():
        raise FileNotFoundError(f"找不到基期数据 {DATA / flows_file}；如尚未剔除赤字，请先运行 --purge")
    rows = list(csv.DictReader(open(DATA / flows_file, encoding="utf-8-sig")))
    regions = sorted({r["exporter"] for r in rows} | {r["importer"] for r in rows})
    sectors = sorted({r["sector"] for r in rows})
    ri = {r: k for k, r in enumerate(regions)}
    si = {s: k for k, s in enumerate(sectors)}
    X = np.zeros((len(regions), len(regions), len(sectors)))
    for r in rows:
        X[ri[r["exporter"]], ri[r["importer"]], si[r["sector"]]] = float(r["value"])
    t = np.zeros_like(X)
    if tariff_file and (DATA / tariff_file).exists():
        for r in csv.DictReader(open(DATA / tariff_file, encoding="utf-8-sig")):
            t[ri[r["exporter"]], ri[r["importer"]], si[r["sector"]]] = float(r["tariff"])
    params = {r["parameter"]: float(r["value"])
              for r in csv.DictReader(open(CALIB / "calibration.csv", encoding="utf-8-sig"))}
    eps = np.array([params[f"eps_{s}"] for s in sectors])
    return Base(regions, sectors, X, t, eps)


# ---------------------------------------------------------------------
# 1. 给定 ŵ 的显式部分
# ---------------------------------------------------------------------
def evaluate(base: Base, what: np.ndarray, tp: np.ndarray, dhat: np.ndarray, Dp: np.ndarray):
    eps = base.eps[None, None, :]
    c = what[:, None, None] * dhat * (1.0 + tp) / (1.0 + base.t)
    num = base.lam * c ** (-eps)
    den = num.sum(axis=0, keepdims=True)
    lamp = num / den
    Phat = den[0] ** (-1.0 / base.eps[None, :])                     # Phat[j, s]
    rho = (base.alpha * (lamp * tp / (1.0 + tp)).sum(axis=0)).sum(axis=1)
    Ep = (what * base.Y + Dp) / (1.0 - rho)
    Rp = rho * Ep
    Xp = lamp * base.alpha[None, :, :] * Ep[None, :, None] / (1.0 + tp)  # 新出厂流
    sales = Xp.sum(axis=(1, 2))
    return dict(lamp=lamp, Phat=Phat, Ep=Ep, Rp=Rp, Xp=Xp, sales=sales)


def clearing_residuals(base, what, tp, dhat, Dp):
    ev = evaluate(base, what, tp, dhat, Dp)
    return what * base.Y - ev["sales"], ev


# ---------------------------------------------------------------------
# 2. 求解：主求解器（hybr）+ 独立第二求解器（阻尼超额需求迭代）
# ---------------------------------------------------------------------
def _numeraire(base, what, numeraire):
    if numeraire == "world":
        return (what * base.Y).sum() - base.Y.sum()
    return what[numeraire] - 1.0


def solve_hybr(base, tp, dhat, Dp, numeraire="world", drop=None, x0=None):
    N = len(base.regions)
    drop = N - 1 if drop is None else drop

    def F(x):
        res, _ = clearing_residuals(base, x, tp, dhat, Dp)
        res = res / base.Y.sum()
        res[drop] = _numeraire(base, x, numeraire) / base.Y.sum()
        return res

    sol = root(F, np.ones(N) if x0 is None else np.asarray(x0, float), method="hybr", tol=1e-13)
    # v0.3 修订：hybr 的 success 标记在接近机器精度时会误报失败（验收案例 ACR 检验中发现），
    # 改为直接以方程残差判定是否收敛。
    resid = np.max(np.abs(F(sol.x)))
    if resid > 1e-12:
        raise RuntimeError(f"hybr 求解失败：残差 {resid:.2e}（{sol.message}）")
    return sol.x, sol


def solve_iterate(base, tp, dhat, Dp, numeraire="world", damp=0.5, tol=1e-13, maxit=100000):
    what = np.ones(len(base.regions))
    for it in range(1, maxit + 1):
        _, ev = clearing_residuals(base, what, tp, dhat, Dp)
        new = what * (ev["sales"] / (what * base.Y)) ** damp
        if numeraire == "world":
            new = new * base.Y.sum() / (new * base.Y).sum()
        else:
            new = new / new[numeraire]
        diff = np.max(np.abs(new - what))
        what = new
        if diff < tol:
            return what, it
    raise RuntimeError("迭代求解器未收敛")


# ---------------------------------------------------------------------
# 3. 结果整理
# ---------------------------------------------------------------------
def outcomes(base: Base, what, tp, dhat, Dp):
    res, ev = clearing_residuals(base, what, tp, dhat, Dp)
    price = (ev["Phat"] ** base.alpha).prod(axis=1)
    What = (ev["Ep"] / base.E) / price
    sec_sales = base.X.sum(axis=1)                        # [i, s]
    sec_sales_p = ev["Xp"].sum(axis=1)
    Lhat = (sec_sales_p / sec_sales) / what[:, None]       # 部门就业变化
    L_check = (sec_sales * Lhat).sum(axis=1) / sec_sales.sum(axis=1) - 1.0   # Σ_s L^s L̂^s / L − 1
    decomp = {
        "ln_wage": np.log(what),
        "ln_tariff_revenue": np.log1p(ev["Rp"] / (what * base.Y)),
        "ln_base_tariff_revenue": -np.log1p(base.R / base.Y),        # 基期 t = 0 时为 0
        "ln_price_index": -np.log(price),
    }
    # 赤字非零时上述各项不再严格可加，剩余部分单列（D = 0 时应为 0）
    decomp["ln_deficit_residual"] = np.log(What) - sum(decomp.values())
    return dict(what=what, What=What, Phat=ev["Phat"], Ep=ev["Ep"], Rp=ev["Rp"], Xp=ev["Xp"],
                lamp=ev["lamp"], Lhat=Lhat, L_check=L_check, decomp=decomp,
                clearing_residuals=res, trade_balance=ev["Ep"] - what * base.Y - ev["Rp"])


def purge_deficits(base: Base) -> Base:
    """DEK (2008)：求解 D' = 0、关税不变的反事实，作为剔除赤字的新基期。"""
    N = len(base.regions)
    tp, dhat, Dp = base.t.copy(), np.ones_like(base.X), np.zeros(N)
    what, _ = solve_hybr(base, tp, dhat, Dp)
    out = outcomes(base, what, tp, dhat, Dp)
    return Base(base.regions, base.sectors, out["Xp"], base.t.copy(), base.eps.copy())


# ---------------------------------------------------------------------
# 4. 数值验证（spec §9）
# ---------------------------------------------------------------------
def solve_levels(base: Base, tp: np.ndarray, Dp: np.ndarray):
    """水平量实现（交叉核对用）：独立的代码路径与求解器，不调用 evaluate()；
    与精确变化法共享基期份额 λ、α 与均衡结构，因此检验的是实现，而非模型设定本身。

    基期 w = 1、L_i = Y_i；校准 a_ij^s = λ_ij^s (1+t_ij^s)^{ε_s}；用 Levenberg–Marquardt 求工资水平。
    """
    from scipy.optimize import least_squares
    N, S = len(base.regions), len(base.sectors)
    L, alpha, eps = base.Y.copy(), base.alpha.copy(), base.eps
    a = base.lam * (1.0 + base.t) ** eps[None, None, :]

    def shares_prices(w, tar):
        p = (w[:, None, None] * (1.0 + tar)) ** (-eps[None, None, :])
        tot = (a * p).sum(axis=0)                                   # [j, s]
        return a * p / tot[None], tot ** (-1.0 / eps[None, :])

    def system(w):
        sh, _ = shares_prices(w, tp)
        rho = np.array([sum(alpha[j, s] * sum(sh[i, j, s] * tp[i, j, s] / (1 + tp[i, j, s]) for i in range(N))
                            for s in range(S)) for j in range(N)])
        expend = (w * L + Dp) / (1.0 - rho)
        out = np.empty(N)
        for i in range(N):
            out[i] = w[i] * L[i] - sum(sh[i, j, s] * alpha[j, s] * expend[j] / (1 + tp[i, j, s])
                                       for j in range(N) for s in range(S))
        out[-1] = (w * L).sum() - L.sum()
        return out / L.sum(), expend

    sol = least_squares(lambda w: system(w)[0], np.ones(N), method="lm", xtol=1e-15, ftol=1e-15, gtol=1e-15)
    w = sol.x
    _, expend1 = system(w)
    _, P1 = shares_prices(w, tp)
    _, P0 = shares_prices(np.ones(N), base.t)
    welfare = (expend1 / base.E) / ((P1 / P0) ** alpha).prod(axis=1)
    return w, welfare


def run_checks(base: Base):
    """返回 (计入判定的检验, 仅供参考的信息)。"""
    N = len(base.regions)
    if N < 2:
        raise ValueError("至少需要 2 个地区")
    ones = np.ones_like(base.X)
    D0 = abs(base.D).max() / base.Y.sum() < 1e-9
    Dp = np.zeros(N) if D0 else base.D.copy()
    checks, info = {}, {}
    # 会计恒等式（按构造必然成立，只作展示，不计入判定）
    info["identity_world_deficit_sum"] = float(abs(base.D.sum()))
    info["identity_income_equals_sales"] = float(np.max(np.abs(base.Y - base.X.sum(axis=(1, 2)))))
    info["identity_expenditure"] = float(np.max(np.abs(base.E - (base.Y + base.R + base.D))))
    # 9.2 剔除赤字后各地区贸易余额为 0
    checks["purged_max_abs_deficit_rel"] = float(abs(base.D).max() / base.Y.sum())
    # 9.3 零冲击：从扰动初值出发
    x0 = np.ones(N) + 0.05 * np.linspace(-1, 1, N)
    w0, _ = solve_hybr(base, base.t.copy(), ones, Dp, x0=x0)
    o0 = outcomes(base, w0, base.t.copy(), ones, Dp)
    checks["zero_shock_what_dev"] = float(np.max(np.abs(w0 - 1.0)))
    checks["zero_shock_What_dev"] = float(np.max(np.abs(o0["What"] - 1.0)))
    # 非平凡检验冲击：地区 1 对来自地区 0 的第 0 部门加征 10%，地区 0 对来自地区 N−1 的最后一个部门加征 5%
    tp = base.t.copy()
    tp[0, 1, 0] += 0.10
    tp[N - 1, 0, -1] += 0.05
    wH, _ = solve_hybr(base, tp, ones, Dp)
    oH = outcomes(base, wH, tp, ones, Dp)
    # 9.4 Walras：全部出清方程（含被删去的一条）
    checks["walras_max_clearing_rel"] = float(np.max(np.abs(oH["clearing_residuals"])) / base.Y.sum())
    # 9.5 计价单位中性（仅 D = 0 时有意义）
    if D0:
        wA, _ = solve_hybr(base, tp, ones, Dp, numeraire=0)
        oA = outcomes(base, wA, tp, ones, Dp)
        checks["numeraire_neutrality_What_diff"] = float(np.max(np.abs(oH["What"] - oA["What"])))
    else:
        info["numeraire_neutrality"] = "跳过：基期 D ≠ 0 时计价单位不中性（spec §5），请先 --purge"
    # 9.6' 独立实现交叉核对（替代原 ACR 检验：后者在单部门、D = 0 下是代数恒等式，不检验求解器）
    wL, WL = solve_levels(base, tp, Dp)
    checks["levels_vs_hat_wage_diff"] = float(np.max(np.abs(wL - wH)))
    checks["levels_vs_hat_welfare_diff"] = float(np.max(np.abs(WL - oH["What"])))
    # 复合检验：0 → t1 → t2 与 0 → t2 一致
    t1 = base.t.copy()
    t1[0, 1, 0] += 0.05
    w1, _ = solve_hybr(base, t1, ones, Dp)
    o1 = outcomes(base, w1, t1, ones, Dp)
    mid = Base(base.regions, base.sectors, o1["Xp"], t1, base.eps.copy())
    w12, _ = solve_hybr(mid, tp, ones, Dp)
    o12 = outcomes(mid, w12, tp, ones, Dp)
    checks["composition_welfare_diff"] = float(np.max(np.abs(o1["What"] * o12["What"] - oH["What"])))
    # 9.7 部门就业加总；福利分解可加
    checks["sector_employment_adding_up"] = float(np.max(np.abs(oH["L_check"])))
    checks["decomposition_residual"] = float(np.max(np.abs(oH["decomp"]["ln_deficit_residual"])))
    # 9.8 两个求解器一致（二者共享 evaluate()，只检验求根，不检验方程；方程由水平量交叉核对检验）
    wI, it = solve_iterate(base, tp, ones, Dp)
    checks["two_solver_what_diff"] = float(np.max(np.abs(wI - wH)))
    info["iterate_solver_iterations"] = int(it)
    # ACR 公式一致性（仅展示，不计入判定）
    Xs = base.X.sum(axis=2, keepdims=True)
    b1 = purge_deficits(Base(base.regions, ["ALL"], Xs, np.zeros_like(Xs), np.array([base.eps.mean()])))
    dh = np.ones_like(b1.X)
    dh[0, 1, 0] = 1.25
    wa, _ = solve_hybr(b1, b1.t, dh, np.zeros(N))
    oa = outcomes(b1, wa, b1.t, dh, np.zeros(N))
    acr = np.array([oa["lamp"][j, j, 0] / b1.lam[j, j, 0] for j in range(N)]) ** (-1.0 / b1.eps[0])
    info["acr_formula_consistency"] = float(np.max(np.abs(oa["What"] - acr)))
    return checks, info


CHECK_TOL = {
    "purged_max_abs_deficit_rel": 1e-9, "zero_shock_what_dev": 1e-12, "zero_shock_What_dev": 1e-12,
    "walras_max_clearing_rel": 1e-10, "numeraire_neutrality_What_diff": 1e-9,
    "levels_vs_hat_wage_diff": 1e-9, "levels_vs_hat_welfare_diff": 1e-9, "composition_welfare_diff": 1e-9,
    "sector_employment_adding_up": 1e-9, "decomposition_residual": 1e-9, "two_solver_what_diff": 1e-9,
}


# ---------------------------------------------------------------------
# 5. 情形
# ---------------------------------------------------------------------
def load_scenario(base: Base, name: str) -> np.ndarray:
    ri = {r: k for k, r in enumerate(base.regions)}
    si = {s: k for k, s in enumerate(base.sectors)}
    tp = base.t.copy()
    found = False
    for r in csv.DictReader(open(CALIB / "scenarios.csv", encoding="utf-8-sig")):
        if r["scenario"] == name:
            tp[ri[r["exporter"]], ri[r["importer"]], si[r["sector"]]] = float(r["tariff_new"])
            found = True
    if not found:
        raise KeyError(f"scenarios.csv 中没有情形 {name}")
    return tp


def run_scenario(base: Base, name: str, tp: np.ndarray, tag: str = "") -> dict:
    N = len(base.regions)
    dhat, Dp = np.ones_like(base.X), base.D.copy()
    w1, _ = solve_hybr(base, tp, dhat, Dp)
    w2, it = solve_iterate(base, tp, dhat, Dp)
    o = outcomes(base, w1, tp, dhat, Dp)
    reg = base.regions
    out = {
        "model": MODEL_NAME,
        "scenario": name + tag,
        "regions": reg, "sectors": base.sectors,
        "eps": base.eps.tolist(),
        "results": {
            "wage_change": dict(zip(reg, o["what"].tolist())),
            "welfare_change": dict(zip(reg, o["What"].tolist())),
            "welfare_decomposition": {k: dict(zip(reg, v.tolist())) for k, v in o["decomp"].items()},
            "tariff_revenue_share_of_income": dict(zip(reg, (o["Rp"] / (o["what"] * base.Y)).tolist())),
            "sector_employment_change": {reg[i]: dict(zip(base.sectors, o["Lhat"][i].tolist())) for i in range(N)},
            "bilateral_flow_change": {f"{reg[i]}->{reg[j]}:{s}": float(o["Xp"][i, j, k] / base.X[i, j, k])
                                      for i in range(N) for j in range(N) for k, s in enumerate(base.sectors)
                                      if base.X[i, j, k] > 0},
        },
        "market_clearing_residuals": {f"clearing_{reg[i]}": float(o["clearing_residuals"][i] / base.Y.sum())
                                      for i in range(N)},
        "sam_balance": {"rows": (o["what"] * base.Y + o["Rp"] + Dp).tolist(), "cols": o["Ep"].tolist()},
        "diagnostics": {
            "two_solver_what_diff": float(np.max(np.abs(w1 - w2))),
            "iterate_solver_iterations": int(it),
            "sector_employment_adding_up": float(np.max(np.abs(o["L_check"]))),
            "trade_balance_minus_D": float(np.max(np.abs(o["trade_balance"] - Dp))),
        },
        "env": {"os": platform.platform(), "python": platform.python_version(),
                "numpy": np.__version__, "scipy": scipy.__version__},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "示意数据，结论仅为机制示范",
    }
    d = out["diagnostics"]
    out["validated"] = bool(max(abs(v) for v in out["market_clearing_residuals"].values()) < 1e-10
                            and d["two_solver_what_diff"] < 1e-9
                            and d["sector_employment_adding_up"] < 1e-9)
    CKPT.mkdir(parents=True, exist_ok=True)
    (CKPT / f"{MODEL_NAME}_{name}{tag}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                                         encoding="utf-8")
    log.info("[%s%s] w_hat=%s  W_hat=%s  validated=%s", name, tag,
             np.round(o["what"], 6).tolist(), np.round(o["What"], 6).tolist(), out["validated"])
    return out


def save_base(base: Base, fname: str):
    with open(DATA / fname, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["exporter", "importer", "sector", "value"])
        for i, ri_ in enumerate(base.regions):
            for j, rj in enumerate(base.regions):
                for k, s in enumerate(base.sectors):
                    w.writerow([ri_, rj, s, f"{base.X[i, j, k]:.10f}"])


def main() -> int:
    ap = argparse.ArgumentParser(description=f"{MODEL_NAME}（strucmod v0.3 CGE 模板）")
    ap.add_argument("--purge", action="store_true", help="剔除基期赤字，写出 trade_flows_purged.csv")
    ap.add_argument("--scenario", action="append", default=[])
    ap.add_argument("--checks", action="store_true")
    ap.add_argument("--flows", default="trade_flows_purged.csv", help="情形与检验所用基期数据")
    args = ap.parse_args()

    LOGS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(LOGS / f"{MODEL_NAME}_solve_{ts}.log", encoding="utf-8")])
    rc = 0
    if args.purge:
        raw = load_base(flows_file="trade_flows.csv")
        log.info("raw base: Y=%s  D=%s  sum(D)=%.2e", raw.Y.round(3).tolist(), raw.D.round(3).tolist(), raw.D.sum())
        purged = purge_deficits(raw)
        save_base(purged, "trade_flows_purged.csv")
        log.info("purged base: Y=%s  max|D|=%.2e", purged.Y.round(3).tolist(), np.abs(purged.D).max())
    base = load_base(flows_file=args.flows) if (DATA / args.flows).exists() else None
    if (args.checks or args.scenario) and base is None:
        log.error("找不到基期数据 %s；请先运行 --purge", DATA / args.flows)
        return 3
    if args.checks:
        checks, info = run_checks(base)
        status = {k: bool(v < CHECK_TOL[k]) for k, v in checks.items()}
        ok = all(status.values())
        CKPT.mkdir(parents=True, exist_ok=True)
        (CKPT / f"{MODEL_NAME}_checks.json").write_text(json.dumps(
            {"model": MODEL_NAME, "checks": checks, "tolerance": {k: CHECK_TOL[k] for k in checks},
             "pass": status, "all_pass": ok, "info_not_counted": info,
             "timestamp": datetime.now(timezone.utc).isoformat()}, indent=2, ensure_ascii=False), encoding="utf-8")
        for k, v in checks.items():
            log.info("check %-34s %.3e  tol %.0e  %s", k, v, CHECK_TOL[k], "PASS" if status[k] else "FAIL")
        log.info("info (not counted): %s", info)
        rc = rc or (0 if ok else 2)
    for name in args.scenario:
        out = run_scenario(base, name, load_scenario(base, name))
        rc = rc or (0 if out["validated"] else 2)
    return rc


if __name__ == "__main__":
    sys.exit(main())
