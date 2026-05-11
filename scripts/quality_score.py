#!/usr/bin/env python3
"""
quality_score.py —— 给一个建模产物（.mod / .jl / .m / .gms / .qmd）打分

评分维度（每项 0-2）：
  - 顶部声明：是否有版本 / 模型名 / spec 引用
  - 路径风格：是否相对路径
  - 日志开闭：是否有 log open/close 或等价
  - 检查点保存：是否有 save_checkpoint 或等价
  - 中文注释：注释是否包含中文（≥3 处）
  - 受保护文件：是否避免直接 import data/raw

满分 12。

用法：
    python scripts/quality_score.py model/03_solve/rbc/rbc.mod
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path


def score_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    head = "\n".join(lines[:40])

    s = {}

    # 1. 顶部声明
    s["header_decl"] = 0
    if re.search(
        r"version|using Pkg|MATLAB R20|GAMS|@#define\s+MODEL|Python\s+3\.|Julia\s+1\.|版本",
        head, re.I):
        s["header_decl"] += 1
    if re.search(r"spec\.md|model/01_setup", head):
        s["header_decl"] += 1

    # 2. 相对路径
    s["relative_paths"] = 2
    if re.search(r"[A-Z]:\\\\|/Users/|/home/", text):
        s["relative_paths"] = 0

    # 3. 日志开闭
    s["logging"] = 0
    if re.search(
        r"\blog\s+open\b|@info|tee\s+|logging\.basicConfig|logging\.FileHandler|getLogger",
        text):
        s["logging"] += 1
    if re.search(
        r"\blog\s+close\b|finally|logger\.info|log\.info|writelog",
        text):
        s["logging"] += 1

    # 4. 检查点
    s["checkpoint"] = 0
    if re.search(r"save_checkpoint|execute_unload|JSON3\.write|json\.dump", text):
        s["checkpoint"] += 1
    if re.search(r"output/checkpoints/", text):
        s["checkpoint"] += 1

    # 5. 中文注释
    chinese = re.findall(r"[一-鿿]", text)
    s["chinese_comments"] = 2 if len(chinese) >= 30 else (1 if len(chinese) >= 5 else 0)

    # 6. 数据保护
    s["data_protection"] = 2
    if re.search(r"data/raw/[^\.]", text):
        s["data_protection"] = 0

    return s


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("path", type=Path)
    args = p.parse_args()

    if not args.path.exists():
        print(f"[ERR] 找不到文件：{args.path}", file=sys.stderr)
        return 1

    s = score_file(args.path)
    total = sum(s.values())

    print(f"# 质量评分 · {args.path}")
    print(f"")
    print(f"| 维度 | 得分 |")
    print(f"|---|---|")
    for k, v in s.items():
        print(f"| {k} | {v}/2 |")
    print(f"| **合计** | **{total}/12** |")

    return 0 if total >= 8 else 2


if __name__ == "__main__":
    sys.exit(main())
