# strucmod v0.3.0 工作流 build-tables：由结果 CSV / 检查点生成 LaTeX 表（报告中的表不经手工转录）
# 输入：output/tables/*.csv、output/checkpoints/*_ss.json；输出：output/latex/aiyagari_borrowing/*.tex
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TB, CK = ROOT / "output" / "tables", ROOT / "output" / "checkpoints"
OUT = ROOT / "output" / "latex" / "aiyagari_borrowing"
OUT.mkdir(parents=True, exist_ok=True)

# 表 1：比较静态
rows = list(csv.DictReader(open(TB / "aiyagari_borrowing_comparative_statics.csv", encoding="utf-8")))
L = [r"\begin{tabular}{rrrrrrr}", r"\toprule",
     r"$b$ & $b/w$ & $r$（\%） & $K/Y$ & $s$（\%） & 受约束比例（\%） & 财富 Gini \\", r"\midrule"]
for r in rows:
    L.append(f"{float(r['b']):.1f} & {float(r['b_over_w']):.2f} & {float(r['r_pct']):.3f} & {float(r['K_over_Y']):.3f} & "
             f"{float(r['saving_rate_pct']):.2f} & {float(r['share_constrained_pct']):.2f} & {float(r['wealth_gini']):.3f} \\\\")
L += [r"\bottomrule", r"\end{tabular}"]
(OUT / "tab_comparative_statics.tex").write_text("\n".join(L) + "\n", encoding="utf-8")

# 表 2：收入离散化的稳健性（7 状态基准行 + 15 状态 + Tauchen 对照）
spec_rows = [("baseline", "Rouwenhorst"), ("rob_nz15_b0", "Rouwenhorst"), ("cmp_tauchen_b0", "Tauchen"),
             ("b2", "Rouwenhorst"), ("rob_nz15_b2", "Rouwenhorst"),
             ("b8", "Rouwenhorst"), ("rob_nz15_b8", "Rouwenhorst"), ("cmp_tauchen_b8", "Tauchen")]
L = [r"\begin{tabular}{lrrrrr}", r"\toprule",
     r"离散化方法 & 状态数 & $b$ & $r$（\%） & $s$（\%） & 对数收入方差相对误差（\%） \\", r"\midrule"]
prev_b = None
for name, meth in spec_rows:
    d = json.loads((CK / f"aiyagari_borrowing_{name}_ss.json").read_text(encoding="utf-8"))
    b = d["params"]["b"]
    if prev_b is not None and b != prev_b:
        L.append(r"\midrule")
    prev_b = b
    q = d["diagnostics"]["income_discretisation"]
    L.append(f"{meth} & {d['params']['n_z']} & {b:.0f} & {100 * d['steady_state']['r']:.3f} & "
             f"{100 * d['steady_state']['saving_rate']:.2f} & {100 * q['var_rel_error']:.1f} \\\\")
L += [r"\bottomrule", r"\end{tabular}"]
(OUT / "tab_robustness.tex").write_text("\n".join(L) + "\n", encoding="utf-8")
print("ok")
