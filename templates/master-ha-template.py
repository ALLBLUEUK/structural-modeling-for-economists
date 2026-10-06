# =====================================================================
# model/03_solve/<MODEL_NAME>/solve.py
# strucmod v0.3.0 · 异质主体（Aiyagari / Bewley）通用求解模板 · Python
# 依赖：Python 3.10+，numpy 1.24+，scipy 1.10+
# spec：model/01_setup/<MODEL_NAME>/spec.md
#
# 复制到 model/03_solve/<MODEL_NAME>/solve.py 后，修改 MODEL_NAME 即可使用。
# 参数从 model/02_calibrate/<MODEL_NAME>/calibration.csv 读取（列：parameter,value,...）。
#
# 方法：
#   家庭问题   内生网格法 EGM（Carroll 2006）
#   平稳分布   Young (2010) 非随机模拟（彩票法）
#   一般均衡   Brent 法求资本市场出清利率；网格随借贷下限 φ(r) 重建
#   收入过程   Rouwenhorst（默认，高持续性下精确匹配方差与自相关）或 Tauchen (1986)；归一化 E[z] = 1
#
# 输出（遵循 strucmod 输入/输出契约）：
#   output/checkpoints/<MODEL>_<scenario>_ss.json   稳态 + 残差 + 诊断（可被 scripts/check_steady_state.py 读取）
#   output/checkpoints/<MODEL>_ss.json              baseline 情形的副本（供 scripts/run_pipeline.sh 读取）
#   output/checkpoints/<MODEL>_<scenario>_arrays.npz 网格、策略函数、分布
#   logs/<MODEL>_solve_<scenario>_<ts>.log
#
# 用法（在项目根目录）：
#   python model/03_solve/<MODEL>/solve.py --scenario baseline
#   python model/03_solve/<MODEL>/solve.py --scenario b2 --set b=2
# =====================================================================
from __future__ import annotations

import argparse
import csv
import json
import logging
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.optimize import brentq
from scipy.stats import norm

MODEL_NAME = "<MODEL_NAME>"
ROOT = Path(__file__).resolve().parents[3]          # 项目根目录
CALIB = ROOT / "model" / "02_calibrate" / MODEL_NAME / "calibration.csv"
CKPT = ROOT / "output" / "checkpoints"
LOGS = ROOT / "logs"
SEED_FILE = ROOT / "model" / "_utils" / "seed.txt"

log = logging.getLogger(MODEL_NAME)


# ---------------------------------------------------------------------
# 0. 读入
# ---------------------------------------------------------------------
def load_params(path: Path, overrides: dict[str, float]) -> dict[str, float]:
    p: dict[str, float] = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            p[row["parameter"]] = float(row["value"])
    allowed_extra = {"r_hi_eps", "r_lo_eps", "use_rouwenhorst", "n_scan"}
    unknown = [k for k in overrides if k not in p and k not in allowed_extra]
    if unknown:
        raise KeyError(f"--set 中有未知参数：{unknown}（calibration.csv 中没有）")
    p.update(overrides)
    for k in ("n_z", "n_a"):
        p[k] = int(p[k])
    return p


# ---------------------------------------------------------------------
# 1. 收入过程：Tauchen 离散 + 归一化
# ---------------------------------------------------------------------
def tauchen(rho: float, sigma_uncond: float, n: int, m: float):
    """log z' = rho log z + eps；网格宽度 ±m·σ（无条件），区间概率按 σ_ε = σ√(1−ρ²)。"""
    sig_e = sigma_uncond * np.sqrt(1.0 - rho**2)
    x = np.linspace(-m * sigma_uncond, m * sigma_uncond, n)
    step = x[1] - x[0]
    P = np.empty((n, n))
    for i in range(n):
        mu = rho * x[i]
        P[i, 0] = norm.cdf((x[0] - mu + step / 2) / sig_e)
        P[i, -1] = 1.0 - norm.cdf((x[-1] - mu - step / 2) / sig_e)
        for j in range(1, n - 1):
            P[i, j] = (norm.cdf((x[j] - mu + step / 2) / sig_e)
                       - norm.cdf((x[j] - mu - step / 2) / sig_e))
    # 平稳分布
    vals, vecs = np.linalg.eig(P.T)
    pi = np.real(vecs[:, np.argmin(np.abs(vals - 1.0))])
    pi = pi / pi.sum()
    z = np.exp(x)
    z = z / (z @ pi)                                 # 归一化 E[z] = 1
    # 离散化质量
    logz = np.log(z)
    mean = logz @ pi
    var = ((logz - mean) ** 2) @ pi
    autocov = sum(pi[i] * P[i, j] * (logz[i] - mean) * (logz[j] - mean)
                  for i in range(n) for j in range(n))
    quality = {"var_logz": float(var), "target_var": float(sigma_uncond**2),
               "autocorr": float(autocov / var), "target_rho": float(rho)}
    return z, P, pi, quality


