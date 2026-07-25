# Quantitative Spatial Model Replication Package — Design

## Goal

Maintain one self-contained Julia replication package for the lecture figures.
The original lecture script remains read-only and is used only for legacy
parity checks.

The revised teaching baseline must match three aggregate expenditure shares:

- own-location purchases: 60 percent;
- purchases from other locations in the same country: 30 percent;
- purchases from the other country: 10 percent.

The 60/30/10 target is a stylized calibration guided by China's provincial
MRIO evidence. Aggregating the public 31-province, 42-sector tables gives local
shares of 66.1 percent in 2018 and 57.6 percent in 2020 after including foreign
imports. The teaching target rounds this evidence to 60 percent while retaining
the existing two-country structure.

## Single Source Chain

All reported objects and figures follow one chain:

1. construct the 30-by-30 spatial economy and baseline fundamentals;
2. solve the level equilibrium;
3. compute the three baseline expenditure-share moments;
4. retain baseline observables `w`, `L`, `P`, `pi`, and `lambda`;
5. define each counterfactual shock in exact-hat form;
6. solve the exact-hat equilibrium;
7. construct figures and summary statistics from those solutions.

No figure may regenerate, approximate, or replace baseline objects separately.

## Baseline Specification

- Random seed: `42`.
- Locations: `30 x 30`, numbered in Julia column-major order.
- Countries: West and East, each occupying one half of the grid.
- Distance: Euclidean distance between location centroids.
- Productivity: lognormal draw with log standard deviation `1.0`, normalized
  to geometric mean one within each country.
- Parameters: `alpha = 0.75`, `sigma = 5.0`, `kappa = 1.5`, and `F = 1.0`.
- Housing stock: `H_i = 100`.
- Labor endowment: `100,000`, split equally across countries.
- Other location fundamentals: `B_i = T_i = 1`.

Delivery costs retain three economically distinct components:

`d[n,i] = spatial[n,i] * interlocation[n,i] * border[n,i]`.

- `spatial[n,i] = distance[n,i]^0.35` for `n != i`, and one on the diagonal;
- `interlocation[n,i] = tau_D` for every nonlocal pair, and one on the diagonal;
- `border[n,i] = tau_B` for cross-country pairs, and one otherwise.

Rounded candidate specifications are compared by solving the level equilibrium
and minimizing the squared distance to the two independent targets:

`(own_share - 0.60)^2 + (foreign_share - 0.10)^2`.

The teaching specification uses transparent round values:

- distance power `0.35`;
- `tau_D = 2.00`, a 100 percent nonlocal interregional wedge;
- `tau_B = 1.05`, an additional 5 percent international-border wedge.

The solved baseline gives expenditure shares of 59.92 percent own-location,
30.78 percent domestic-nonlocal, and 9.30 percent cross-country. These are
reported as the approximate 60/30/10 teaching target.

## Counterfactual Definitions

All four counterfactuals use the same stored calibrated baseline.

1. **Internal liberalization:** remove the generic nonlocal interlocation
   wedge for domestic nonlocal pairs only. Set their cost hat to `1 / tau_D`;
   leave own-location and cross-country pairs unchanged.
2. **Bilateral border liberalization:** remove the additional international
   border wedge for every cross-country pair. Set their cost hat to
   `1 / tau_B`; leave all domestic pairs unchanged.
3. **Road construction:** retain the fixed road seed and lower traversal costs
   along the West-East route to one half. Recompute all origin-destination
   least-cost routes before constructing trade-cost hats.
4. **Development zones:** retain the fixed development-zone seed and apply the
   20 percent productivity increase to the three West-side zones near the
   border.

## Module Boundaries

- `src/BaselineModel.jl`: fundamentals, geography, level-equilibrium solver,
  and baseline-share moments.
- `src/ExactHat.jl`: exact-hat solver, shock construction, and counterfactual
  statistics.
- `src/Figures.jl`: plots and output tables; no equilibrium equations.
- `run_all.jl`: one reproducible entry point.
- `test/runtests.jl`: specification, moment, equilibrium, shock-definition,
  exact-hat, and slide-consistency tests.

## Validation

The revised package must establish all of the following:

- own, domestic-nonlocal, and foreign shares lie within one percentage point
  of the 60/30/10 teaching target;
- every row of `pi` sums to one;
- each country's population sums to 50,000;
- goods-market residuals are numerically small;
- the level and exact-hat solvers converge;
- an identity shock returns unit hats;
- internal liberalization removes `tau_D`, not `tau_B`;
- bilateral liberalization removes `tau_B`, not `tau_D`;
- all four counterfactual outputs are finite and economically interpretable;
- baseline population and bilateral expenditure-share figures use levels;
- every displayed figure is generated from the stored revised baseline;
- the Beamer source compiles successfully with XeLaTeX and affected pages pass
  visual inspection.

`legacy_baseline_settings()` remains available solely to verify numerical
parity with the original lecture script.

## Outputs

`run_all.jl` writes:

- all lecture PNG figures to `figures/`;
- a machine-readable baseline file to `output/baseline.jls`;
- a text summary of settings, target and achieved moments, convergence,
  residuals, and all four counterfactual results to
  `output/replication_summary.txt`;
- optionally, the same PNG files to the parent slide folder using
  `--sync-slide`.
