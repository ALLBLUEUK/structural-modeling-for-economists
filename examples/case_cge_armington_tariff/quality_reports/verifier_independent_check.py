"""Independent spot-check (verifier, Gate 3). Written from spec.md sec.5 only; does NOT import solve.py.
Start: RAW data/calibration/armington_tariff/trade_flows.csv -> own deficit purge -> S1, S2 -> welfare, MAN imports.
Then compare with project outputs (read only, via plain csv/json parsing).
Run from the project root.
"""
import csv, json, sys
import numpy as np
from scipy.optimize import fsolve

sys.stdout.reconfigure(encoding="utf-8")
R = ["A", "B", "R"]
S = ["MAN", "OTH"]
EPS = np.array([4.0, 4.0])


def load(path):
    X = np.zeros((3, 3, 2))
    for r in csv.DictReader(open(path, encoding="utf-8")):
        X[R.index(r["exporter"]), R.index(r["importer"]), S.index(r["sector"])] = float(r["value"])
    return X


def params(X, t):
    Xt = X * (1 + t)                                  # tax-inclusive expenditure
    Ej = Xt.sum(axis=(0, 2))
    alpha = Xt.sum(axis=0) / Ej[:, None]              # [j,s]
    lam = Xt / Xt.sum(axis=0, keepdims=True)          # [i,j,s]
    Y = X.sum(axis=(1, 2))
    return Ej, alpha, lam, Y


def shares(lam, t, tp, w, eps):
    c = w[:, None, None] * (1 + tp) / (1 + t)
    num = lam * c ** (-eps[None, None, :])
    den = num.sum(axis=0, keepdims=True)
    return num / den, den[0] ** (-1.0 / eps[None, :])  # lam', Phat[j,s]


def solve_cf(X, t, tp, eps, D=None):
    """Exact hat algebra (spec sec.5 eq 1-6) with D'=0 (or given)."""
    E0, alpha, lam, Y = params(X, t)
    Dp = np.zeros(3) if D is None else D

    def agg(w):
        lp, P = shares(lam, t, tp, w, eps)
        rho = (alpha * (tp / (1 + tp) * lp).sum(axis=0)).sum(axis=1)
        Ep = (w * Y + Dp) / (1 - rho)
        return lp, P, rho, Ep

    def F(x):
        w = np.exp(x)
        lp, P, rho, Ep = agg(w)
        sales = (lp * alpha[None, :, :] * Ep[None, :, None] / (1 + tp)).sum(axis=(1, 2))
        r = w * Y - sales
        return [r[0] / Y.sum(), r[1] / Y.sum(), (w * Y).sum() / Y.sum() - 1.0]

    x, info, ier, msg = fsolve(F, np.zeros(3), xtol=1e-14, full_output=True)
    assert ier == 1 or np.abs(F(x)).max() < 1e-13, msg   # ier!=1 can occur when start point is already exact (tariff 0)
    w = np.exp(x)
    lp, P, rho, Ep = agg(w)
    sales = (lp * alpha[None, :, :] * Ep[None, :, None] / (1 + tp)).sum(axis=(1, 2))
    clear = w * Y - sales                              # all 3 clearing eqs (incl. dropped one)
    What = (Ep / E0) / np.prod(P ** alpha, axis=1)
    Xp = lp * alpha[None, :, :] * Ep[None, :, None] / (1 + tp)
    return dict(w=w, What=What, Xp=Xp, Ep=Ep, clear=clear, lam=lp, E0=E0, Y=Y, rho=rho)


raw = load("data/calibration/armington_tariff/trade_flows.csv")
t0 = np.zeros_like(raw)
E_raw, _, _, Y_raw = params(raw, t0)
print("raw deficits D_j = E_j - Y_j:", E_raw - Y_raw)
pg = solve_cf(raw, t0, t0, EPS)                       # own purge
Xpur = pg["Xp"]
Ep_, _, _, Ypur = params(Xpur, t0)
print("purged baseline max|E-Y|/sumY:", np.abs(Ep_ - Ypur).max() / Ypur.sum())
ref = load("data/calibration/armington_tariff/trade_flows_purged.csv")
print("purge vs project trade_flows_purged.csv: max abs diff =", np.abs(Xpur - ref).max(),
      " max rel diff =", (np.abs(Xpur - ref) / ref).max())


def scen(lst, X=Xpur, eps=EPS):
    tp = np.zeros_like(X)
    for ex, im, sec, tau in lst:
        tp[R.index(ex), R.index(im), S.index(sec)] = tau
    return solve_cf(X, np.zeros_like(X), tp, eps)


s1 = scen([("B", "A", "MAN", 0.10)])
s2 = scen([("B", "A", "MAN", 0.10), ("A", "B", "MAN", 0.10)])


def imp_chg(res, ex, im, sec):
    i, j, s = R.index(ex), R.index(im), S.index(sec)
    return (res["Xp"][i, j, s] / Xpur[i, j, s] - 1) * 100


out = {"S1": s1, "S2": s2}
for nm, r in out.items():
    print(f"\n{nm}: w_hat = {r['w']}")
    print(f"{nm}: What = {r['What']}  welfare_pct = {(r['What'] - 1) * 100}")
    print(f"{nm}: max|clearing resid|/sumY (all 3 eqs) = {np.abs(r['clear']).max() / r['Y'].sum():.3e}")
    print(f"{nm}: A MAN imports from B, value change % = {imp_chg(r, 'B', 'A', 'MAN')}")


def u8(p):
    return json.load(open(p, encoding="utf-8"))


