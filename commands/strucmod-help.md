---
description: Show what the strucmod plugin can do and how to use it.
---

# /strucmod-help — strucmod plugin overview

The user typed `/strucmod-help` and wants a quick orientation. Reply with a concise overview in Chinese (since most users of this plugin are Chinese-speaking graduate students), structured as:

## What you should print back to the user

1. **What this plugin is** (1 sentence): an agent-assisted pipeline that turns a one-line research question into a publication-grade economics paper PDF.

2. **The 6 stages**:
   - 设定 (spec) — `setup-dsge` / `setup-cge-gtap` / `setup-ha-bewley`
   - 校准 (calibrate) — `calibrate-from-moments`
   - 求解 (solve) — `solve-perturbation` / `solve-vfi`
   - 仿真 (simulate) — `simulate-irf` / `counterfactual-run`
   - 写论文 (write) — `paper-structure` + `write-introduction` / `write-model-section` / ... / `write-conclusion`
   - 编译 (render) — `render-paper` 出 PDF

3. **3 evaluation gates** (where mistakes get caught):
   - `model-reviewer` + `math-reviewer` 审 spec
   - `numerics-reviewer` + `validate-steady-state` 审求解
   - `paper-reviewer` + `verifier` 审最终论文

4. **Recommended next commands**:
   - `/strucmod-new` — start a new research project from scratch
   - 自然语言任意提问 — e.g. "帮我建一个标准 RBC 模型并把全套论文写出来"

5. **Where to read more**:
   - 主入口 skill：`<plugin>/skills/strucmod/SKILL.md`
   - 学术写作规则：`<plugin>/rules/academic-writing-style.md`
   - GitHub: https://github.com/ALLBLUEUK/structural-modeling-for-economists

Keep the whole response under 30 lines. Do not list all 32 skills — just the categories.
