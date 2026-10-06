# =====================================================================
# model/03_solve/aiyagari_borrowing/tables_figures.py
# strucmod v0.3.0 工作流 build-tables：比较静态表与图
# 依赖：Python 3.10+，numpy 1.24+，matplotlib 3.7+；输入：output/checkpoints/*_ss.json 与 *_arrays.npz
# 输出：output/tables/、output/figures/
# =====================================================================
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CK, TB, FG = ROOT / "output" / "checkpoints", ROOT / "output" / "tables", ROOT / "output" / "figures"
M = "aiyagari_borrowing"
TB.mkdir(parents=True, exist_ok=True)
FG.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def load(s):
    return json.loads((CK / f"{M}_{s}_ss.json").read_text(encoding="utf-8"))


def main():
    scen = [("baseline", 0.0), ("b0.5", 0.5), ("b1", 1.0), ("b2", 2.0), ("b4", 4.0), ("b8", 8.0)]
    rows = []
    for name, b in scen:
        d = load(name)
        ss, dg = d["steady_state"], d["diagnostics"]
        assert d["validated"], f"{name} 未通过验证，不得进入结果表"
        rows.append({"scenario": name, "b": b, "b_over_w": ss["b_over_w"], "r_pct": 100 * ss["r"],
                     "K_over_Y": ss["K_over_Y"], "saving_rate_pct": 100 * ss["saving_rate"],
                     "share_constrained_pct": 100 * ss["share_constrained"], "wealth_gini": ss["wealth_gini"],
                     "natural_limit": ss["natural_limit"], "b_share_of_natural_limit_pct": 100 * b / ss["natural_limit"],
                     "euler_err_log10_mean": dg["euler_error_log10_mean"]})
    with open(TB / f"{M}_comparative_statics.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})

    # 稳健性与对照
    rob = []
    for name in ("rob_nz15_b0", "rob_nz15_b2", "rob_nz15_b8", "cmp_tauchen_b0", "cmp_tauchen_b8", "limit_sigma0"):
        d = load(name)
        ss = d["steady_state"]
        q = d["diagnostics"]["income_discretisation"]
        rob.append({"scenario": name, "method": q["method"], "n_z": d["params"]["n_z"], "b": d["params"]["b"],
                    "sigma": d["params"]["sigma"], "r_pct": 100 * ss["r"], "saving_rate_pct": 100 * ss["saving_rate"],
                    "var_rel_error": q["var_rel_error"], "validated": d["validated"]})
    with open(TB / f"{M}_robustness.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rob[0]))
        w.writeheader()
        for r in rob:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})

    # 图 1：资本供需（基准）
    d = load("baseline")
    sc = d["diagnostics"]["uniqueness_scan"]
    p = d["params"]
    r = np.array(sc["r"])
    Kd = (p["alpha"] / (r + p["delta"])) ** (1 / (1 - p["alpha"]))
    Ks = Kd * (1 + np.array(sc["excess_rel"]))
    fig, ax = plt.subplots(figsize=(5.5, 4))
    ax.plot(Ks, 100 * r, "o-", ms=3, label="家庭资产供给 $K^s(r)$")
    ax.plot(Kd, 100 * r, "-", label="企业资本需求 $K^d(r)$")
    ax.axhline(100 * (1 / p["beta"] - 1), ls="--", color="grey", lw=0.8, label="$1/\\beta-1$（完全市场）")
    ax.plot(d["steady_state"]["K"], 100 * d["steady_state"]["r"], "kD", label="均衡")
    ax.set_xlim(0, 3 * d["steady_state"]["K"])
    ax.set_xlabel("资本 / 资产")
    ax.set_ylabel("利率 r（%）")
    ax.set_title("资本市场出清（b = 0）", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FG / f"{M}_capital_market.png", dpi=200)
    fig.savefig(FG / f"{M}_capital_market.pdf")

    # 图 2：比较静态
    bs = [x["b"] for x in rows]
    fig, ax1 = plt.subplots(figsize=(5.5, 4))
    ax1.plot(bs, [x["r_pct"] for x in rows], "o-", label="均衡利率 r（%）")
    ax1.set_xlabel("借贷限额 b")
    ax1.set_ylabel("r（%）")
    ax2 = ax1.twinx()
    ax2.plot(bs, [x["saving_rate_pct"] for x in rows], "s--", color="tab:red", label="储蓄率 s（%）")
    ax2.set_ylabel("s（%）")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="center right", fontsize=8)
    ax1.set_title("放松借贷约束：利率上升、储蓄率下降", fontsize=10)
    fig.tight_layout()
    fig.savefig(FG / f"{M}_comparative_statics.png", dpi=200)
    fig.savefig(FG / f"{M}_comparative_statics.pdf")

    # 图 3：财富分布（b = 0 与 b = 8）
    fig, ax = plt.subplots(figsize=(5.5, 4))
    for name, lab in (("baseline", "b = 0"), ("b8", "b = 8")):
        z = np.load(CK / f"{M}_{name}_arrays.npz")
        a, D = z["a"], z["D"].sum(axis=1)
        cdf = np.cumsum(D)
        ax.plot(a, cdf, label=lab)
    ax.set_xlim(-9, 30)
    ax.set_xlabel("净资产 a")
    ax.set_ylabel("累积分布")
    ax.set_title("平稳财富分布", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FG / f"{M}_wealth_distribution.png", dpi=200)
    fig.savefig(FG / f"{M}_wealth_distribution.pdf")
    print("ok", len(rows), len(rob))


if __name__ == "__main__":
    main()
