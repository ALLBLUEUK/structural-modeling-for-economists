# =====================================================================
# model/03_solve/armington_tariff/counterfactuals.py
# strucmod v0.3.0 工作流 counterfactual-run：情形汇总、贸易弹性稳健性、数值最优关税
# 依赖：Python 3.10+，numpy 1.24+，scipy 1.10+，matplotlib 3.7+；求解器：同目录 solve.py
# 输出：output/tables/、output/figures/、output/checkpoints/armington_tariff_cf_summary.json
# spec：model/01_setup/armington_tariff/spec.md（§1 命题、§8 稳健性与最优关税）
# 示意数据，结论仅为机制示范
# =====================================================================
from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
spec_ = importlib.util.spec_from_file_location("solve", HERE / "solve.py")
S = importlib.util.module_from_spec(spec_)
sys.modules["solve"] = S                     # dataclass 需要模块已注册
spec_.loader.exec_module(S)

TABLES, FIGS, CKPT = S.TABLES, S.ROOT / "output" / "figures", S.CKPT
TABLES.mkdir(parents=True, exist_ok=True)
CKPT.mkdir(parents=True, exist_ok=True)
FIGS.mkdir(parents=True, exist_ok=True)
NOTE = "示意数据，结论仅为机制示范"
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def base_with_eps(eps_man: float) -> "S.Base":
    raw = S.load_base(flows_file="trade_flows.csv")
    raw.eps = np.array([eps_man if s == "MAN" else e for s, e in zip(raw.sectors, raw.eps)])
    return S.purge_deficits(raw)


def scenario_outcome(base, name):
    tp = S.load_scenario(base, name)
    ones = np.ones_like(base.X)
    w, _ = S.solve_hybr(base, tp, ones, np.zeros(len(base.regions)))
    return S.outcomes(base, w, tp, ones, np.zeros(len(base.regions)))


