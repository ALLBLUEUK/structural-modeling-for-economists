# 60/30/10 Spatial Baseline Recalibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recalibrate the teaching baseline to 60 percent own-location, 30 percent domestic-nonlocal, and 10 percent foreign expenditure; correct the two liberalization shocks; regenerate and verify all four counterfactuals, figures, documentation, and the final PDF.

**Architecture:** Keep the existing three-module Julia package. `BaselineModel.jl` owns the rounded teaching wedges and expenditure-share moments, `ExactHat.jl` owns shock definitions and counterfactual solutions, and `Figures.jl` reports only objects produced by that common chain. Tests establish the approximate target moments and distinguish the domestic interlocation wedge from the international border wedge.

**Tech Stack:** Julia 1.10, `Test`, `LinearAlgebra`, `Statistics`, `StatsBase`, `Plots`, XeLaTeX, and PDF page rendering.

## Global Constraints

- Keep `d[n,i]` indexed as the delivery cost from supplier `i` to destination `n`.
- Use the rounded distance power `0.35`; preserve `productivity_log_sd = 1.0`, `sigma = 5.0`, `kappa = 1.5`, and all fixed random seeds.
- Use the rounded wedges `tau_D = 2.00` and `tau_B = 1.05`.
- Target aggregate expenditure shares are 0.60 own-location, 0.30 domestic-nonlocal, and 0.10 cross-country.
- Internal liberalization removes only `tau_D` on domestic nonlocal pairs.
- Bilateral liberalization removes only `tau_B` on cross-country pairs.
- Road and development-zone constructions retain their current seeds and magnitudes.
- Do not modify original lecture inputs outside the synthesis folder.
- The current directory is not a Git repository; commit steps do not apply.

---

### Task 1: Lock the Revised Baseline and Shock Definitions with Failing Tests

**Files:**
- Modify: `replication_package/test/runtests.jl`

**Interfaces:**
- Consumes: `BaselineSettings`, `build_baseline_fundamentals`,
  `solve_level_equilibrium`, and `build_counterfactuals`.
- Produces: regression tests for exact settings, target moments, and distinct
  liberalization hats.

- [ ] **Step 1: Replace obsolete setting assertions**

```julia
@test fund.settings.distance_power == 0.35
@test fund.settings.internal_trade_factor == 2.0
@test fund.settings.international_border_factor == 1.05
```

- [ ] **Step 2: Add aggregate expenditure-share assertions**

```julia
E = sol.w .* sol.L
total_E = sum(E)
own_share = sum(E .* diag(sol.pi)) / total_E
foreign_share =
    sum((E .* ones(1, fund.NN)) .* sol.pi .* fund.cross_border) / total_E
domestic_nonlocal_share = 1.0 - own_share - foreign_share
@test own_share ≈ 0.60 atol=0.01
@test domestic_nonlocal_share ≈ 0.30 atol=0.01
@test foreign_share ≈ 0.10 atol=0.01
```

- [ ] **Step 3: Make the shock tests distinguish the two wedges**

```julia
@test all(
    experiments.internal.shock.d_hat[domestic_nonlocal] .==
    1.0 / fund.settings.internal_trade_factor
)
@test all(experiments.internal.shock.d_hat[fund.cross_border] .== 1.0)
@test all(
    experiments.integration.shock.d_hat[fund.cross_border] .==
    1.0 / fund.settings.international_border_factor
)
```

- [ ] **Step 4: Run tests and verify the expected failures**

Run:

```powershell
julia --project=replication_package replication_package/test/runtests.jl
```

Expected: failures at obsolete default settings, target shares, and internal
shock factor.

---

### Task 2: Implement and Report the Calibrated Baseline

**Files:**
- Modify: `replication_package/src/BaselineModel.jl`
- Modify: `replication_package/test/runtests.jl`

**Interfaces:**
- Produces:
  - revised `BaselineSettings()` defaults;
  - `baseline_trade_moments(solution, fundamentals)`.

- [ ] **Step 1: Export a single moment function**

```julia
export BaselineSettings,
       legacy_baseline_settings,
       build_baseline_fundamentals,
       solve_level_equilibrium,
       baseline_residuals,
       baseline_trade_moments
```

- [ ] **Step 2: Replace the three trade-cost defaults with rounded teaching values**

```julia
distance_power::Float64 = 0.35
internal_trade_factor::Float64 = 2.0
international_border_factor::Float64 = 1.05
```

- [ ] **Step 3: Implement the authoritative moment calculation**

```julia
function baseline_trade_moments(sol, fund)
    expenditure = sol.w .* sol.L
    total = sum(expenditure)
    own =
        sum(expenditure .* diag(sol.pi)) / total
    foreign =
        sum(
            (expenditure .* ones(1, fund.NN)) .*
            sol.pi .* fund.cross_border,
        ) / total
    return (
        own_location = own,
        domestic_nonlocal = 1.0 - own - foreign,
        foreign = foreign,
    )
end
```

- [ ] **Step 4: Update tests to call `baseline_trade_moments`**

```julia
moments = baseline_trade_moments(sol, fund)
@test moments.own_location ≈ 0.60 atol=0.01
@test moments.domestic_nonlocal ≈ 0.30 atol=0.01
@test moments.foreign ≈ 0.10 atol=0.01
```

- [ ] **Step 5: Run baseline tests**

