#!/usr/bin/env python3
"""
nk_solve.py — Canonical 3-equation New Keynesian model solver.

Reads:   calibration.csv
Writes:  results/checkpoints/nk_ss.json
         results/checkpoints/nk_policy.json
         logs/nk_solve_<ts>.log

Method: After substituting the Taylor rule into the IS curve, the system has
two forward-looking jumpers (y, pi) and three exogenous AR(1) states
(eps_a, eps_b, eps_m). Solve with Klein (2000) generalised Schur via
scipy.linalg.ordqz.
"""
from __future__ import annotations
import csv, json, logging, sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.linalg import ordqz

ROOT  = Path(__file__).resolve().parents[2]
CALIB = ROOT / "code" / "nk_three_eq" / "calibration.csv"
CKPT  = ROOT / "results" / "checkpoints"
LOGS  = ROOT / "logs"
CKPT.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)


def setup_logger() -> logging.Logger:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = LOGS / f"nk_solve_{ts}.log"
    logger = logging.getLogger("nk.solve")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.info("log file: %s", log_path)
    return logger


def load_calibration() -> dict[str, float]:
    p: dict[str, float] = {}
    with CALIB.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if not (row.get("source") or "").strip():
                raise ValueError(f"Parameter {row['parameter']} has no source.")
            p[row["parameter"]] = float(row["value"])
    return p


def composite_coeffs(p: dict[str, float]) -> dict[str, float]:
    """NKPC slope kappa = (1 - theta)(1 - beta*theta)/theta * (sigma + varphi)."""
    beta   = p["beta"]
    theta  = p["theta"]
    sigma  = p["sigma"]
    varphi = p["varphi"]
    kappa = ((1.0 - theta) * (1.0 - beta * theta) / theta) * (sigma + varphi)
    return {"kappa": float(kappa)}


# =====================================================================
# System construction.
#
# Variable order (5 total):
#   states (3):   eps_a, eps_b, eps_m
#   jumpers (2):  y, pi
#
# After substituting r_t = phi_pi*pi_t + phi_y*y_t + eps_m_t into the IS:
#   y_t = E_t y_{t+1} - (1/sigma) * (phi_pi*pi_t + phi_y*y_t + eps_m_t - E_t pi_{t+1})
#         + eps_b_t
#   <=> (1 + phi_y/sigma) * y_t + (phi_pi/sigma) * pi_t
#       = E_t y_{t+1} + (1/sigma) * E_t pi_{t+1} - (1/sigma)*eps_m_t + eps_b_t
#
# NKPC:
#   pi_t = beta * E_t pi_{t+1} + kappa * y_t - eps_a_t
#
# State transitions (AR(1)):
#   eps_x_{t+1} = rho_x * eps_x_t   (innovations enter via impact later)
#
# Write A * E_t[y'] = B * y_t  (5x5 system).
# =====================================================================

VAR_NAMES = ["eps_a", "eps_b", "eps_m", "y", "pi"]
N_STATES  = 3
N_JUMPERS = 2
N = N_STATES + N_JUMPERS

IDX = {v: i for i, v in enumerate(VAR_NAMES)}


def build_system(p: dict[str, float], cc: dict[str, float]):
    A = np.zeros((N, N))
    B = np.zeros((N, N))

    rho_a = p["rho_a"]; rho_b = p["rho_b"]; rho_m = p["rho_m"]
    sigma = p["sigma"]; beta = p["beta"]
    phi_pi = p["phi_pi"]; phi_y = p["phi_y"]
    kappa = cc["kappa"]

    # ----- State transitions -----
    # eps_a: E[eps_a'] = rho_a * eps_a_t
    A[0, IDX["eps_a"]] = 1.0;  B[0, IDX["eps_a"]] = rho_a
    A[1, IDX["eps_b"]] = 1.0;  B[1, IDX["eps_b"]] = rho_b
    A[2, IDX["eps_m"]] = 1.0;  B[2, IDX["eps_m"]] = rho_m

    # ----- IS curve (after substituting Taylor rule) -----
    # E_t y_{t+1} + (1/sigma)*E_t pi_{t+1}
    #   = (1 + phi_y/sigma) * y_t + (phi_pi/sigma) * pi_t
    #     + (1/sigma)*eps_m_t - eps_b_t
    A[3, IDX["y"]]  = 1.0
    A[3, IDX["pi"]] = 1.0 / sigma
    B[3, IDX["y"]]  = 1.0 + phi_y / sigma
    B[3, IDX["pi"]] = phi_pi / sigma
    B[3, IDX["eps_m"]] = 1.0 / sigma
    B[3, IDX["eps_b"]] = -1.0

    # ----- NKPC -----
    # beta * E_t pi_{t+1} = pi_t - kappa * y_t + eps_a_t
    A[4, IDX["pi"]] = beta
    B[4, IDX["pi"]] = 1.0
    B[4, IDX["y"]]  = -kappa
    B[4, IDX["eps_a"]] = 1.0

    return A, B


