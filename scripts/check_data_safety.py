#!/usr/bin/env python3
"""
check_data_safety.py —— 提交前数据安全扫描

按 data-protection 规则：
- 禁止提交 data/raw/、data/derived/ 中的任何数据文件（除 .gitkeep）
- 禁止提交常见密钥文件（.env, credentials.json, *.key, *.pem）
- 警告：体积大于 10 MB 的二进制（应进 LFS 或 .gitignore）

用法：
    python scripts/check_data_safety.py --staged $(git diff --cached --name-only)
    python scripts/check_data_safety.py --files file1 file2 ...
    python scripts/check_data_safety.py --all   # 扫描整个 staging area

退出码：
    0  全部通过
    1  使用错误
    2  发现违规
"""

from __future__ import annotations
import argparse
import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN_DIRS = (
    "data/raw/",
    "data/derived/",
)
FORBIDDEN_NAMES = re.compile(
    r"(?:^|/)(?:\.env(?:\..+)?|credentials\.json|secrets\.json|"
    r".*\.pem|.*\.key|id_rsa(?:\.pub)?|service-account.*\.json)$",
    re.IGNORECASE,
)
LARGE_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


def staged_files() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True
    )
    if out.returncode != 0:
        print(f"[ERR] git diff failed: {out.stderr}", file=sys.stderr)
        sys.exit(1)
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def main() -> int:
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--staged", nargs="*", help="explicit staged file list")
    g.add_argument("--files", nargs="*", help="files to check directly")
    g.add_argument("--all", action="store_true", help="auto: git diff --cached")
    args = p.parse_args()

    if args.all or args.staged is not None:
        files = list(args.staged or []) or staged_files()
    else:
        files = args.files or []

    if not files:
        print("[check_data_safety] 没有要检查的文件")
        return 0

    violations: list[str] = []
    warnings: list[str] = []

    for f in files:
        # 受保护目录
        if any(f.startswith(d) for d in FORBIDDEN_DIRS):
            if not f.endswith(".gitkeep") and not f.endswith("manifest.json"):
                violations.append(f"❌ 禁止提交受保护目录中的文件：{f}")
                continue
        # 密钥文件名模式
        if FORBIDDEN_NAMES.search(f):
            violations.append(f"❌ 疑似密钥/凭据文件：{f}")
            continue
        # 体积警告
        path = Path(f)
        if path.exists():
            sz = path.stat().st_size
            if sz > LARGE_FILE_BYTES:
                warnings.append(f"⚠️ 文件 > 10 MB：{f} ({sz/1e6:.1f} MB)；考虑 LFS 或 .gitignore")

    print("[check_data_safety] 扫描完成")
    for w in warnings:
        print(f"  {w}")
    if violations:
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        print(f"\n[check_data_safety] 共 {len(violations)} 项违规。提交被拒绝。",
              file=sys.stderr)
        return 2

    print(f"[check_data_safety] 通过（{len(files)} 个文件，{len(warnings)} 项警告）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
