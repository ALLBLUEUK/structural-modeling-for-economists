# strucmod v0.3.0 工作流 build-tables：由结果 CSV 生成 LaTeX 表（报告中的表不经手工转录）
# 输入：output/tables/*.csv；输出：output/latex/armington_tariff/*.tex
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
TB, OUT = ROOT / "output" / "tables", ROOT / "output" / "latex" / "armington_tariff"
OUT.mkdir(parents=True, exist_ok=True)
rows = list(csv.DictReader(open(TB / "armington_tariff_cf_summary.csv", encoding="utf-8")))
L = [r"\begin{tabular}{llrrrrrr}", r"\toprule",
     r"情形 & 地区 & 福利 & 工资 & 关税收入项 & 价格指数项 & 制造业就业 & 其他部门就业 \\", r"\midrule"]
for k, r in enumerate(rows):
    if k == 3:
        L.append(r"\midrule")
    L.append(f"{r['scenario']} & {r['region']} & {float(r['welfare_pct']):.4f} & {float(r['wage_pct']):.3f} & "
             f"{float(r['decomp_tariff_revenue_pct']):.3f} & {float(r['decomp_price_index_pct']):.3f} & "
             f"{float(r['MAN_employment_pct']):.3f} & {float(r['OTH_employment_pct']):.3f} \\\\")
L += [r"\bottomrule", r"\end{tabular}"]
(OUT / "tab_scenarios.tex").write_text("\n".join(L) + "\n", encoding="utf-8")
rob = list(csv.DictReader(open(TB / "armington_tariff_robustness_eps.csv", encoding="utf-8")))
L = [r"\begin{tabular}{rrrrr}", r"\toprule",
     r"$\varepsilon_{MAN}$ & S1：A & S1：B & S2：A & S2：B \\", r"\midrule"]
for r in rob:
    L.append(f"{r['eps_MAN']} & {float(r['S1_A_welfare_pct']):.4f} & {float(r['S1_B_welfare_pct']):.4f} & "
             f"{float(r['S2_A_welfare_pct']):.4f} & {float(r['S2_B_welfare_pct']):.4f} \\\\")
L += [r"\bottomrule", r"\end{tabular}"]
(OUT / "tab_robustness.tex").write_text("\n".join(L) + "\n", encoding="utf-8")
print("ok")
