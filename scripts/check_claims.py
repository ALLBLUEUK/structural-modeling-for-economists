#!/usr/bin/env python3
"""
check_claims.py —— 论文/报告中的数字与数据源逐条核对（strucmod v0.3 新增）

按 numerical-validation-protocol 的 Gate 3：任何对外报告的数字都必须能由数据源复算得到。
本脚本读取项目中的 claims.csv，逐条检查：
  1) 该数字是否确实出现在文稿中；
  2) 由数据源（CSV 或 JSON）按给定换算复算、按文稿精度四舍五入后，是否与文稿数字一致。

claims.csv 列：
  claim_id     自定义编号
  doc          文稿路径（相对项目根目录，.tex / .md）
  text_value   文稿中出现的数字字符串（如 0.352）
  source       数据源路径（.csv 或 .json）
  locator      CSV：row=<行号或列值条件>;col=<列名>，如 row=0;col=pi_annualised_pp 或 row=period:0;col=y_pct
               JSON：点分路径，如 steady_state.r
  factor       换算系数（默认 1），如 100 表示转为百分数
  abs          1 表示取绝对值后比较（文稿写“下降 0.352”时用）
  note         说明

用法（项目根目录）：
    python scripts/check_claims.py claims.csv
    python scripts/check_claims.py claims.csv --report-dir quality_reports

退出码：0 全部通过；2 有不一致；3 文件或格式错误
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


def read_source(path: Path, locator: str) -> float:
    if path.suffix.lower() == ".json":
        node = json.loads(path.read_text(encoding="utf-8"))
        for key in locator.split("."):
            node = node[int(key)] if isinstance(node, list) else node[key]
        return float(node)
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    parts = dict(p.split("=", 1) for p in locator.split(";"))
    r = parts["row"]
    if ":" in r:
        col, val = r.split(":", 1)
        hits = [x for x in rows if x[col].strip() == val]
        if len(hits) != 1:
            raise KeyError(f"行条件 {r} 匹配到 {len(hits)} 行")
        row = hits[0]
    else:
        row = rows[int(r)]
    return float(row[parts["col"]])


def round_like(x: float, text_value: str) -> Decimal:
    decimals = len(text_value.split(".")[1]) if "." in text_value else 0
    q = Decimal(1).scaleb(-decimals)
    return Decimal(repr(x)).quantize(q, rounding=ROUND_HALF_UP)


def main() -> int:
    ap = argparse.ArgumentParser(description="文稿数字与数据源逐条核对")
    ap.add_argument("claims", type=Path)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--report-dir", type=Path, default=Path("quality_reports"))
    ap.add_argument("--model", default=None)
    args = ap.parse_args()

    if not args.claims.exists():
        print(f"[ERR] 找不到 {args.claims}", file=sys.stderr)
        return 3
    claims = list(csv.DictReader(open(args.claims, encoding="utf-8-sig")))
    results = []
    for c in claims:
        doc = args.root / c["doc"]
        tv = c["text_value"].strip()
        status, recomputed, msg = "PASS", "", ""
        try:
            appears = tv in doc.read_text(encoding="utf-8")
            x = read_source(args.root / c["source"], c["locator"]) * float(c.get("factor") or 1)
            if (c.get("abs") or "0").strip() == "1":
                x = abs(x)
            recomputed = str(round_like(x, tv))
            if not appears:
                status, msg = "FAIL", "文稿中未找到该数字"
            elif Decimal(recomputed) != Decimal(tv):
                status, msg = "FAIL", f"数据源复算为 {x:.6g}，按文稿精度应为 {recomputed}"
        except Exception as e:                      # 定位或读取失败也记为不通过
            status, msg = "ERROR", f"{type(e).__name__}: {e}"
        results.append({**c, "status": status, "recomputed": recomputed, "message": msg})

    n_bad = sum(r["status"] != "PASS" for r in results)
    model = args.model or args.claims.parent.resolve().name
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    args.report_dir.mkdir(parents=True, exist_ok=True)
    rep = args.report_dir / f"{model}_claims_{ts}.md"
    lines = [f"# 文稿数字核对报告 · {model} · {ts}", "",
             f"- claims 文件：`{args.claims}`",
             f"- 核对条数：{len(results)}；不一致：{n_bad}",
             f"- 结论：{'✅ 全部一致' if n_bad == 0 else '❌ 存在不一致，禁止对外发布（numerical-validation-protocol Gate 3）'}",
             "", "| 编号 | 文稿 | 文稿数字 | 复算 | 结果 | 说明 |", "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['claim_id']} | `{r['doc']}` | {r['text_value']} | {r['recomputed']} | "
                     f"{'✅' if r['status'] == 'PASS' else '❌'} {r['status']} | {r['message'] or r.get('note', '')} |")
    rep.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for r in results:
        print(f"[{r['status']:5}] {r['claim_id']:10} 文稿 {r['text_value']:>10}  复算 {r['recomputed']:>10}  {r['message']}")
    print(f"[check_claims] 报告：{rep}")
    return 0 if n_bad == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