Run the complete Julia test file. Expected: baseline setting, cost
decomposition, equilibrium, and 60/30/10 moment tests pass; the uncorrected
internal-shock test still fails.

---

### Task 3: Correct and Verify the Two Liberalization Shocks

**Files:**
- Modify: `replication_package/src/ExactHat.jl`
- Modify: `replication_package/test/runtests.jl`

**Interfaces:**
- Consumes: calibrated `fund.settings`.
- Produces: economically distinct `internal` and `integration` shocks.

- [ ] **Step 1: Correct the internal cost hat**

```julia
internal_d_hat = ifelse.(
    fund.cross_border,
    1.0,
    1.0 / fund.settings.internal_trade_factor,
)
for location in 1:NN
    internal_d_hat[location, location] = 1.0
end
```

- [ ] **Step 2: Preserve the bilateral border cost hat**

```julia
d_hat = ifelse.(
    fund.cross_border,
    1.0 / fund.settings.international_border_factor,
    1.0,
)
```

- [ ] **Step 3: Add level-versus-hat consistency tests**

For representative domestic nonlocal, international, and own-location pairs,
verify that `fund.d .* d_hat` equals the intended counterfactual cost:

```julia
@test fund.d[n_dom, i_dom] *
      experiments.internal.shock.d_hat[n_dom, i_dom] ≈
      fund.icebergcost[n_dom, i_dom]
@test fund.d[n_cross, i_cross] *
      experiments.integration.shock.d_hat[n_cross, i_cross] ≈
      fund.icebergcost[n_cross, i_cross] *
      fund.settings.internal_trade_factor
```

- [ ] **Step 4: Run all Julia tests**

Expected: all specification, equilibrium, identity-shock, road,
development-zone, welfare, and shock-definition tests pass.

---

### Task 4: Regenerate Outputs and Update Documentation

**Files:**
- Modify: `replication_package/src/Figures.jl`
- Modify: `replication_package/run_all.jl`
- Modify: `replication_package/README.md`
- Modify: `quantitative_spatial_models.tex`

**Interfaces:**
- Consumes: one calibrated baseline and four exact-hat results.
- Produces: updated summary, PNGs, slide copies, and teaching text.

- [ ] **Step 1: Pass all baseline moments and four statistics to the summary**

Compute:

```julia
moments = baseline_trade_moments(base, fund)
internal_stats = counterfactual_statistics(experiments.internal.result, base, fund)
integration_stats = counterfactual_statistics(experiments.integration.result, base, fund)
road_stats = counterfactual_statistics(experiments.road.result, base, fund)
development_stats =
    counterfactual_statistics(experiments.development.result, base, fund)
```

Update `write_replication_summary` to report all three moments, both rounded
wedges, every solver's convergence diagnostics, and all four country-welfare
results.

- [ ] **Step 2: Update README calibration evidence and definitions**

Document the Chinese MRIO 2018/2020 local shares, the 60/30/10 target, exact
values of `tau_D` and `tau_B`, and the corrected meaning of each
liberalization.

- [ ] **Step 3: Update slide text without adding new main-text pages**

Replace obsolete 1.30 calibration text and ensure counterfactual shock slides
describe:

```tex
\rho=0.35,\qquad \tau_D=2,\qquad \tau_B=1.05,
```

with internal and bilateral liberalization removing their own wedges.

- [ ] **Step 4: Regenerate and sync every figure**

Run:

```powershell
julia --project=replication_package replication_package/run_all.jl --sync-slide
```

Expected: baseline and all four shock/result figures are overwritten from the
same revised baseline; every exact-hat solver converges.

---

### Task 5: Numerical, Visual, and PDF Completion Audit

**Files:**
- Verify: `replication_package/output/replication_summary.txt`
- Verify: `replication_package/figures/*.png`
- Verify: `quantitative_spatial_models.tex`
- Verify: `quantitative_spatial_models.pdf`

**Interfaces:**
- Produces: evidence that every explicit goal requirement is complete.

- [ ] **Step 1: Run the complete tests in a fresh Julia process**

```powershell
julia --project=replication_package replication_package/test/runtests.jl
```

Expected: all tests pass.

- [ ] **Step 2: Audit numerical evidence**

Confirm from the generated summary:

- each baseline expenditure share lies within one percentage point of the
  60/30/10 target;
- level and four exact-hat solvers converged;
- trade shares add to one;
- goods markets clear within the package tolerance;
- all country welfare numbers and plotted hats are finite.

- [ ] **Step 3: Inspect every revised PNG**

Check titles, axes, West-East divider, colorbar endpoints, spatial variation,
and absence of clipping or large unused margins.

- [ ] **Step 4: Compile the lecture**

```powershell
latexmk -xelatex -interaction=nonstopmode quantitative_spatial_models.tex
```

Expected: exit code zero, with no undefined references or missing figures.

- [ ] **Step 5: Render and inspect affected PDF pages**

Render baseline-input, baseline-observable, and all eight counterfactual pages.
Confirm correct order, readable labels, no overlap, and figures corresponding
to the revised outputs.

- [ ] **Step 6: Perform requirement-by-requirement final audit**

Match each goal clause to its authoritative evidence: source lines, passing
test, summary output, regenerated figure, compiled PDF, and rendered-page
inspection. Keep the goal active unless every clause is proven.
