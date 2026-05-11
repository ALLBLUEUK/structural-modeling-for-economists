---
description: Start a brand-new structural-modeling research project (creates academic project layout + invites you to describe the model).
---

# /strucmod-new — start a new structural modeling research project

You have been asked to start a new structural-modeling research project. The user typed `/strucmod-new` in Claude Code.

## What you should do

1. **Ask the user for the basics** (one combined question, not four separate ones):
   - A short working title for the paper.
   - The model class: DSGE / CGE / heterogeneous-agent / dynamic programming / empirical.
   - The core research question in one sentence.
   - (Optional) Any specific calibration target or data they want to use.

2. After they answer, follow the `strucmod` entry skill (`skills/strucmod/SKILL.md`) decision tree:
   - Run `paper-structure` skill to scaffold `paper/`, `code/`, `data/`, `results/`, `slides/`, `references/` in the current directory.
   - Run the appropriate `setup-<class>` skill (e.g. `setup-dsge`) to draft `code/<model>/spec.md`.
   - Submit the spec to `model-reviewer` and `math-reviewer` for sanity check.

3. Stop after spec approval and ask the user to confirm before proceeding to calibration + solving + simulating + writing.

## Hard constraints

- Do not assume an existing project layout — create fresh dirs if missing.
- Do not write any code before the spec is approved by `model-reviewer`.
- Default code comments to Chinese; default manuscript prose to English.
- All artifacts go in the standard layout — do not invent new top-level folders.

## Reference

Full pipeline overview lives in the plugin's `skills/strucmod/SKILL.md`. The academic-writing rule that governs the final paper is in `rules/academic-writing-style.md`.
