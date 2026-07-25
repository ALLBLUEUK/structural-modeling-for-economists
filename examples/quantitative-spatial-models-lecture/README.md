# Quantitative Spatial Models: Lecture and Replication

This directory contains the complete English lecture deck and the Julia code
used to construct its synthetic baseline, solve the level and exact-hat
equilibria, run four counterfactual experiments, and generate the figures.

## Main files

- `quantitative_spatial_models.pdf`: compiled 79-page lecture deck.
- `quantitative_spatial_models.tex`: Beamer source.
- `worked_example_*.png`: figures embedded in the lecture.
- `replication_package/`: cleaned Julia replication code, tests, environment
  files, generated figures, and detailed documentation.

## Reproduce the numerical results

From `replication_package`:

```powershell
julia --project=. -e "using Pkg; Pkg.instantiate()"
julia --project=. test/runtests.jl
julia --project=. run_all.jl
```

To regenerate the figures and copy the lecture PNGs into the parent directory:

```powershell
julia --project=. run_all.jl --sync-slide
```

## Compile the lecture

From this directory:

```powershell
xelatex -interaction=nonstopmode -halt-on-error quantitative_spatial_models.tex
xelatex -interaction=nonstopmode -halt-on-error quantitative_spatial_models.tex
```

The numerical exercise uses fixed random seeds. See
`replication_package/README.md` for model settings, shock definitions, output
mapping, and validation details.
