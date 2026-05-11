#!/usr/bin/env python3
"""
check_steady_state.py —— 数值化稳态校验

用法：
    python scripts/check_steady_state.py output/checkpoints/<model>_ss.json
    python scripts/check_steady_state.py output/checkpoints/<model>_ss.json --tol 1e-8

读取 checkpoint JSON（含稳态向量与方程残差），验证残差是否在容差以内。

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
from pathlib import Path
from datetime import datetime


def main() -> int:
    p = argparse.ArgumentParser(description="稳态残差校验")
    p.add_argument("checkpoint", type=Path, help="output/checkpoints/<model>_ss.json")
    p.add_argument("--tol", type=float, default=1e-8, help="残差容差（默认 1e-8）")
    p.add_argument("--report-dir", type=Path, default=Path("quality_reports"),
                   help="残差报告输出目录")
    args = p.parse_args()

    if not args.checkpoint.exists():
        print(f"[ERR] 找不到 checkpoint：{args.checkpoint}", file=sys.stderr)
        return 3

    try:
        data = json.loads(args.checkpoint.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[ERR] checkpoint 不是合法 JSON：{e}", file=sys.stderr)
        return 3

    # 必要字段
    required = ["model", "steady_state"]
    missing = [k for k in required if k not in data]
    if missing:
        print(f"[ERR] checkpoint 缺字段：{missing}", file=sys.stderr)
        return 3

    model = data["model"]
    residuals = data.get("residuals", {})

    if not residuals:
        print(f"[WARN] checkpoint 中无 residuals 字段。"
              f" 通常应由求解器后处理写入：每个方程名 → 残差绝对值。",
              file=sys.stderr)
        return 3

    # 排序残差
    items = sorted(residuals.items(), key=lambda kv: -abs(float(kv[1])))
    max_eq, max_r = items[0]
    max_r = abs(float(max_r))

    n_total = len(items)
    n_fail = sum(1 for _, r in items if abs(float(r)) >= args.tol)

    # 写报告
    args.report_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = args.report_dir / f"{model}_ss_{ts}.md"

    lines = [
        f"# 稳态残差报告 · {model} · {ts}",
        "",
        f"- checkpoint：`{args.checkpoint}`",
        f"- 总方程数：{n_total}",
        f"- 容差：{args.tol:.0e}",
        f"- 最大残差：{max_r:.3e}（方程 `{max_eq}`）",
        f"- 通过：{'✅ YES' if n_fail == 0 else '❌ NO'}",
        "",
        "## 残差最大的前 10 条",
        "",
        "| 方程 | 残差 |",
        "|---|---|",
    ]
    for eq, r in items[:10]:
        lines.append(f"| `{eq}` | {abs(float(r)):.3e} |")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[check_steady_state] 报告写入：{report_path}")

    if n_fail == 0:
        # 在 checkpoint 中标记 validated
        data["validated"] = True
        data["validated_at"] = datetime.utcnow().isoformat() + "Z"
        data["validated_tol"] = args.tol
        args.checkpoint.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[check_steady_state] 通过（max residual = {max_r:.3e}）")
        return 0
    else:
        print(f"[check_steady_state] 失败：{n_fail} 个方程残差 >= {args.tol:.0e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
