# Quantitative Spatial Model - Lecture Replication Package

This folder contains only the cleaned code used by the revised lecture:

```text
baseline fundamentals
    -> level equilibrium
    -> baseline observables {w, L, P, pi, lambda}
    -> exact-hat counterfactuals
    -> figures and summary statistics
```

Every table and figure uses the same solved baseline. The package does not
replace the bilateral expenditure matrix or spatial distributions with
separately generated plotting data.

## 1. Environment and commands

- Julia 1.10 or later
- `Plots.jl`
- `StatsBase.jl`

From `replication_package`:

```powershell
julia --project=. -e "using Pkg; Pkg.instantiate()"
julia --project=. test/runtests.jl
julia --project=. run_all.jl
```

To regenerate the package outputs and copy the lecture PNGs into the parent
slide folder:

```powershell
julia --project=. run_all.jl --sync-slide
```

## 2. Revised baseline

| Object | Setting |
|---|---|
| Grid | 30 x 30 locations |
| Countries | West and East halves of the grid |
| Baseline random seed | `42` |
| Productivity | `sd(log(A_i)) = 1.0`; country geometric means normalized to one |
| Housing | `H_i = 100` |
| Labor | 100,000; 50,000 in each country |
| Parameters | `alpha = 0.75`, `sigma = 5`, `kappa = 1.5`, `F = 1` |
| Normalized amenity | `B_i = 1` |
| Wage numeraire | geometric-mean West wage equals one |

The matrix is indexed `d[n,i]`: the iceberg cost of delivery from supplier
location `i` to destination location `n`.

```text
own location:
    d[n,i] = 1

nonlocal pair:
    d[n,i] = distance[n,i]^0.35 * tau_D

cross-country pair:
    d[n,i] = (distance[n,i] / s_B)^0.35 * tau_D * tau_B
```

The teaching baseline uses rounded, interpretable values:

```text
distance power = 0.35
tau_D = 2.00       # a 100% nonlocal interregional wedge
tau_B = 2.00       # an additional international-border factor
s_B = 6.303        # normalization of cross-country effective distance
```

They approximately reproduce the expenditure-weighted targets:

| Source of purchases | Target | Solved baseline |
|---|---:|---:|
| Own location | 60% | 59.92% |
| Other locations in the same country | 30% | 30.78% |
| Other country | 10% | 9.30% |

The 60 percent local target is guided by China's public provincial MRIO
evidence. Aggregating intermediate and final demand and including foreign
imports gives local shares of approximately 66.1 percent in 2018 and
57.6 percent in 2020. The exercise uses the rounded 60/30/10 target.

Data reference: Li et al. (2025),
[China's Provincial Multi-Regional Input-Output Database for 2018 and
2020](https://doi.org/10.1038/s41597-025-06543-y). The international
order-of-magnitude check also uses 2024 bilateral trade shares from the
[U.S. Census Bureau](https://www.census.gov/foreign-trade/statistics/highlights/top/top2412yr.html).

## 3. Counterfactuals

All four experiments start from the same revised baseline.

| Experiment | Shock |
|---|---|
| Internal trade liberalization | domestic nonlocal cost hat equals `1 / tau_D`; cross-country costs unchanged |
| Bilateral border liberalization | cross-country cost hat equals `1 / tau_B`; domestic costs unchanged |
| Road construction | traversal costs on the seeded West-East road fall to one half; all OD least-cost routes are recomputed |
| Development zones | productivity rises by 20% in three seeded West-side zones near the border |

Reproducible geography:

| Object | Fixed seed |
|---|---:|
| Continuous simulated road | `20260724` |
| Three separated development zones | `20260725` |

## 4. Source responsibilities

- `src/BaselineModel.jl`
  - constructs geography, fundamentals, and the three-part trade-cost matrix;
  - solves the level equilibrium;
  - computes equilibrium residuals and the baseline moments used to assess the
    approximate 60/30/10 target.
- `src/ExactHat.jl`
  - defines all exact-hat shocks;
  - solves wage, population, price-index, and expenditure-share hats;
  - computes country summary statistics and welfare.
- `src/Figures.jl`
  - receives solved model objects only;
  - produces figures and the replication summary.
- `run_all.jl`
  - runs the complete chain once and writes every output.
- `calibrate_round_costs.jl`
  - compares nearby rounded teaching specifications against the 60/30/10
    targets; it never inserts long calibration decimals into the baseline.
- `test/runtests.jl`
  - verifies target fit, indexing, market clearing, shock definitions,
    convergence, plotting rules, and slide consistency.

## 5. Output mapping

| File | Content |
|---|---|
| `worked_example_fundamentals.png` | spatially varying baseline productivity `A` |
| `worked_example_trade_costs.png` | baseline `d[n,i]` |
| `worked_example_baseline.png` | baseline wage, population, land rent, and price index |
| `worked_example_trade_matrix.png` | bilateral `pi[n,i]` and trade-cost–bilateral-expenditure relationship |
| `worked_example_shock_internal.png` | internal-liberalization trade-cost hats |
| `worked_example_results_internal.png` | internal-liberalization outcomes |
| `worked_example_shock_integration.png` | bilateral-border trade-cost hats |
| `worked_example_results_integration.png` | bilateral-border outcomes |
| `worked_example_shock_road.png` | seeded road traversal-cost hats |
| `worked_example_results_road.png` | road-construction outcomes |
| `worked_example_shock_development.png` | development-zone productivity hats |
| `worked_example_results_development.png` | development-zone outcomes |

Baseline population and expenditure shares use levels. Counterfactual maps use
ordinary percentage changes, `100 * (hat - 1)`, with continuous color scales
and truncated display limits where needed; the underlying values are never
truncated.

## 6. Outputs

`run_all.jl` writes:

- `figures/*.png`;
- `output/baseline.jls`;
- `output/replication_summary.txt`.

`replication_summary.txt` reports solved baseline moments, solver convergence,
equilibrium residuals, and country results for all four counterfactuals.

`legacy_baseline_settings()` remains available only for parity checks against
the read-only original lecture script.
