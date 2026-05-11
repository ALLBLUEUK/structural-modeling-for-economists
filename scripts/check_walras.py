#!/usr/bin/env python3
"""
check_walras.py —— CGE / 一般均衡模型的 Walras 律校验

按 numerical-validation-protocol：
- 在所有市场出清方程满足后，剩余的"全经济总价值"约束应自动满足（Walras 律）。
- 数值上：把 baseline 求解后的所有市场剩余加总，应在容差内为 0。
- 同时校验 SAM（社会账户矩阵）行和 = 列和。

用法：
    python scripts/check_walras.py output/checkpoints/<model>_baseline.json
    python scripts/check_walras.py output/checkpoints/<model>_baseline.json --tol 1e-6

退出码：
    0  通过
    1  使用错误
    2  超过容差
    3  缺字段 / 文件错误
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="Walras 律 + SAM 平衡校验")
    p.add_argument("checkpoint", type=Path,
                   help="output/checkpoints/<model>_<scenario>.json (CGE)")
    p.add_argument("--tol", type=float, default=1e-6,
                   help="Walras 残差容差（默认 1e-6）")
    p.add_argument("--report-dir", type=Path, default=Path("quality_reports"))
    args = p.parse_args()

    if not args.checkpoint.exists():
        print(f"[ERR] 找不到 checkpoint：{args.checkpoint}", file=sys.stderr)
        return 3

    try:
        data = json.loads(args.checkpoint.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[ERR] checkpoint 不是合法 JSON：{e}", file=sys.stderr)
        return 3

    model = data.get("model", "<unknown>")
    market_clearing = data.get("market_clearing_residuals")
    sam = data.get("sam_balance")  # {"rows":[...], "cols":[...]}

    if market_clearing is None and sam is None:
        print(
            f"[ERR] checkpoint 中既无 market_clearing_residuals 也无 sam_balance；\n"
            f"     CGE 求解器后处理必须输出二者之一。\n"
            f"     market_clearing_residuals: 字典 {{market_name: residual}}\n"
            f"     sam_balance: {{'rows':[...], 'cols':[...]}} 行和列和数组",
            file=sys.stderr,
        )
        return 3

    pass_walras = True
    pass_sam = True
    notes: list[str] = []

    # ----- Walras 律 -----
    if market_clearing is not None:
        residuals = {k: abs(float(v)) for k, v in market_clearing.items()}
        max_market, max_r = max(residuals.items(), key=lambda kv: kv[1])
        n_fail = sum(1 for r in residuals.values() if r >= args.tol)
        notes.append(
            f"市场出清残差最大：{max_market} = {max_r:.3e}（容差 {args.tol:.0e}）"
        )
        if n_fail:
            pass_walras = False

    # ----- SAM 平衡 -----
    if sam is not None:
        rows = [float(x) for x in sam.get("rows", [])]
        cols = [float(x) for x in sam.get("cols", [])]
        if len(rows) != len(cols) or not rows:
            notes.append("SAM 行列长度不一致或为空")
            pass_sam = False
        else:
            diffs = [abs(r - c) for r, c in zip(rows, cols)]
            max_diff = max(diffs)
            notes.append(f"SAM 行和-列和最大差：{max_diff:.3e}（容差 1e-9）")
            if max_diff >= 1e-9:
                pass_sam = False

    overall = pass_walras and pass_sam

    args.report_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report = args.report_dir / f"{model}_walras_{ts}.md"
    lines = [
        f"# Walras 律 + SAM 平衡报告 · {model} · {ts}",
        "",
        f"- checkpoint：`{args.checkpoint}`",
        f"- 容差：Walras={args.tol:.0e}，SAM=1e-9",
        f"- Walras 通过：{'✅' if pass_walras else '❌'}",
        f"- SAM 通过：{'✅' if pass_sam else '❌'}",
        f"- 综合：{'✅ PASS' if overall else '❌ FAIL'}",
        "",
        "## 详情",
    ]
    lines.extend(f"- {n}" for n in notes)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[check_walras] 报告写入：{report}")
    print(f"[check_walras] {'通过' if overall else '失败'}")
    return 0 if overall else 2


if __name__ == "__main__":
    sys.exit(main())
