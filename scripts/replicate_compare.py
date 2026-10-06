#!/usr/bin/env python3
"""
replicate_compare.py —— 一键复现核对（strucmod v0.3 新增，verifier 子 agent 的自动化部分）

把项目复制到临时目录，在副本中重跑指定命令，再把副本产物与原产物逐个数值比对。
原项目不被修改。容差遵循 replication-protocol（默认 IRF/仿真 1e-6）。

用法（项目根目录）：
    python scripts/replicate_compare.py \
        --cmd "python code/nk_three_eq/nk_solve.py" \
        --cmd "python code/nk_three_eq/nk_simulate.py" \
        --compare results/tables/nk_irf_eps_m.csv \
        --compare results/checkpoints/nk_policy.json \
        --tol 1e-6

比较规则：
    CSV   逐单元格，数值单元格比较绝对差，非数值单元格要求相同
    JSON  递归比较所有数值叶子；键名含 timestamp / time / path / log / env / validated_at 的字段跳过

退出码：0 全部一致；2 存在超容差差异；3 命令失败或文件缺失
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SKIP_KEYS = ("timestamp", "time", "path", "log", "env", "validated_at")


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def compare_csv(a: Path, b: Path):
    ra = list(csv.reader(open(a, encoding="utf-8-sig")))
    rb = list(csv.reader(open(b, encoding="utf-8-sig")))
    if len(ra) != len(rb):
        return float("inf"), f"行数不同 {len(ra)} vs {len(rb)}"
    worst = 0.0
    for i, (x, y) in enumerate(zip(ra, rb)):
        if len(x) != len(y):
            return float("inf"), f"第 {i} 行列数不同"
        for u, v in zip(x, y):
            nu, nv = _num(u), _num(v)
            if nu is None or nv is None:
                if u != v:
                    return float("inf"), f"第 {i} 行非数值单元格不同：{u!r} vs {v!r}"
            else:
                worst = max(worst, abs(nu - nv))
    return worst, ""


def _walk(x, y, path, out):
    if isinstance(x, dict) and isinstance(y, dict):
        for k in x:
            if any(s in k.lower() for s in SKIP_KEYS):
                continue
            if k not in y:
                out.append((float("inf"), f"{path}.{k} 在复现结果中缺失"))
                continue
            _walk(x[k], y[k], f"{path}.{k}", out)
    elif isinstance(x, list) and isinstance(y, list):
        if len(x) != len(y):
            out.append((float("inf"), f"{path} 长度不同"))
            return
        for i, (u, v) in enumerate(zip(x, y)):
            _walk(u, v, f"{path}[{i}]", out)
    elif isinstance(x, bool) or isinstance(y, bool):
        if x != y:
            out.append((float("inf"), f"{path} 布尔值不同：{x} vs {y}"))
    elif _num(x) is not None and _num(y) is not None and not isinstance(x, str):
        out.append((abs(float(x) - float(y)), path))


def compare_json(a: Path, b: Path):
    diffs = []
    _walk(json.loads(a.read_text(encoding="utf-8")), json.loads(b.read_text(encoding="utf-8")), "$", diffs)
    if not diffs:
        return 0.0, ""
    worst = max(diffs, key=lambda d: d[0])
    return worst[0], (worst[1] if worst[0] > 0 else "")


def main() -> int:
    ap = argparse.ArgumentParser(description="复制项目、重跑、逐项比对")
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--cmd", action="append", required=True, help="在副本根目录执行的命令，可多次")
    ap.add_argument("--compare", action="append", required=True, help="需比对的产物（相对路径），可多次")
    ap.add_argument("--tol", type=float, default=1e-6)
    ap.add_argument("--model", default=None)
    ap.add_argument("--report-dir", type=Path, default=Path("quality_reports"))
    args = ap.parse_args()

    root = args.root.resolve()
    model = args.model or root.name
    ignore = shutil.ignore_patterns(".git", "__pycache__", "*.pdf", "_superseded*", "quality_reports")
    rows, rc = [], 0
    with tempfile.TemporaryDirectory(prefix="strucmod_replicate_") as tmp:
        work = Path(tmp) / "proj"
        shutil.copytree(root, work, ignore=ignore)
        for c in args.compare:                      # 删除副本中的旧产物，确保是重新生成的
            (work / c).unlink(missing_ok=True)
        for cmd in args.cmd:
            p = subprocess.run(cmd, shell=True, cwd=work, capture_output=True, text=True, encoding="utf-8",
                               errors="replace")
            rows.append(("cmd", cmd, p.returncode))
            if p.returncode not in (0,):
                print(p.stdout[-2000:], p.stderr[-2000:], sep="\n")
                print(f"[replicate] 命令失败（退出码 {p.returncode}）：{cmd}", file=sys.stderr)
                rc = 3
        results = []
        for c in args.compare:
            a, b = root / c, work / c
            if not a.exists() or not b.exists():
                results.append((c, float("inf"), "原产物或复现产物缺失"))
                continue
            worst, msg = (compare_json if a.suffix.lower() == ".json" else compare_csv)(a, b)
            results.append((c, worst, msg))

    ok = rc == 0 and all(w <= args.tol for _, w, _ in results)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    args.report_dir.mkdir(parents=True, exist_ok=True)
    rep = args.report_dir / f"{model}_replicate_{ts}.md"
    lines = [f"# 复现核对报告 · {model} · {ts}", "",
             "- 方法：复制项目到临时目录，删除待比对产物后重跑命令，与原产物逐项比较",
             f"- 容差：{args.tol:.0e}（replication-protocol）",
             f"- 结论：{'✅ 复现一致' if ok else '❌ 复现不一致或命令失败'}", "", "## 命令", ""]
    lines += [f"- `{c}` → 退出码 {r}" for _, c, r in rows]
    lines += ["", "## 产物比对", "", "| 产物 | 最大绝对差 | 结果 | 说明 |", "|---|---|---|---|"]
    lines += [f"| `{c}` | {w:.3e} | {'✅' if w <= args.tol else '❌'} | {m} |" for c, w, m in results]
    rep.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for c, w, m in results:
        print(f"[{'PASS' if w <= args.tol else 'FAIL'}] {c}  max|diff| = {w:.3e}  {m}")
    print(f"[replicate] 报告：{rep}")
    return 0 if ok else (rc or 2)


if __name__ == "__main__":
    sys.exit(main())
