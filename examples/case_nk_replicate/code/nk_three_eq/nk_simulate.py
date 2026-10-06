#!/usr/bin/env python3
"""
nk_simulate.py — IRF simulation for 3-equation NK to a 25 bp monetary shock.
"""
from __future__ import annotations
import csv, json, logging, shutil, sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman"],
    "text.latex.preamble": r"\usepackage{lmodern}\usepackage{amsmath}\usepackage{amssymb}",
    "axes.titlesize":  10,
    "axes.labelsize":  9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.titlesize": 11,
})

ROOT = Path(__file__).resolve().parents[2]
CKPT = ROOT / "results" / "checkpoints"
TBL  = ROOT / "results" / "tables"
FIG  = ROOT / "results" / "figures"
PAP  = ROOT / "paper" / "figures"
LOGD = ROOT / "logs"
for d in (TBL, FIG, PAP, LOGD):
    d.mkdir(parents=True, exist_ok=True)


def setup_logger() -> logging.Logger:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = LOGD / f"nk_simulate_{ts}.log"
    logger = logging.getLogger("nk.simulate")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.info("log file: %s", log_path)
    return logger


def main() -> int:
    log = setup_logger()
    log.info("============ 3-eq NK simulate monetary IRF ============")
    pol = json.loads((CKPT / "nk_policy.json").read_text(encoding="utf-8"))
    if not pol.get("bk_pass") or not pol.get("validated"):
        log.error("policy not validated; refusing to simulate.")
        return 2

    P = np.array(pol["P_state_transition"])           # (3, 3)
    F = np.array(pol["F_policy"])                     # (2, 3)
    state_names  = pol["state_names"]                 # eps_a, eps_b, eps_m
    jumper_names = pol["jumper_names"]                # y, pi
    p = pol["params"]
    phi_pi = p["phi_pi"]; phi_y = p["phi_y"]

    # 25 bp = 0.0025 (quarterly nominal rate deviation)
    shock_size = 0.0025
    shock_idx = state_names.index("eps_m")

    horizon = 20
    n_states  = P.shape[0]
    n_jumpers = F.shape[0]
    X = np.zeros((horizon + 1, n_states))   # states (eps_a, eps_b, eps_m)
    Y = np.zeros((horizon + 1, n_jumpers))  # jumpers (y, pi)
    R = np.zeros(horizon + 1)               # nominal rate (derived)

    X[0, shock_idx] = shock_size
    Y[0] = F @ X[0]
    R[0] = phi_pi * Y[0, 1] + phi_y * Y[0, 0] + X[0, shock_idx]

    for t in range(horizon):
        X[t + 1] = P @ X[t]
        Y[t + 1] = F @ X[t + 1]
        R[t + 1] = phi_pi * Y[t + 1, 1] + phi_y * Y[t + 1, 0] + X[t + 1, shock_idx]

    series = {
        "y":  Y[:, 0],
        "pi": Y[:, 1],
        "r":  R,
        "eps_m": X[:, shock_idx],
    }
    # real rate ex-post
    series["real_rate"] = series["r"] - np.concatenate([series["pi"][1:], [series["pi"][-1]]])
    # pct (multiply by 100 to get percentage points, then annualise rates by *4)
    pct = {k: 100.0 * v for k, v in series.items()}
    pct["r_annualised"] = 4.0 * pct["r"]
    pct["pi_annualised"] = 4.0 * pct["pi"]
    pct["real_rate_annualised"] = 4.0 * pct["real_rate"]

    # save CSV
    csv_path = TBL / "nk_irf_eps_m.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["period", "y_pct", "pi_pct", "r_pct", "real_rate_pct",
                    "pi_annualised_pp", "r_annualised_pp", "real_rate_annualised_pp",
                    "eps_m"])
        for t in range(horizon + 1):
            w.writerow([t,
                        f"{pct['y'][t]:.4f}",
                        f"{pct['pi'][t]:.4f}",
                        f"{pct['r'][t]:.4f}",
                        f"{pct['real_rate'][t]:.4f}",
                        f"{pct['pi_annualised'][t]:.4f}",
                        f"{pct['r_annualised'][t]:.4f}",
                        f"{pct['real_rate_annualised'][t]:.4f}",
                        f"{pct['eps_m'][t]:.4f}"])
    log.info("wrote %s", csv_path)

    # save JSON
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (CKPT / "nk_irf_eps_m.json").write_text(json.dumps({
        "model": "nk_three_eq",
        "shock": "eps_m",
        "shock_size": shock_size,
        "horizon": horizon,
        "data_pct": {k: pct[k].tolist() for k in ("y", "pi", "r", "real_rate")},
        "data_annualised_pp": {
            "pi": pct["pi_annualised"].tolist(),
            "r":  pct["r_annualised"].tolist(),
            "real_rate": pct["real_rate_annualised"].tolist(),
        },
        "diagnostics": {
            "y_falls_on_impact":          bool(pct["y"][0] < 0),
            "inflation_falls_on_impact":  bool(pct["pi"][0] < 0),
            "real_rate_rises_on_impact":  bool(pct["real_rate"][0] > 0),
            "nominal_rate_rises_on_impact": bool(pct["r"][0] > 0),
            "y_peak_quarter":             int(np.argmin(pct["y"])),
            "y_peak_pct":                 float(np.min(pct["y"])),
            "pi_peak_quarter":            int(np.argmin(pct["pi"])),
            "pi_peak_pct":                float(np.min(pct["pi"])),
            "all_decay_by_horizon":       bool(
                abs(pct["y"][-1]) < 0.1 * abs(np.min(pct["y"])) and
                abs(pct["pi"][-1]) < 0.1 * abs(np.min(pct["pi"]))
            ),
        },
        "timestamp": ts,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("wrote nk_irf_eps_m.json")

    # 3-panel figure
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))
    t_axis = np.arange(horizon + 1)

    ax = axes[0]
    ax.plot(t_axis, pct["y"], color="tab:blue", lw=2)
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.set_title(r"Output ($\hat{y}_{t}$)")
    ax.set_xlabel(r"Quarters"); ax.set_ylabel(r"\%-point deviation")
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.plot(t_axis, pct["pi_annualised"], color="tab:red", lw=2, label=r"Annualised")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.set_title(r"Inflation ($\hat{\pi}_{t}$, annualised)")
    ax.set_xlabel(r"Quarters"); ax.set_ylabel(r"Percentage points")
    ax.grid(alpha=0.3)

    ax = axes[2]
    ax.plot(t_axis, pct["r_annualised"], color="tab:purple", lw=2, label=r"Nominal $r$")
    ax.plot(t_axis, pct["real_rate_annualised"], color="tab:green", lw=2, ls="--",
            label=r"Real rate $r - \mathbb{E}\pi_{t+1}$")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.set_title(r"Interest rates (annualised)")
    ax.set_xlabel(r"Quarters"); ax.set_ylabel(r"Percentage points")
    ax.grid(alpha=0.3); ax.legend(loc="upper right")

    fig.suptitle(
        rf"Impulse responses to a 25-bp contractionary monetary policy shock "
        rf"($\varepsilon^{{m}}_{{t}}=0.0025$, AR(1) with $\rho_{{m}}={p['rho_m']}$)",
        fontsize=11)
    fig.tight_layout()
    fig.savefig(FIG / "nk_irf_eps_m.pdf", dpi=300)
    fig.savefig(FIG / "nk_irf_eps_m.png", dpi=120)
    plt.close(fig)
    shutil.copy(FIG / "nk_irf_eps_m.pdf", PAP / "nk_irf_eps_m.pdf")

    log.info("============ done ============")
    log.info("on impact:  y = %.3f%%  pi (annualised) = %.3f pp  r (annualised) = %.3f pp",
             pct["y"][0], pct["pi_annualised"][0], pct["r_annualised"][0])
    log.info("peak y     = %.3f%%  at quarter %d",
             np.min(pct["y"]), int(np.argmin(pct["y"])))
    log.info("peak pi    = %.3f pp at quarter %d",
             np.min(pct["pi_annualised"]), int(np.argmin(pct["pi_annualised"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