def rouwenhorst(rho: float, sigma_uncond: float, n: int):
    """Rouwenhorst 离散：网格 ±√(n−1)·σ，p = q = (1+ρ)/2；精确匹配无条件方差与一阶自相关。"""
    p_ = (1.0 + rho) / 2.0
    P = np.array([[p_, 1 - p_], [1 - p_, p_]])
    for k in range(3, n + 1):
        Z = np.zeros((k, k))
        Z[:k - 1, :k - 1] += p_ * P
        Z[:k - 1, 1:] += (1 - p_) * P
        Z[1:, :k - 1] += (1 - p_) * P
        Z[1:, 1:] += p_ * P
        Z[1:k - 1, :] /= 2.0
        P = Z
    x = np.linspace(-np.sqrt(n - 1) * sigma_uncond, np.sqrt(n - 1) * sigma_uncond, n)
    return x, P


def income_process(p: dict):
    """返回 (z, P, π_z, 离散化质量)。p['use_rouwenhorst'] = 1（默认）或 0（Tauchen, 宽度 p['m']）。"""
    n, rho, sig = p["n_z"], p["rho"], p["sigma"]
    if p.get("use_rouwenhorst", 1.0) >= 0.5:
        x, P = rouwenhorst(rho, sig, n)
        method = "rouwenhorst"
    else:
        z_t, P, _, _ = tauchen(rho, sig, n, p["m"])
        x = np.log(z_t)
        method = "tauchen"
    vals, vecs = np.linalg.eig(P.T)
    pi = np.real(vecs[:, np.argmin(np.abs(vals - 1.0))])
    pi = pi / pi.sum()
    z = np.exp(x)
    z = z / (z @ pi)
    logz = np.log(z)
    mean = logz @ pi
    var = ((logz - mean) ** 2) @ pi
    autocov = float((pi[:, None] * P * np.outer(logz - mean, logz - mean)).sum())
    quality = {"method": method, "var_logz": float(var), "target_var": float(sig**2),
               "autocorr": autocov / float(var), "target_rho": float(rho)}
    quality["var_rel_error"] = abs(quality["var_logz"] / quality["target_var"] - 1.0)
    quality["autocorr_abs_error"] = abs(quality["autocorr"] - rho)
    return z, P, pi, quality


# ---------------------------------------------------------------------
# 2. 价格与借贷下限
# ---------------------------------------------------------------------
def prices(r: float, p: dict) -> tuple[float, float]:
    """给定 r：企业资本需求 K^d（L = 1）与工资 w。"""
    Kd = (p["alpha"] / (r + p["delta"])) ** (1.0 / (1.0 - p["alpha"]))
    w = (1.0 - p["alpha"]) * Kd ** p["alpha"]
    return Kd, w


def borrowing_limit(r: float, w: float, zmin: float, b: float) -> tuple[float, float]:
    """φ(r)：r ≤ 0 时为 b；r > 0 时为 min{b, w z_min / r}。返回 (φ, 自然上限)。"""
    if r <= 0:
        return b, float("inf")
    nat = w * zmin / r
    return min(b, nat), nat


def asset_grid(phi: float, a_max: float, n: int, curv: float = 2.0) -> np.ndarray:
    return -phi + (a_max + phi) * np.linspace(0.0, 1.0, n) ** curv