tab = list(csv.DictReader(open("output/tables/armington_tariff_cf_summary.csv", encoding="utf-8")))
cf = u8("output/checkpoints/armington_tariff_cf_summary.json")
print("\n=== Comparison with project outputs ===")
mx = 0.0
for nm in ("S1", "S2"):
    ck = u8(f"output/checkpoints/armington_tariff_{nm}.json")["results"]
    for k, reg in enumerate(R):
        d_w = abs(out[nm]["What"][k] - ck["welfare_change"][reg])
        d_wage = abs(out[nm]["w"][k] - ck["wage_change"][reg])
        mx = max(mx, d_w, d_wage)
        if reg in ("A", "B"):
            row = [r for r in tab if r["scenario"] == nm and r["region"] == reg][0]
            d_csv = abs((out[nm]["What"][k] - 1) * 100 - float(row["welfare_pct"]))
            print(f"{nm} {reg}: welfare_pct mine={(out[nm]['What'][k] - 1) * 100:.10f} "
                  f"ckpt={(ck['welfare_change'][reg] - 1) * 100:.10f} |dWhat|={d_w:.2e} |dwage|={d_wage:.2e} (csv 6dp diff {d_csv:.1e})")
P = cf["propositions"]
mine_imp = imp_chg(s1, "B", "A", "MAN")
d_imp = abs(mine_imp - P["P1_A_imports_MAN_from_B_value_change_pct"])
d_r = abs(imp_chg(s1, "R", "A", "MAN") - P["P1_A_imports_MAN_from_R_value_change_pct"])
d_own = abs(imp_chg(s1, "A", "A", "MAN") - P["P1_A_own_MAN_value_change_pct"])
rel = s1["w"][1] / s1["w"][0]
d_rel = abs(rel - P["P2_relative_wage_B_over_A"])
print(f"A MAN imports from B: mine={mine_imp:.10f} proj={P['P1_A_imports_MAN_from_B_value_change_pct']:.10f} diff(pct pts)={d_imp:.2e}")
print(f"A MAN imports from R: diff={d_r:.2e}; A own MAN sales: diff={d_own:.2e}")
print(f"relative wage B/A: mine={rel:.12f} diff={d_rel:.2e} -> decline {100 * (1 - rel):.4f}%")
P3A = (s2["What"][0] - s1["What"][0]) * 100
P3B = (s2["What"][1] - s1["What"][1]) * 100
print(f"P3 A S2-S1 pp: {P3A:.6f} (diff {abs(P3A - P['P3_A_welfare_S2_minus_S1_pp']):.2e}); "
      f"B: {P3B:.6f} (diff {abs(P3B - P['P3_B_welfare_S2_minus_S1_pp']):.2e})")
d_all = max(mx, d_imp / 100, d_r / 100, d_own / 100, d_rel)
print(f"MAX |diff| (What, w_hat, flow-change ratios, relative wage): {d_all:.3e}  (threshold 1e-8)")

print("\n=== Report-derived numbers ===")
lnw = np.log(s1["w"][0])
rho = s1["rho"][0]
lnrev = np.log(1 + rho / (1 - rho))                   # R'/(w Y) = rho E'/(w Y)
lnW = np.log(s1["What"][0])
lnP = lnW - lnw - lnrev
print(f"S1 A ln decomposition (%): wage={lnw * 100:.4f}  tariff rev={lnrev * 100:.4f}  price index(residual)={lnP * 100:.4f}  sum={lnW * 100:.4f}")
grid = np.round(np.arange(0, 0.601, 0.01), 2)
wl = [(scen([("B", "A", "MAN", tau)])["What"][0] - 1) * 100 for tau in grid]
k = int(np.argmax(wl))
print(f"Optimal tariff grid argmax = {grid[k]:.2f}, A welfare = {wl[k]:.6f}%; at 10%: {wl[10]:.6f}%")


def run_eps(e):
    ep = np.array([e, 4.0])
    Xp_ = solve_cf(raw, t0, t0, ep)["Xp"]             # re-purge from raw for each eps
    tp1 = np.zeros_like(Xp_)
    tp1[1, 0, 0] = .10
    r1 = solve_cf(Xp_, np.zeros_like(Xp_), tp1, ep)
    tp2 = tp1.copy()
    tp2[0, 1, 0] = .10
    r2 = solve_cf(Xp_, np.zeros_like(Xp_), tp2, ep)
    return [(r1["What"][0] - 1) * 100, (r1["What"][1] - 1) * 100, (r2["What"][0] - 1) * 100, (r2["What"][1] - 1) * 100]


print("eps_MAN sweep (S1A,S1B,S2A,S2B %), re-purged from raw:")
ref_rob = list(csv.DictReader(open("output/tables/armington_tariff_robustness_eps.csv", encoding="utf-8")))
mr = 0
for row in ref_rob:
    v = run_eps(float(row["eps_MAN"]))
    pr = [float(row[c]) for c in ("S1_A_welfare_pct", "S1_B_welfare_pct", "S2_A_welfare_pct", "S2_B_welfare_pct")]
    mr = max(mr, max(abs(a - b) for a, b in zip(v, pr)))
    print(f"  eps={row['eps_MAN']}: " + ", ".join(f"{x:.6f}" for x in v))
print(f"  max |diff| vs project 6dp table: {mr:.2e}")
es = np.round(np.arange(2.0, 12.01, 0.25), 2)
sv = np.array([run_eps(e) for e in es])
print(f"fine sweep eps 2..12 step .25 ({len(es)} pts): S1 A welfare min={sv[:, 0].min():.6f} max={sv[:, 0].max():.6f}, any<=0: {bool((sv[:, 0] <= 0).any())}; "
      f"S2 A welfare max={sv[:, 2].max():.6f}, any>=0: {bool((sv[:, 2] >= 0).any())}")
print(f"S1 A at eps=12: {sv[-1, 0]:.6f}%")
print("\nRESULT:", "PASS" if d_all < 1e-8 else "FAIL")
