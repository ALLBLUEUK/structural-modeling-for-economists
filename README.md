# Structural Modeling for Economists

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-plugin-blue)](https://github.com/anthropics/claude-code)
[![Codex Compatible](https://img.shields.io/badge/Codex-AGENTS.md-green)](https://agents.md)
[![Cursor Compatible](https://img.shields.io/badge/Cursor-rules-purple)](https://cursor.com)

**An AI-agent pipeline that turns one-line research questions into publication-grade economics papers.**

DSGE, CGE, heterogeneous-agent, dynamic-programming — model spec → calibration → solve → simulate → write a real academic paper (introduction, model, calibration, solution, results, robustness, conclusion, references) → compile to PDF.

> Output of UIBE 2025 Graduate Education Reform Project · *AI Multi-Tool Coordinated Empowerment of Graduate Structural Modeling and Dynamic Simulation Research and Practice* · 贾宁远.

---

## What's inside

- **30+ skills** — `setup-dsge`, `setup-cge-gtap`, `setup-ha-bewley`, `calibrate-from-moments`, `solve-perturbation`, `solve-vfi`, `simulate-irf`, `counterfactual-run`, plus 8 paper-composition skills (`paper-structure`, `write-introduction`, `write-model-section`, `write-calibration-section`, `write-solution-section`, `write-results-section`, `write-conclusion`, `manage-bibliography`, `render-paper`).
- **7 review subagents** — `model-reviewer`, `math-reviewer`, `numerics-reviewer`, `code-reviewer`, `pedagogy-reviewer`, `paper-reviewer`, `verifier`.
- **6 cross-cutting rules** — `orchestrator-protocol`, `plan-first-modeling`, `numerical-validation-protocol`, `replication-protocol`, `modeling-coding-conventions`, **`academic-writing-style`** (zero implementation leak, formal voice, citation discipline).
- **Paper templates** — `main.tex` + 7 section skeletons + appendix + a starter `references.bib` pre-filled with canonical citations.
- **Adapter shims** — one for every supported agent (see install section below).

What it produces: a self-contained research project (`paper/`, `code/`, `data/`, `results/`, `slides/`, `references/`) and a publication-grade `paper/paper.pdf` — 8–15 pages with full academic structure, zero implementation leakage.

---

## Install — choose your agent

### Option 1 · Claude Code (recommended)

#### 1A. Global install via marketplace — *one-time setup, then works in any project*

Inside Claude Code:

```text
/plugin marketplace add https://github.com/ALLBLUEUK/structural-modeling-for-economists
/plugin install strucmod
```

That's it. Every Claude Code session in any directory knows the pipeline. No per-project setup.

#### 1B. Project-level install — *plugin scoped to one project's `.claude/`*

```bash
cd ~/my-research-project
git clone https://github.com/ALLBLUEUK/structural-modeling-for-economists.git \
          .claude/plugins/strucmod
```

Restart Claude Code in the project; the plugin auto-loads.

#### 1C. User-level install (manual) — *equivalent to 1A without going through the marketplace*

```bash
git clone https://github.com/ALLBLUEUK/structural-modeling-for-economists.git \
          ~/.claude/plugins/strucmod
```

---

### Option 2 · Codex CLI

Codex natively reads `AGENTS.md` ([agents.md spec](https://agents.md)). The plugin ships an `AGENTS.md` template that tells Codex where to find skills and rules.

```bash
# 1) Install plugin once (global recommended):
git clone https://github.com/ALLBLUEUK/structural-modeling-for-economists.git \
          ~/.claude/plugins/strucmod

# 2) In each research project, drop AGENTS.md into the project root:
cd ~/my-research-project
cp ~/.claude/plugins/strucmod/templates/adapters/AGENTS.md ./AGENTS.md

# 3) Start Codex:
codex
```

Codex automatically reads `AGENTS.md` and follows the pipeline's procedures.

---

### Option 3 · Cursor

Cursor uses `.cursor/rules/*.mdc` for project rules.

```bash
cd ~/my-research-project

git clone https://github.com/ALLBLUEUK/structural-modeling-for-economists.git \
          ~/.claude/plugins/strucmod

mkdir -p .cursor/rules
cp ~/.claude/plugins/strucmod/templates/adapters/cursor/rules/strucmod.mdc \
   .cursor/rules/strucmod.mdc
cp ~/.claude/plugins/strucmod/templates/adapters/AGENTS.md ./AGENTS.md
```

Open the project in Cursor; the rule auto-loads.

---

### Option 4 · Aider

```bash
cd ~/my-research-project

git clone https://github.com/ALLBLUEUK/structural-modeling-for-economists.git \
          .claude/plugins/strucmod

cp .claude/plugins/strucmod/templates/adapters/.aider.conf.yml ./.aider.conf.yml
cp .claude/plugins/strucmod/templates/adapters/AGENTS.md ./AGENTS.md

aider
```

---

### Option 5 · Windsurf

```bash
cd ~/my-research-project

git clone https://github.com/ALLBLUEUK/structural-modeling-for-economists.git \
          ~/.claude/plugins/strucmod

cp ~/.claude/plugins/strucmod/templates/adapters/.windsurfrules ./.windsurfrules
cp ~/.claude/plugins/strucmod/templates/adapters/AGENTS.md ./AGENTS.md
```

Open the project in Windsurf.

---

### Option 6 · GitHub Copilot

```bash
cd ~/my-research-project

git clone https://github.com/ALLBLUEUK/structural-modeling-for-economists.git \
          ~/.claude/plugins/strucmod

mkdir -p .github
cp ~/.claude/plugins/strucmod/templates/adapters/github/copilot-instructions.md \
   .github/copilot-instructions.md
cp ~/.claude/plugins/strucmod/templates/adapters/AGENTS.md ./AGENTS.md
```

---

### Option 7 · One-shot multi-agent install (lazy mode)

Want every adapter installed at once so you can freely switch agents on the same project? Use the helper script:

```bash
git clone https://github.com/ALLBLUEUK/structural-modeling-for-economists.git \
          ~/.claude/plugins/strucmod

bash ~/.claude/plugins/strucmod/install.sh universal ~/my-research-project
```

This drops `AGENTS.md`, `.cursor/rules/strucmod.mdc`, `.github/copilot-instructions.md`, `.aider.conf.yml`, and `.windsurfrules` into your project root — pick whichever agent.

> **Claude Code users don't need install.sh** — option 1A handles everything natively.

---

## Usage — your first session

After install (any of the above), in your research project root:

```bash
claude   # or: codex / cursor / aider / etc.
```

Then ask, in natural language:

> "I want to study how a positive TFP shock propagates through a standard RBC economy. Use the plugin's pipeline: spec it out, calibrate to quarterly post-war U.S. values, solve, run 40-quarter IRFs, then write the whole paper (introduction, literature review, model, calibration, solution, results, robustness, conclusion, references), and compile a PDF."

The agent will:

1. Plan the model via `setup-dsge`, draft `code/<model>/spec.md`, submit to `model-reviewer` and `math-reviewer` for sanity check.
2. Calibrate (`calibrate-from-moments`), validate steady state (`validate-steady-state`), solve (`solve-perturbation`), simulate (`simulate-irf`).
3. Write each paper section via the `write-*` skills — each section reviewed by `paper-reviewer` for academic style (no file paths, no pipeline talk, no bash in body, formal voice, real citations).
4. Compile `paper/paper.pdf` via `render-paper` (pdflatex + bibtex).
5. Submit the final PDF to `verifier` + `paper-reviewer` for a clean-pass review.

What you get: a project structured like a real academic-paper repository (`paper/`, `code/`, `data/`, `results/`, `slides/`, `references/`) and a publication-grade `paper/paper.pdf`.

A **worked example** (RBC paper, 8-page PDF, Codex-verified for academic quality) lives in `rbc-demo-test/` alongside this repo.

---

## Plugin repository layout

```
structural-modeling-for-economists/
├── .claude-plugin/
│   ├── plugin.json          ← Claude Code plugin manifest
│   └── marketplace.json     ← single-plugin marketplace (for /plugin marketplace add)
├── skills/                  ← 30+ task skills
├── agents/                  ← 7 review subagents
├── rules/                   ← 6 cross-cutting protocols (incl. academic-writing-style)
├── hooks/                   ← Claude Code lifecycle scripts
├── scripts/                 ← shipped CLI utilities
├── templates/               ← reusable file templates
│   ├── paper/               ← complete paper skeleton (main.tex + sections + references.bib)
│   ├── model-spec-template.md
│   └── adapters/            ← agent-specific shim files
│       ├── AGENTS.md                  (agents.md spec entry — Codex etc.)
│       ├── cursor/rules/strucmod.mdc
│       ├── github/copilot-instructions.md
│       ├── .aider.conf.yml
│       └── .windsurfrules
├── install.sh               ← OPTIONAL multi-agent adapter installer (Claude Code doesn't need it)
├── README.md, LICENSE, CITATION.cff
```

---

## Why this exists

Most agent-assisted modeling pipelines stop at "run the model and dump figures." The unique value here is the `academic-writing-style` rule + 8 `write-*` skills, which force the agent to compose a **real academic paper** — formal voice, four-paragraph introduction with named recent literature, results with substantive economic interpretation (not a list of numbers), AEA-style references, no implementation leakage. The output is meant to be plausibly mistakable for a graduate student's working paper.

Standard pitfalls of AI-generated economics papers that this pipeline blocks:

- File paths in the body (`see output/checkpoints/rbc_ss.json`) → rejected by `paper-reviewer`.
- "By the pipeline" / "AI-generated" / "verifier-pending" language → rejected.
- Bash commands in the Reproducibility section → rejected (allowed only in repo `README.md`).
- Results with no economic interpretation → flagged for revision.
- "All variables return to steady state at horizon" when they don't → flagged.

---

## Citation

If this plugin helps your research, please cite per `CITATION.cff`.

## License

MIT. See `LICENSE`.