# ---------------------------------------------------------------------
# 3. 家庭问题：EGM
# ---------------------------------------------------------------------
def solve_household(r, w, a, z, P, p, c_init=None, tol=1e-10, maxit=5000):
    mu, beta = p["mu"], p["beta"]
    na, nz = a.size, z.size
    R = 1.0 + r
    coh = R * a[:, None] + w * z[None, :]            # 手头现金
    c = c_init if c_init is not None else np.maximum(coh - a[0], 1e-10) * 0.5 + 1e-3
    for it in range(1, maxit + 1):
        Emu = (c ** (-mu)) @ P.T                     # Emu[i', z] = Σ_z' P(z,z') u'(c(a_i', z'))
        c_endo = (beta * R * Emu) ** (-1.0 / mu)     # 由 Euler 等式反解当期消费
        a_endo = (c_endo + a[:, None] - w * z[None, :]) / R
        a_new = np.empty((na, nz))
        for j in range(nz):
            a_new[:, j] = np.interp(a, a_endo[:, j], a)
            a_new[a < a_endo[0, j], j] = a[0]          # 低于内生网格下端：撞约束
        c_new = coh - a_new
        if not np.all(np.isfinite(c_new)) or np.any(c_new <= 0):
            raise FloatingPointError(f"EGM 第 {it} 次迭代出现非正或非有限消费（φ 可能触及自然借贷上限）")
        diff = np.max(np.abs(c_new - c))
        c = c_new
        if diff < tol:
            return c, a_new, it, diff
    raise RuntimeError(f"EGM 未在 {maxit} 次内收敛（diff={diff:.2e}）")


# ---------------------------------------------------------------------
# 4. 平稳分布：Young (2010) 彩票法
# ---------------------------------------------------------------------
def stationary_distribution(a, a_pol, P, tol=1e-12, maxit=100000):
    na, nz = a_pol.shape
    idx = np.clip(np.searchsorted(a, a_pol, side="right") - 1, 0, na - 2)
    wt_hi = np.clip((a_pol - a[idx]) / (a[idx + 1] - a[idx]), 0.0, 1.0)
    rows, cols, vals = [], [], []
    for j in range(nz):
        for jp in range(nz):
            if P[j, jp] == 0:
                continue
            s = np.arange(na) + j * na
            rows += [s, s]
            cols += [idx[:, j] + jp * na, idx[:, j] + 1 + jp * na]
            vals += [(1 - wt_hi[:, j]) * P[j, jp], wt_hi[:, j] * P[j, jp]]
    T = sparse.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                          shape=(na * nz, na * nz))
    TT = T.T.tocsr()
    n = na * nz
    # v0.3 修订：先直接解线性方程组 (T' − I) d = 0, Σd = 1（用最后一行替换为归一化条件），
    # 再用迭代打磨。纯迭代法在 β(1+r) → 1 时收敛极慢（验收案例 σ→0 极限检验中发现）。
    A = (TT - sparse.identity(n, format="csr")).tolil()
    A[n - 1, :] = np.ones(n)
    rhs = np.zeros(n)
    rhs[n - 1] = 1.0
    try:
        d = spsolve(A.tocsr(), rhs)
        if not np.all(np.isfinite(d)):
            raise FloatingPointError("spsolve 返回非有限值")
        d = np.maximum(d, 0.0)
        d = d / d.sum()
    except Exception as e:                            # 奇异时退回均匀初值，靠迭代收敛
        log.warning("平稳分布直接解失败（%s），改用迭代", e)
        d = np.full(n, 1.0 / n)
    it, diff = 0, np.inf
    for it in range(1, maxit + 1):
        d_new = TT @ d
        diff = np.max(np.abs(d_new - d))
        d = d_new
        if diff < tol:
            break
    D = d.reshape(nz, na).T                           # D[i, j]：资产 a_i、状态 z_j
    return D, it, diff


# ---------------------------------------------------------------------
# 5. 给定 r 的家庭侧总量
# ---------------------------------------------------------------------
def household_side(r, p, z, P):
    Kd, w = prices(r, p)
    phi, nat = borrowing_limit(r, w, z.min(), p["b"])
    a = asset_grid(phi, p["a_max"], p["n_a"])
    c, a_pol, it_hh, d_hh = solve_household(r, w, a, z, P, p)
    D, it_d, d_d = stationary_distribution(a, a_pol, P)
    Ks = float((a[:, None] * D).sum())
    return dict(r=r, w=w, Kd=Kd, Ks=Ks, phi=phi, nat=nat, a=a, c=c, a_pol=a_pol, D=D,
                it_hh=it_hh, diff_hh=d_hh, it_dist=it_d, diff_dist=d_d)


