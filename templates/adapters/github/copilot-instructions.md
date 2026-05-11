# GitHub Copilot — strucmod project instructions

This repository is a structural-modeling and academic-paper composition project. The canonical instruction source is **AGENTS.md** at the repository root; please read it for the full pipeline ordering and hard constraints. Copilot's job here is to suggest code and prose that respect those rules.

## When suggesting code

1. Use **relative paths**, never hardcoded absolute paths.
2. Pin language version at the top of each script (Python 3.11+, Julia 1.10+, Dynare 6.x, etc.).
3. Read the project random seed from `code/seed.txt`; never hardcode.
4. Write all artifacts to the standard project layout (`results/checkpoints/`, `results/figures/`, `results/tables/`, `paper/figures/`, `logs/`).
5. **Code comments default to Chinese**, unless the user explicitly requests another language.

## When suggesting manuscript prose

Follow the strict `academic-writing-style` rule documented in the plugin (`<plugin-root>/rules/academic-writing-style.md`):

- No machine paths in the body (`results/checkpoints/...`, `code/03_solve/...`).
- No pipeline / agent / plugin terms (`pipeline`, `sub-agent`, `verifier`, `Claude`, `Codex`, `AI-assisted`).
- No bash commands (`python ...`, `pdflatex ...`).
- No meta-annotations (`auto-drafted`, `verifier-pending`).
- Use formal academic voice (present tense for definitions; passive voice acceptable).
- Use `\citet{}` / `\citep{}` for citations; all keys must exist in `paper/references.bib`.

## Mandatory pipeline ordering

```
spec.md → model-reviewer → calibration.csv → validate-steady-state
       → solve-* → simulate-* → write paper sections → render PDF → verifier
```

Never skip steady-state validation before reporting any IRF or counterfactual.
