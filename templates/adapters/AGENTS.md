# AGENTS.md — agent-universal entry for this research project

This project follows the [agents.md](https://agents.md) convention. Codex, Aider, Cursor, GitHub Copilot, Windsurf, and any agent that respects the `AGENTS.md` standard will read this file first.

## Project type

This is a **structural modeling and academic-paper composition project** for economics graduate research. The workflow follows the `strucmod` pipeline:

```
spec.md → model-reviewer → calibration.csv → validate-steady-state
       → solve-* → simulate-* → write paper sections → render PDF → verifier
```

## Where the procedures live

The pipeline (skills, agents, rules) lives in **`<plugin-root>/skills/`, `<plugin-root>/agents/`, `<plugin-root>/rules/`**. Depending on how this project installed the plugin, `<plugin-root>` is one of:

- `.claude/plugins/strucmod/` (local plugin install)
- `~/.claude/plugins/strucmod/` (global / user-level plugin install)
- A custom path declared in the project's `.codex/config.toml` or similar

## Mandatory reading on session start

1. This file (`AGENTS.md`)
2. `<plugin-root>/skills/strucmod/SKILL.md` — entry decision tree
3. `<plugin-root>/rules/orchestrator-protocol.md`
4. `<plugin-root>/rules/plan-first-modeling.md`
5. `<plugin-root>/rules/academic-writing-style.md` — non-negotiable writing rules
6. `<plugin-root>/rules/numerical-validation-protocol.md`
7. `<plugin-root>/rules/replication-protocol.md`
8. `<plugin-root>/rules/modeling-coding-conventions.md`

## Hard constraints (excerpt — full list in `<plugin-root>/rules/`)

- No quantitative claim in the manuscript without a corresponding artifact in `results/checkpoints/` or `results/tables/`.
- No model code without a `spec.md` approved by `model-reviewer`.
- No paper section without `paper-reviewer` approval.
- All comments default to Chinese; all manuscript prose in English unless the user requests otherwise.
- Random seed lives in `code/seed.txt`; never hardcode.
- Steady-state residuals must drop below `1e-8` before any IRF or counterfactual is reported.
- Figures exported as both `.pdf` and `.png` to `results/figures/`; `.pdf` mirrored into `paper/figures/`.

## Project layout (this project)

```
<project>/
├── paper/             ← LaTeX manuscript (main.tex + sections/ + appendix/ + references.bib + paper.pdf)
├── code/              ← analysis scripts (01_calibration.csv, 02_solve.py, 03_simulate.py, …)
├── data/{raw,clean}/  ← gitignored datasets
├── results/           ← intermediate artifacts (checkpoints/, figures/, tables/)
├── logs/              ← run logs (gitignored)
├── slides/            ← presentation drafts (optional)
├── references/        ← bibliography notes (optional)
└── .claude/plugins/strucmod/  ← (only if locally installed) the plugin
```

If a section of `<plugin-root>` cannot be found, the plugin is not installed; halt and tell the user to install it (see project README).