def excess(r, p, z, P):
    s = household_side(r, p, z, P)
    return (s["Ks"] - s["Kd"]) / s["Kd"]


# ---------------------------------------------------------------------
# 6. 一般均衡与诊断
# ---------------------------------------------------------------------
def euler_errors(s, z, P, p):
    """非约束、且平稳分布质量 > 1e-12 的点上的 log10 Euler 误差（相对消费单位）。"""
    mu, beta, R = p["mu"], p["beta"], 1.0 + s["r"]
    a, c, a_pol = s["a"], s["c"], s["a_pol"]
    errs = []
    for j in range(z.size):
        c_next = np.column_stack([np.interp(a_pol[:, j], a, c[:, jp]) for jp in range(z.size)])
        rhs = beta * R * (c_next ** (-mu)) @ P[j]
        unc = (a_pol[:, j] > a[0] + 1e-8) & (s["D"][:, j] > 1e-12)
        e = np.abs(1.0 - rhs[unc] ** (-1.0 / mu) / c[unc, j])
        errs.append(e)
    e = np.concatenate(errs)
    e = e[e > 0]
    if not e.size:
        return None, None                            # 无可计算点（JSON 中写为 null）
    return float(np.log10(e.mean())), float(np.log10(e.max()))


def solve_ge(p, z, P, r_lo, r_hi, n_scan=30):
    scan_r = np.linspace(r_lo, r_hi, n_scan)
    scan_ex = np.array([excess(r, p, z, P) for r in scan_r])
    crossings = int(np.sum(np.diff(np.sign(scan_ex)) != 0))
    if np.sign(scan_ex[0]) == np.sign(scan_ex[-1]):
        raise ValueError(f"出清函数在 [{r_lo:.4f}, {r_hi:.4f}] 两端同号（{scan_ex[0]:.3e}, {scan_ex[-1]:.3e}），"
                         "无法求根；请检查参数或调整 r_lo_eps / r_hi_eps")
    r_star = brentq(excess, r_lo, r_hi, args=(p, z, P), xtol=1e-15, rtol=1e-15, maxiter=500)  # v0.3：接近 β(1+r)=1 时 K^s 极陡，需机器精度
    return r_star, scan_r, scan_ex, crossings


def gini(values, weights):
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w)
    cv = np.cumsum(v * w)
    total = cv[-1]
    if total <= 0:
        return float("nan")                          # 总财富非正时 Gini 无定义
    # Lorenz 面积（梯形）
    lorenz = np.concatenate([[0.0], cv / total])
    pop = np.concatenate([[0.0], cw])
    trap = getattr(np, "trapezoid", None) or np.trapz   # numpy ≥ 2.0 为 trapezoid
    area = trap(lorenz, pop)
    return float(1.0 - 2.0 * area)