# ---------------------------------------------------------------------
# Klein 2000 solver
# ---------------------------------------------------------------------
def klein_solve(A, B, n_states, log):
    """
    Klein (2000) solver.  A E[y_{t+1}] = B y_t.

    Generalised eigenvalue convention: for (A, B), det(A - lambda*B) = 0
    gives lambda = A_ii/B_ii on the diagonal.  But the actual dynamics
    matrix is B^{-1}*A * y_t = E[y_{t+1}]  (No wait that's wrong; it's
    E[y_{t+1}] = A^{-1}*B*y_t, so dynamics matrix is A^{-1}B with eigenvalues
    1/lambda_gen).

    Therefore: stable dynamics |mu_dyn| < 1  <=>  |lambda_gen| > 1.
    Sort so that |alpha| > |beta| (= "stable dynamics") comes first.
    """
    def sort_stable(alpha, beta):
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.abs(alpha) > np.abs(beta)   # |lambda_gen| > 1 = stable dynamics

    AA, BB, alpha, beta, Q, Z = ordqz(A, B, sort=sort_stable, output="complex")
    lambda_gen = alpha / beta
    # Dynamics eigenvalues mu = 1/lambda_gen
    with np.errstate(divide="ignore", invalid="ignore"):
        mu = 1.0 / lambda_gen
    n_stable = int(np.sum(np.abs(mu) < 1.0 - 1e-9))   # stable dynamics: |mu|<1
    n_jumpers = A.shape[0] - n_states
    n_unstable = A.shape[0] - n_stable

    log.info("dynamics eigenvalues mu (= 1/lambda_gen, sorted stable-first):")
    for i, (lg, m) in enumerate(zip(lambda_gen, mu)):
        marker = "S" if np.abs(m) < 1.0 - 1e-9 else "U"
        log.info("  mu[%d] = %.4f%+.4fj  (%s, |mu|=%.4f, lambda_gen=%.4f%+.4fj)",
                 i, np.real(m), np.imag(m), marker, np.abs(m),
                 np.real(lg), np.imag(lg))
    log.info("n_states=%d, n_jumpers=%d, n_stable=%d, n_unstable=%d",
             n_states, n_jumpers, n_stable, n_unstable)

    bk = (n_stable == n_states)   # equivalently n_unstable == n_jumpers
    log.info("Blanchard-Kahn: %s (need n_stable == n_states == %d)",
             "PASS" if bk else "FAIL", n_states)
    if not bk:
        return None, None, False, mu.tolist()
    eigvals = mu

    Z11 = Z[:n_states, :n_states]
    Z21 = Z[n_states:, :n_states]
    S11 = AA[:n_states, :n_states]
    T11 = BB[:n_states, :n_states]

    log.info("cond(Z11) = %.3e, cond(S11) = %.3e",
             np.linalg.cond(Z11), np.linalg.cond(S11))

    Z11inv = np.linalg.inv(Z11)
    S11inv = np.linalg.inv(S11)
    F = (Z21 @ Z11inv).real         # jumpers = F @ states
    P = (Z11 @ S11inv @ T11 @ Z11inv).real  # state transition

    return P, F, True, eigvals.tolist()


def main() -> int:
    log = setup_logger()
    log.info("============ 3-equation NK model solver ============")

    p = load_calibration()
    cc = composite_coeffs(p)
    log.info("parameters: %s", p)
    log.info("NKPC slope kappa = %.6f", cc["kappa"])

    A, B = build_system(p, cc)
    log.info("system built: %dx%d", *A.shape)

    P, F, bk_pass, eigvals = klein_solve(A, B, N_STATES, log)
    if not bk_pass:
        log.error("Blanchard-Kahn failed.")
        return 2

    log.info("solution: P %s (state transition), F %s (policy)", P.shape, F.shape)
    log.info("P =\n%s", P)
    log.info("F =\n%s", F)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ss_ckpt = {
        "model": "nk_three_eq",
        "steady_state": {"y": 0.0, "pi": 0.0, "r": 0.0},
        "params": p,
        "validated": True,
        "validated_basis": "log-deviation SS by construction (all zeros)",
        "validated_at": ts,
        "residuals": {"all": 0.0},
        "timestamp": ts,
    }
    (CKPT / "nk_ss.json").write_text(
        json.dumps(ss_ckpt, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("wrote results/checkpoints/nk_ss.json")

    pol_ckpt = {
        "model": "nk_three_eq",
        "order": 1,
        "language": "Python 3.13",
        "solver": "Klein 2000 generalised Schur (scipy.linalg.ordqz)",
        "seed": int((ROOT / "code" / "seed.txt").read_text().strip()),
        "params": p,
        "composite_coeffs": cc,
        "var_names": VAR_NAMES,
        "state_names":  VAR_NAMES[:N_STATES],
        "jumper_names": VAR_NAMES[N_STATES:],
        "n_states": N_STATES,
        "n_jumpers": N_JUMPERS,
        "P_state_transition": P.tolist(),
        "F_policy":            F.tolist(),
        "eigenvalues_real": [float(np.real(e)) for e in eigvals],
        "eigenvalues_imag": [float(np.imag(e)) for e in eigvals],
        "bk_pass": True,
        "validated": True,
        "validation_basis": "BK condition holds AND log-dev SS by construction",
        "validated_at": ts,
        "timestamp": ts,
    }
    (CKPT / "nk_policy.json").write_text(
        json.dumps(pol_ckpt, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("wrote results/checkpoints/nk_policy.json")
    log.info("============ done ============")
    return 0


if __name__ == "__main__":
    sys.exit(main())