def main():
    base = S.load_base()                                  # 剔除赤字后的基期（ε = 4）
    R, SEC = base.regions, base.sectors
    iA, iB, iR, kM = R.index("A"), R.index("B"), R.index("R"), SEC.index("MAN")

    # ---- 1. 情形汇总 ----
    rows = []
    res = {}
    for name in ("S1", "S2"):
        o = scenario_outcome(base, name)
        res[name] = o
        for j, r in enumerate(R):
            rows.append({
                "scenario": name, "region": r,
                "welfare_pct": 100 * (o["What"][j] - 1),
                "wage_pct": 100 * (o["what"][j] - 1),
                "decomp_wage_pct": 100 * o["decomp"]["ln_wage"][j],
                "decomp_tariff_revenue_pct": 100 * o["decomp"]["ln_tariff_revenue"][j],
                "decomp_price_index_pct": 100 * o["decomp"]["ln_price_index"][j],
                "MAN_employment_pct": 100 * (o["Lhat"][j, kM] - 1),
                "OTH_employment_pct": 100 * (o["Lhat"][j, 1 - kM] - 1),
            })
    with open(TABLES / "armington_tariff_cf_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})

    # 双边流（MAN，出厂价值变化）
    flows = []
    for name in ("S1", "S2"):
        o = res[name]
        for i, ri in enumerate(R):
            for j, rj in enumerate(R):
                flows.append({"scenario": name, "exporter": ri, "importer": rj,
                              "MAN_value_change_pct": 100 * (o["Xp"][i, j, kM] / base.X[i, j, kM] - 1)})
    with open(TABLES / "armington_tariff_cf_flows_MAN.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(flows[0]))
        w.writeheader()
        for r in flows:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})

    # 命题检验
    o1 = res["S1"]
    props = {
        "P1_A_imports_MAN_from_B_value_change_pct": 100 * (o1["Xp"][iB, iA, kM] / base.X[iB, iA, kM] - 1),
        "P1_A_imports_MAN_from_R_value_change_pct": 100 * (o1["Xp"][iR, iA, kM] / base.X[iR, iA, kM] - 1),
        "P1_A_own_MAN_value_change_pct": 100 * (o1["Xp"][iA, iA, kM] / base.X[iA, iA, kM] - 1),
        "P2_relative_wage_B_over_A": float(o1["what"][iB] / o1["what"][iA]),
        "P3_A_welfare_S2_minus_S1_pp": 100 * (res["S2"]["What"][iA] - o1["What"][iA]),
        "P3_B_welfare_S2_minus_S1_pp": 100 * (res["S2"]["What"][iB] - o1["What"][iB]),
    }
    props["P1_pass"] = bool(props["P1_A_imports_MAN_from_B_value_change_pct"] < 0 and props["P1_A_imports_MAN_from_R_value_change_pct"] > 0)
    props["P2_pass"] = bool(props["P2_relative_wage_B_over_A"] < 1)

    # ---- 2. 稳健性：ε_MAN 扫描（每个 ε 重新剔除赤字）----
    rob = []
    for e in (2, 3, 4, 6, 8):
        b = base_with_eps(e)
        oS1, oS2 = scenario_outcome(b, "S1"), scenario_outcome(b, "S2")
        rob.append({"eps_MAN": e,
                    "S1_A_welfare_pct": 100 * (oS1["What"][iA] - 1), "S1_B_welfare_pct": 100 * (oS1["What"][iB] - 1),
                    "S2_A_welfare_pct": 100 * (oS2["What"][iA] - 1), "S2_B_welfare_pct": 100 * (oS2["What"][iB] - 1)})
    # 符号翻转临界值：在 ε ∈ [1.5, 12] 上细扫 S1 中 A 的福利
    grid_e = np.round(np.arange(2.0, 12.01, 0.25), 2)                # 与校准下界 2 一致
    a_wel = np.array([scenario_outcome(base_with_eps(e), "S1")["What"][iA] - 1 for e in grid_e])
    flips = [float(grid_e[k + 1]) for k in range(len(grid_e) - 1) if np.sign(a_wel[k]) != np.sign(a_wel[k + 1])]
    with open(TABLES / "armington_tariff_robustness_eps.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rob[0]))
        w.writeheader()
        for r in rob:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})

    # ---- 3. 数值最优关税：A 对 B 的 MAN 关税 ----
    tgrid = np.round(np.arange(0.0, 0.601, 0.01), 2)
    welA = []
    ones = np.ones_like(base.X)
    for t in tgrid:
        tp = base.t.copy()
        tp[iB, iA, kM] = t
        wv, _ = S.solve_hybr(base, tp, ones, np.zeros(len(R)))
        welA.append(S.outcomes(base, wv, tp, ones, np.zeros(len(R)))["What"][iA] - 1)
    welA = np.array(welA)
    t_opt = float(tgrid[int(np.argmax(welA))])
    with open(TABLES / "armington_tariff_optimal_tariff_grid.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tariff_A_on_B_MAN", "A_welfare_pct"])
        for t, v in zip(tgrid, welA):
            w.writerow([f"{t:.2f}", f"{100 * v:.6f}"])

    summary = {"model": S.MODEL_NAME, "disclaimer": NOTE, "propositions": props,
               "robustness_eps_MAN": rob, "S1_A_welfare_sign_flip_eps": flips,
               "numerical_optimal_tariff_A_on_B_MAN": t_opt,
               "A_welfare_at_optimal_pct": float(100 * welA.max())}
    (CKPT / "armington_tariff_cf_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                                                         encoding="utf-8")

    # ---- 4. 图 ----
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    comp = [("decomp_wage_pct", "工资（要素收入）"), ("decomp_tariff_revenue_pct", "关税收入"),
            ("decomp_price_index_pct", "价格指数")]
    allv = []
    for ax, name in zip(axes, ("S1", "S2")):
        sub = [r for r in rows if r["scenario"] == name]
        x = np.arange(len(sub))
        width = 0.2
        for k, (key, lab) in enumerate(comp):
            v = [r[key] for r in sub]
            allv += v
            ax.bar(x + (k - 1) * width, v, width=width, label=lab)
        wv = [r["welfare_pct"] for r in sub]
        ax.plot(x + 1.75 * width, wv, "kD", label="福利合计（右侧菱形）")
        ax.axhline(0, color="grey", lw=0.8)
        ax.set_xticks(x, [r["region"] for r in sub])
        ax.set_title({"S1": "S1：A 对 B 制造业加征 10%", "S2": "S2：B 对等报复"}[name], fontsize=10)
    lim = 1.15 * max(abs(v) for v in allv)
    axes[0].set_ylim(-lim, lim)
    axes[0].set_ylabel("相对基期变化（%，对数近似）")
    axes[1].legend(fontsize=8, loc="lower right")
    fig.suptitle(f"福利变化及其分解（{NOTE}）", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGS / "armington_tariff_welfare_decomposition.png", dpi=200)
    fig.savefig(FIGS / "armington_tariff_welfare_decomposition.pdf")

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(100 * tgrid, 100 * welA, lw=2)
    ax.axvline(100 * t_opt, ls="--", color="grey")
    ax.axvline(10, ls=":", color="tab:red")
    ax.set_xlabel("A 对 B 制造业关税（%）")
    ax.set_ylabel("A 的福利变化（%）")
    ax.set_title(f"A 的福利随关税变化（B 不报复；{NOTE}）", fontsize=9)
    ax.annotate(f"网格最优 ≈ {100 * t_opt:.0f}%（步长 1%）", (100 * t_opt, 100 * welA.max()), textcoords="offset points",
                xytext=(8, -14), fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "armington_tariff_optimal_tariff.png", dpi=200)
    fig.savefig(FIGS / "armington_tariff_optimal_tariff.pdf")

    print(json.dumps(summary, indent=1, ensure_ascii=False))
    (S.LOGS / "armington_tariff_counterfactuals.log").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