def run(scenario: str, overrides: dict[str, float]) -> dict:
    p = load_params(CALIB, overrides)
    seed = int(SEED_FILE.read_text().strip()) if SEED_FILE.exists() else None
    z, P, pi, quality = income_process(p)
    log.info("参数：%s", {k: p[k] for k in sorted(p)})
    log.info("收入离散化：%s", quality)

    r_hi = 1.0 / p["beta"] - 1.0 - p.get("r_hi_eps", 1e-4)
    r_lo = -p["delta"] + p.get("r_lo_eps", 0.02)
    r_star, scan_r, scan_ex, crossings = solve_ge(p, z, P, r_lo, r_hi, int(p.get("n_scan", 30)))
    s = household_side(r_star, p, z, P)

    K = s["Kd"]
    Y = K ** p["alpha"]
    C = float((s["c"] * s["D"]).sum())
    D = s["D"]
    wealth = s["a"][:, None] * np.ones_like(D)
    res_market = abs(s["Ks"] - s["Kd"]) / s["Kd"]
    res_resource = abs(C + p["delta"] * K - Y) / Y
    mass_top = float(D[-1, :].sum())
    mass_constrained = float(D[s["a_pol"] <= s["a"][0] + 1e-10].sum())
    ee_mean, ee_max = euler_errors(s, z, P, p)

    out = {
        "model": MODEL_NAME,
        "scenario": scenario,
        "params": {k: p[k] for k in sorted(p)},
        "steady_state": {
            "r": s["r"], "w": s["w"], "K": K, "Y": Y, "C": C,
            "K_over_Y": K / Y, "saving_rate": p["delta"] * K / Y,
            "phi": s["phi"], "natural_limit": s["nat"], "b_over_w": p["b"] / s["w"],
            "share_constrained": mass_constrained,
            "wealth_gini": gini(wealth.ravel(), D.ravel()),
        },
        "residuals": {
            "capital_market_rel": res_market,
            "resource_constraint_rel": res_resource,
            "distribution_mass_minus_one": abs(float(D.sum()) - 1.0),
        },
        "diagnostics": {
            "egm_iterations": s["it_hh"], "egm_sup_diff": s["diff_hh"],
            "dist_iterations": s["it_dist"], "dist_sup_diff": s["diff_dist"],
            "mass_at_grid_top": mass_top,
            "euler_error_log10_mean": ee_mean, "euler_error_log10_max": ee_max,
            "uniqueness_scan_crossings": crossings,
            "uniqueness_scan": {"r": scan_r.tolist(), "excess_rel": scan_ex.tolist()},
            "income_discretisation": quality,
        },
        "seed": seed,
        "env": {"os": platform.platform(), "python": platform.python_version(),
                "numpy": np.__version__, "scipy": scipy.__version__},
        "git_sha": "n/a",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    tol_ss = p.get("tol_ss", 1e-6)
    dist_converged = s["diff_dist"] < 1e-12
    egm_converged = s["diff_hh"] < 1e-10
    disc_ok = quality["var_rel_error"] < 0.05 and quality["autocorr_abs_error"] < 0.01
    out["diagnostics"]["discretisation_ok"] = bool(disc_ok)
    out["diagnostics"]["dist_converged"] = bool(dist_converged)
    out["diagnostics"]["egm_converged"] = bool(egm_converged)
    out["validated"] = bool(res_market < tol_ss and res_resource < tol_ss
                            and mass_top < 1e-8 and crossings == 1
                            and dist_converged and egm_converged and disc_ok)
    if not dist_converged:
        log.error("平稳分布未收敛（diff=%.2e），结果不得对外报告", s["diff_dist"])

    CKPT.mkdir(parents=True, exist_ok=True)
    (CKPT / f"{MODEL_NAME}_{scenario}_ss.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    if scenario == "baseline":
        (CKPT / f"{MODEL_NAME}_ss.json").write_text(
            json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    np.savez(CKPT / f"{MODEL_NAME}_{scenario}_arrays.npz",
             a=s["a"], z=z, P=P, c=s["c"], a_pol=s["a_pol"], D=D)
    log.info("均衡：r=%.6f  K/Y=%.4f  s=%.4f  受约束比例=%.4f",
             s["r"], K / Y, p["delta"] * K / Y, mass_constrained)
    log.info("残差：%s", out["residuals"])
    log.info("诊断：EGM %d 次，分布 %d 次，上端质量 %.2e，Euler 误差 log10 均值 %s，唯一性扫描穿越 %d 次",
             s["it_hh"], s["it_dist"], mass_top, "n/a" if ee_mean is None else f"{ee_mean:.2f}", crossings)
    log.info("validated = %s", out["validated"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=f"{MODEL_NAME} 稳态求解（strucmod v0.3 HA 模板）")
    ap.add_argument("--scenario", default="baseline")
    ap.add_argument("--set", action="append", default=[], help="覆盖参数，如 --set b=2")
    args = ap.parse_args()
    bad = [x for x in args.set if "=" not in x]
    if bad:
        ap.error(f"--set 需要 key=value 形式：{bad}")
    overrides = {k: float(v) for k, v in (x.split("=", 1) for x in args.set)}

    LOGS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(LOGS / f"{MODEL_NAME}_solve_{args.scenario}_{ts}.log",
                                                      encoding="utf-8")])
    try:
        out = run(args.scenario, overrides)
    except Exception:
        log.exception("求解失败")
        return 3
    return 0 if out["validated"] else 2


if __name__ == "__main__":
    sys.exit(main())
